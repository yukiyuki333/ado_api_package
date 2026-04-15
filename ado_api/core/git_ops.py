import requests
from utils.auth import get_auth, validate_env

def get_git_file_content(project: str, repo: str, file_path: str, branch: str = "master") -> str:
    """
    Retrieves the raw content of a file from an Azure DevOps repository.
    """
    org_url, _ = validate_env()
    auth = get_auth()
    
    org_url = org_url.rstrip("/")
    # Using items API with includeContent=True and scopePath
    # API: GET https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repositoryId}/items?path={path}&includeContent=True&api-version=7.1
    url = f"{org_url}/{project}/_apis/git/repositories/{repo}/items"
    params = {
        "path": file_path,
        "includeContent": "True",
        "versionDescriptor.version": branch,
        "api-version": "7.1"
    }
    
    response = requests.get(url, auth=auth, params=params)
    
    if response.status_code == 200:
        return response.text
    
    # Handle errors per Constitution
    print(f"Error: API returned status code {response.status_code}")
    print(f"Raw API Feedback: {response.text}")
    
    if response.status_code == 404:
        print(f"Suggested Solution: File '{file_path}' not found in repo '{repo}'. Check path and branch.")
    elif response.status_code == 401:
        print("Suggested Solution: Please check if your AZDO_PAT is correct.")
        
    raise RuntimeError(f"API Error {response.status_code}")

class GitOps:
    pass

def push_git_file_content(project: str, repo: str, file_path: str, content: str, branch: str = "master", commit_message: str = "Update file") -> dict:
    """
    Pushes new content to a file in an Azure DevOps repository.
    """
    pass
