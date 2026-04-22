import requests
from requests.auth import HTTPBasicAuth

def get_group(organization: str, group_type: str, group_name: str, pat: str) -> str:
    """
    Finds a specific project group's descriptor based on its type and name.

    Args:
        organization (str): The Azure DevOps organization name.
        group_type (str): Type of the group. Only "ProjectManager" or "ProjectMember" are allowed.
        group_name (str): The display name of the group to search for (e.g., "[Project]\\Contributors").
        pat (str): Personal Access Token for authentication.

    Returns:
        str: The descriptor of the matching group, or an empty string if not found.
    """
    # 1. Validation
    valid_types = ["ProjectManager", "ProjectMember"]
    if group_type not in valid_types:
        print(f"Validation failed: Invalid group_type '{group_type}'. Must be one of {valid_types}")
        return ""

    auth = HTTPBasicAuth('', pat)
    
    try:
        # 2. Azure DevOps Graph API to list groups
        # Note: Graph API uses a different base URL than Core API.
        url = f"https://vssps.dev.azure.com/{organization}/_apis/graph/groups?api-version=7.1-preview.1"
        
        # 3. Simple loop to handle possible pagination (X-MS-ContinuationToken)
        continuation_token = None
        
        while True:
            params = {}
            if continuation_token:
                params['continuationToken'] = continuation_token
                
            response = requests.get(url, auth=auth, params=params)
            
            if response.status_code != 200:
                print(f"Execution failed: Graph API returned status code {response.status_code}")
                print(f"Response: {response.text}")
                return ""
            
            data = response.json()
            groups = data.get('value', [])
            
            # 4. Filter for matching group_name
            for group in groups:
                if group.get('displayName') == group_name:
                    return group.get('descriptor', "")
            
            # Check for continuation token
            continuation_token = response.headers.get('X-MS-ContinuationToken')
            if not continuation_token:
                break
                
        # 5. If not found after checking all pages
        print(f"Execution failed: Group '{group_name}' not found in organization.")
        return ""
        
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return ""

def update_group(organization: str, group_descriptor: str, user_email: str, add_user: bool, pat: str) -> bool:
    """
    Adds or removes a user to/from a group in Azure DevOps using the user's email and the group's descriptor.

    Args:
        organization (str): The Azure DevOps organization name.
        group_descriptor (str): The descriptor of the group (e.g., vssgp.123).
        user_email (str): The email address of the user.
        add_user (bool): True to add the user to the group, False to remove them.
        pat (str): Personal Access Token for authentication.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    auth = HTTPBasicAuth('', pat)
    
    try:
        # 1. Resolve User Email to Descriptor
        query_url = f"https://vssps.dev.azure.com/{organization}/_apis/graph/subjectquery?api-version=7.1-preview.1"
        query_payload = {
            "query": user_email,
            "subjectKind": ["User"]
        }
        
        query_response = requests.post(query_url, auth=auth, json=query_payload)
        
        if query_response.status_code != 200:
            print(f"Execution failed: User resolution failed for {user_email}. Status: {query_response.status_code}")
            return False
            
        users = query_response.json().get('value', [])
        if not users:
            print(f"Execution failed: User {user_email} not found.")
            return False
            
        user_descriptor = users[0].get('descriptor')
        if not user_descriptor:
            print(f"Execution failed: Descriptor not found for user {user_email}")
            return False

        # 2. Perform Membership Operation
        # https://vssps.dev.azure.com/{organization}/_apis/graph/memberships/{subjectDescriptor}/{containerDescriptor}?api-version=7.1-preview.1
        membership_url = f"https://vssps.dev.azure.com/{organization}/_apis/graph/memberships/{user_descriptor}/{group_descriptor}?api-version=7.1-preview.1"
        
        if add_user:
            # PUT to add member
            member_response = requests.put(membership_url, auth=auth)
            expected_status = [200, 201]
        else:
            # DELETE to remove member
            member_response = requests.delete(membership_url, auth=auth)
            expected_status = [204]
            
        if member_response.status_code in expected_status:
            return True
        else:
            print(f"Execution failed: Membership operation failed. Method: {'PUT' if add_user else 'DELETE'}. Status: {member_response.status_code}")
            print(f"Response: {member_response.text}")
            return False
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return False
