import requests
from requests.auth import HTTPBasicAuth

def get_azure_repo_file(organization: str, project: str, repo: str, file_path: str, pat: str, branch: str = "main") -> str:
    """
    Retrieves the raw content of a file from an Azure DevOps repository.
    
    Args:
        organization (str): The name of the organization.
        project (str): The project name.
        repo (str): The repository name or ID.
        file_path (str): The absolute path to the file in the repository (e.g., "/README.md").
        pat (str): Personal Access Token for authentication.
        branch (str, optional): The Git branch name. Defaults to "main".
        
    Returns:
        str: The raw content of the file if successful, an empty string otherwise.
    """
    url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo}/items"
    params = {
        "path": file_path,
        "includeContent": "true",
        "versionDescriptor.version": branch,
        "api-version": "7.1"
    }
    
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth('', pat),
            params=params
        )
        
        if response.status_code == 200:
            return response.text
        elif response.status_code == 404:
            return ""
        else:
            print(f"Execution failed: API returned status code {response.status_code} for URL: {url}")
            return ""
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return ""

def push_azure_repo_file(file_text: str, organization: str, project: str, repo: str, file_path: str, pat: str, branch: str = "main", commit_message: str = None) -> bool:
    """
    Pushes (creates or updates) a file in an Azure DevOps Git repository.

    Args:
        file_text (str): The content to be written to the file.
        organization (str): The Azure DevOps organization name.
        project (str): The name of the project.
        repo (str): The name or ID of the repository.
        file_path (str): The absolute path (starting with /) in the repo.
        pat (str): Personal Access Token with Code (Read & Write) permissions.
        branch (str, optional): The target branch. Defaults to "main".
        commit_message (str, optional): Custom commit message. Defaults to "Auto-push file: {file_path}".

    Returns:
        bool: True if the push was successful, False otherwise.
    """
    import base64
    
    # 1. Resolve branch ref (T008)
    if not branch.startswith("refs/"):
        branch_ref = f"refs/heads/{branch}"
    else:
        branch_ref = branch
        
    auth = HTTPBasicAuth('', pat)
    
    try:
        # 2. Check file existence to determine changeType (T010)
        item_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo}/items"
        item_params = {
            "path": file_path,
            "versionDescriptor.version": branch,
            "api-version": "7.1"
        }
        item_response = requests.get(item_url, auth=auth, params=item_params)
        
        # If 200, file exists (edit), if 404, file doesn't exist (add)
        if item_response.status_code == 200:
            change_type = "edit"
        else:
            change_type = "add"

        # 3. Get latest commit ID (T009, US3 T019)
        ref_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo}/refs"
        ref_params = {
            "filter": branch_ref.replace("refs/", ""),
            "api-version": "7.1"
        }
        ref_response = requests.get(ref_url, auth=auth, params=ref_params)
        
        old_object_id = "0000000000000000000000000000000000000000"
        base_commit_id = None
        
        if ref_response.status_code == 200:
            refs = ref_response.json().get('value', [])
            if refs:
                old_object_id = refs[0]['objectId']
            else:
                # Branch doesn't exist, handle US3 (T019)
                # Need baseCommitId from default branch (usually main)
                default_ref_params = {
                    "filter": "heads/main",
                    "api-version": "7.1"
                }
                default_ref_response = requests.get(ref_url, auth=auth, params=default_ref_params)
                if default_ref_response.status_code == 200:
                    default_refs = default_ref_response.json().get('value', [])
                    if default_refs:
                        base_commit_id = default_refs[0]['objectId']
                    else:
                        print(f"Execution failed: Could not find base commit for new branch {branch}")
                        return False
                else:
                    print(f"Execution failed: Could not fetch default branch ref. Status: {default_ref_response.status_code}")
                    return False
        else:
            print(f"Execution failed: Could not fetch branch ref. Status: {ref_response.status_code}")
            return False

        # 4. Perform Push (T011, US2 T015/T016, US3 T018/T019)
        push_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo}/pushes?api-version=7.1"
        
        # Determine commit message (US3 T018)
        if not commit_message:
            commit_message = f"Auto-push file: {file_path}"
        
        push_body = {
            "refUpdates": [
                {
                    "name": branch_ref,
                    "oldObjectId": old_object_id
                }
            ],
            "commits": [
                {
                    "comment": commit_message,
                    "changes": [
                        {
                            "changeType": change_type,
                            "item": {
                                "path": file_path
                            },
                            "newContent": {
                                "content": file_text,
                                "contentType": "rawtext"
                            }
                        }
                    ]
                }
            ]
        }
        
        if base_commit_id:
            push_body["commits"][0]["baseCommitId"] = base_commit_id
            
        push_response = requests.post(push_url, auth=auth, json=push_body)
        
        if push_response.status_code in [200, 201]:
            return True
        else:
            # T012: Add debug prints for API failures
            print(f"Execution failed: Push API returned status code {push_response.status_code}")
            print(f"Response: {push_response.text}")
            return False
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return False

def set_azure_repo_capacity(organization: str, project: str, repo: str, pat: str) -> bool:
    """
    Sets a repository size limit (5MB) for an Azure DevOps Git repository using a policy configuration.

    Args:
        organization (str): The Azure DevOps organization name.
        project (str): The name or ID of the project.
        repo (str): The name or ID of the repository.
        pat (str): Personal Access Token for authentication.

    Returns:
        bool: True if the policy was successfully applied or confirmed, False otherwise.
    """
    auth = HTTPBasicAuth('', pat)
    
    try:
        # 1. Get repository ID
        repo_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo}?api-version=7.1"
        repo_response = requests.get(repo_url, auth=auth)
        
        if repo_response.status_code != 200:
            print(f"Execution failed: Could not find repository {repo}. Status: {repo_response.status_code}")
            return False
            
        repo_data = repo_response.json()
        repo_id = repo_data.get('id')
        if not repo_id:
            print(f"Execution failed: Repository ID not found for {repo}")
            return False

        # 2. Create Policy Configuration
        # Policy Type ID for "Maximum repository size": 2e26e725-8201-4edd-8bf5-978563c34a80
        policy_url = f"https://dev.azure.com/{organization}/{project}/_apis/policy/configurations?api-version=7.1"
        
        policy_body = {
            "MaximumGitBlobSizeInBytes": 5242880,
            "isEnabled": True,
            "isBlocking": True,
            "type": {
                "id": "2e26e725-8201-4edd-8bf5-978563c34a80"
            },
            "settings": {
                "maximumRepositorySize": 5242880,  # 5MB in bytes (5 * 1024 * 1024)
                "scope": [
                    {
                        "repositoryId": repo_id
                    }
                ]
            }
        }
        
        policy_response = requests.post(policy_url, auth=auth, json=policy_body)
        
        if policy_response.status_code in [200, 201]:
            return True
        else:
            print(f"Execution failed: Policy API returned status code {policy_response.status_code}")
            print(f"Response: {policy_response.text}")
            return False
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return False
