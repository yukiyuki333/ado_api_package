import requests
from requests.auth import HTTPBasicAuth

from typing import Optional

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

def create_project(org_name: str, pat: str, project_name: str, description: str = "") -> Optional[dict]:
    """
    Creates a new private Azure DevOps project with Git source control.
    
    Args:
        org_name (str): The name of the Azure DevOps organization.
        pat (str): Personal Access Token for authentication.
        project_name (str): The name of the project to create.
        description (str): Optional description for the project.
        
    Returns:
        dict: The OperationReference object if successful (202 Accepted), None otherwise.
    """
    url = f"https://dev.azure.com/{org_name}/_apis/projects?api-version=7.1"
    
    payload = {
        "name": project_name,
        "description": description,
        "visibility": "private",
        "capabilities": {
            "versioncontrol": {
                "sourceControlType": "Git"
            },
            "processTemplate": {
                "templateTypeId": "adcc42ab-9882-485e-a3ed-7678f01f66bc"
            }
        }
    }
    
    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth('', pat),
            json=payload
        )
        
        if response.status_code in [200, 202]:
            return response.json()
        else:
            print(f"Execution failed: API returned status code {response.status_code} for URL: {url}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        # Mandatory try-except and debug output per Constitutional Principle II
        print(f"Execution failed: {str(e)}")
        return None

def get_project_id(organization: str, project_name: str, pat: str) -> Optional[str]:
    """
    Retrieves the unique identifier (UUID) for an Azure DevOps project.
    
    Args:
        organization (str): The name of the Azure DevOps organization.
        project_name (str): The name of the project.
        pat (str): Personal Access Token for authentication.
        
    Returns:
        Optional[str]: The project ID (UUID) if found, None otherwise.
    """
    url = f"https://dev.azure.com/{organization}/_apis/projects/{project_name}?api-version=7.1"
    
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth('', pat)
        )
        
        if response.status_code == 200:
            project_data = response.json()
            return project_data.get('id')
        elif response.status_code == 404:
            print(f"Project '{project_name}' not found in organization '{organization}'.")
            return None
        else:
            print(f"Execution failed: API returned status code {response.status_code} for URL: {url}")
            return None
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return None
