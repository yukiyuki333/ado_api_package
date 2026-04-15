import requests
from utils.auth import get_auth, validate_env, _resolve_identity

def check_project_exists(project_identifier: str) -> bool:
    """
    Checks if an Azure DevOps project exists using the REST API v7.1.
    
    Args:
        project_identifier (str): The project's name or its UUID.
    
    Returns:
        bool: True if the project exists, False if not found (404).
    
    Raises:
        RuntimeError: If the API returns any other error code (401, 500, etc.).
    """
    org_url, _ = validate_env()
    auth = get_auth()
    
    # Ensure org_url doesn't have a trailing slash for consistency
    org_url = org_url.rstrip("/")
    url = f"{org_url}/_apis/projects/{project_identifier}?api-version=7.1"
    
    response = requests.get(url, auth=auth)
    
    if response.status_code == 200:
        return True
    
    if response.status_code == 404:
        return False
        
    # Handle other errors per Constitution
    print(f"Error: API returned status code {response.status_code}")
    print(f"Raw API Feedback: {response.text}")
    
    if response.status_code == 401:
        print("Suggested Solution: Please check if your AZDO_PAT is correct and has the necessary permissions.")
    elif response.status_code == 403:
        print("Suggested Solution: You do not have permission to access this project.")
    else:
        print("Suggested Solution: Please verify your AZDO_ORG_URL and project identifier.")
        
    raise RuntimeError(f"API Error {response.status_code}")

class Project:
    """
    Class for handling project-related operations in Azure DevOps.
    """
    def __init__(self, project_identifier: str):
        self.project_identifier = project_identifier
        self.org_url, self.pat = validate_env()
        self.auth = get_auth()
        self.organization = self.org_url.rstrip("/").split("/")[-1]
        self.vssps_base_url = f"https://vssps.dev.azure.com/{self.organization}/_apis"
        self._group_cache = {}

    def _handle_api_error(self, response):
        """
        Standardized error handling for API responses.
        """
        if response.status_code >= 400:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Raw API Feedback: {response.text}")
            raise RuntimeError(f"API Error {response.status_code}: {response.text}")

    def get_project_groups(self) -> dict:
        """
        Retrieves security groups for the specified project.
        
        Returns:
            dict: Mapping of group display names to descriptors.
        """
        if self._group_cache:
            return self._group_cache

        # Note: In a real implementation, we might need the scope ID (Project ID)
        # to filter groups effectively. For now, we list organization groups and filter.
        # Ideally, use /_apis/graph/groups with scopeDescriptor.
        
        url = f"{self.vssps_base_url}/graph/groups?api-version=7.1-preview.1"
        response = requests.get(url, auth=self.auth)
        self._handle_api_error(response)
        
        groups = response.json().get("value", [])
        
        # Filter for Project Administrators and Contributors
        # This is a simplified filter. In practice, groups are usually prefixed
        # with [ProjectName]\...
        target_groups = ["Project Administrators", "Contributors"]
        result = {}
        
        for group in groups:
            display_name = group.get("displayName", "")
            # Match common AzDo project group patterns
            if any(target in display_name for target in target_groups):
                # Map to generic names for easier use
                if "Project Administrators" in display_name:
                    result["Project Administrators"] = group["descriptor"]
                elif "Contributors" in display_name:
                    result["Contributors"] = group["descriptor"]
        
        self._group_cache = result
        return result

    def add_member_to_group(self, group_descriptor: str, user_email: str):
        """
        Adds a user to a security group.
        
        Args:
            group_descriptor: The target group's descriptor.
            user_email: The email of the user to add.
        """
        user_descriptor = _resolve_identity(user_email)
        
        # membership endpoint: PUT https://vssps.dev.azure.com/{organization}/_apis/graph/memberships/{subjectDescriptor}/{containerDescriptor}?api-version=7.1-preview.1
        url = f"{self.vssps_base_url}/graph/memberships/{user_descriptor}/{group_descriptor}?api-version=7.1-preview.1"
        
        response = requests.put(url, auth=self.auth)
        self._handle_api_error(response)

    def remove_member_from_group(self, group_descriptor: str, user_email: str):
        """
        Removes a user from a security group.
        
        Args:
            group_descriptor: The target group's descriptor.
            user_email: The email of the user to remove.
        """
        user_descriptor = _resolve_identity(user_email)
        
        # membership endpoint: DELETE https://vssps.dev.azure.com/{organization}/_apis/graph/memberships/{subjectDescriptor}/{containerDescriptor}?api-version=7.1-preview.1
        url = f"{self.vssps_base_url}/graph/memberships/{user_descriptor}/{group_descriptor}?api-version=7.1-preview.1"
        
        response = requests.delete(url, auth=self.auth)
        self._handle_api_error(response)
