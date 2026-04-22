import requests
from requests.auth import HTTPBasicAuth

def check_project_exists(organization: str, project_name: str, pat: str) -> bool:
    """
    Checks if an Azure DevOps project exists in a given organization.
    
    Args:
        organization (str): The name of the Azure DevOps organization.
        project_name (str): The name of the project to check for.
        pat (str): Personal Access Token for authentication.
        
    Returns:
        bool: True if project exists (200 OK), False otherwise (404 Not Found or other failures).
    """
    url = f"https://dev.azure.com/{organization}/_apis/projects/{project_name}?api-version=7.1"
    
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth('', pat)
        )
        
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            # Handle other status codes (401, 403, etc.) as failures with debug info
            print(f"Execution failed: API returned status code {response.status_code} for URL: {url}")
            return False
            
    except Exception as e:
        # Mandatory try-except and debug output per Constitutional Principle II
        print(f"Execution failed: {str(e)}")
        return False
