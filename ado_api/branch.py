import requests
from requests.auth import HTTPBasicAuth

def create_branch(organization: str, project: str, repo: str, pat: str, new_branch_name: str, source_branch_name: str) -> bool:
    """
    Creates a new branch in an Azure DevOps Git repository starting from a source branch's current commit.

    Args:
        organization (str): The Azure DevOps organization name.
        project (str): The name or ID of the project.
        repo (str): The name or ID of the repository.
        pat (str): Personal Access Token for authentication.
        new_branch_name (str): The name of the branch to create (e.g., "feature/login").
        source_branch_name (str): The name of the source branch (e.g., "main").

    Returns:
        bool: True if the branch was successfully created, False otherwise.
    """
    # 1. Normalize branch names
    def normalize_ref(name):
        if not name.startswith("refs/heads/"):
            return f"refs/heads/{name}"
        return name

    full_new_branch = normalize_ref(new_branch_name)
    full_source_branch = normalize_ref(source_branch_name)
    
    auth = HTTPBasicAuth('', pat)
    
    try:
        # 2. Get Source Branch Commit ID
        # Endpoint: GET https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo}/refs?filter=heads/{source_branch_name}&api-version=7.1
        filter_name = full_source_branch.replace("refs/", "")
        ref_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo}/refs?api-version=7.1"
        ref_params = {
            "filter": filter_name,
            "api-version": "7.1"
        }
        
        ref_response = requests.get(ref_url, auth=auth, params=ref_params)
        
        if ref_response.status_code != 200:
            print(f"Execution failed: Could not fetch branch ref. Status: {ref_response.status_code}")
            return False
            
        refs = ref_response.json().get('value', [])
        if not refs:
            print(f"Execution failed: Source branch '{source_branch_name}' not found.")
            return False
            
        source_commit_id = refs[0].get('objectId')
        if not source_commit_id:
            print(f"Execution failed: Object ID not found for branch '{source_branch_name}'")
            return False

        # 3. Create the New Branch Ref
        # Endpoint: POST https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo}/refs?api-version=7.1
        update_body = [
            {
                "name": full_new_branch,
                "oldObjectId": "0000000000000000000000000000000000000000",
                "newObjectId": source_commit_id
            }
        ]
        
        update_response = requests.post(ref_url, auth=auth, json=update_body)
        
        if update_response.status_code in [200, 201]:
            # Success is indicated by the updateStatus within the response array
            results = update_response.json().get('value', [])
            if results and results[0].get('updateStatus') == 'succeeded':
                return True
            else:
                status = results[0].get('updateStatus') if results else "unknown"
                print(f"Execution failed: Branch creation failed with status '{status}'")
                return False
        else:
            print(f"Execution failed: Refs Update API returned status code {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return False

def set_git_branch_policy(organization: str, project: str, repo: str, branch: str, pat: str) -> bool:
    """
    Configures three specific branch policies (Work Item Linking, Comment Resolution, and Merge Strategy)
    for a target branch in Azure DevOps.

    Args:
        organization (str): The Azure DevOps organization name.
        project (str): The name or ID of the project.
        repo (str): The name or ID of the repository.
        branch (str): The branch name (e.g., "main") or ref (e.g., "refs/heads/main").
        pat (str): Personal Access Token for authentication.

    Returns:
        bool: True if all policies were successfully applied, False otherwise.
    """
    auth = HTTPBasicAuth('', pat)
    
    # 1. Normalize branch ref (T002)
    if not branch.startswith("refs/heads/"):
        branch_ref = f"refs/heads/{branch}"
    else:
        branch_ref = branch
        
    try:
        # 2. Get Repository GUID (T003)
        repo_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo}?api-version=7.1"
        repo_response = requests.get(repo_url, auth=auth)
        
        if repo_response.status_code != 200:
            print(f"Execution failed: Could not find repository {repo}. Status: {repo_response.status_code}")
            return False
            
        repo_id = repo_response.json().get('id')
        if not repo_id:
            print(f"Execution failed: Repository ID not found for {repo}")
            return False

        # 3. Get existing policies for idempotency (T009)
        # We need to find if any of the target policies already exist for this branch
        policy_list_url = f"https://dev.azure.com/{organization}/{project}/_apis/policy/configurations?api-version=7.1"
        list_response = requests.get(policy_list_url, auth=auth)
        
        existing_policies = []
        if list_response.status_code == 200:
            all_configs = list_response.json().get('value', [])
            # Filter for policies matching our repo and branch
            for config in all_configs:
                scope = config.get('settings', {}).get('scope', [])
                for s in scope:
                    if s.get('repositoryId') == repo_id and s.get('refName') == branch_ref:
                        existing_policies.append(config)
                        break

        # 4. Define target policy settings
        # US1: Work Item Linking (40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e)
        # US1: Comment Resolution (c6a1889d-b943-4856-b76f-9e46bb6b0df2)
        # US2: Merge Strategy (fa4e907d-c16b-4a4c-9dfa-4916e5d171ab)
        
        targets = [
            {
                "type_id": "40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e",
                "settings": {
                    "scope": [{"repositoryId": repo_id, "refName": branch_ref, "matchKind": "exact"}]
                }
            },
            {
                "type_id": "c6a1889d-b943-4856-b76f-9e46bb6b0df2",
                "settings": {
                    "scope": [{"repositoryId": repo_id, "refName": branch_ref, "matchKind": "exact"}]
                }
            },
            {
                "type_id": "fa4e907d-c16b-4a4c-9dfa-4916e5d171ab",
                "settings": {
                    "allowSquash": False,
                    "allowRebase": False,
                    "allowNoFastForward": True,
                    "allowRebaseMerge": False,
                    "scope": [{"repositoryId": repo_id, "refName": branch_ref, "matchKind": "exact"}]
                }
            }
        ]

        # 5. Apply policies (T004, T005, T007, T010)
        success_count = 0
        for target in targets:
            policy_type_id = target["type_id"]
            
            # Find existing config for this type
            existing_config = next((p for p in existing_policies if p.get('type', {}).get('id') == policy_type_id), None)
            
            payload = {
                "isEnabled": True,
                "isBlocking": True,
                "type": {"id": policy_type_id},
                "settings": target["settings"]
            }
            
            if existing_config:
                # Update (PUT)
                policy_id = existing_config['id']
                update_url = f"https://dev.azure.com/{organization}/{project}/_apis/policy/configurations/{policy_id}?api-version=7.1"
                resp = requests.put(update_url, auth=auth, json=payload)
            else:
                # Create (POST)
                create_url = f"https://dev.azure.com/{organization}/{project}/_apis/policy/configurations?api-version=7.1"
                resp = requests.post(create_url, auth=auth, json=payload)
            if resp.status_code in [200, 201]:
                success_count += 1
            else:
                print(f"Execution failed for policy type {policy_type_id}. Status: {resp.status_code}")
                print(f"Response: {resp.text}")

        return success_count == len(targets)

    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return False
