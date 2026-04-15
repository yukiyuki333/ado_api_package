import os
import sys
import requests
from requests.auth import HTTPBasicAuth

def validate_env():
    """
    Validates that necessary environment variables are set.
    If not, prints non-technical instructions and terminates the program.
    """
    org_url = os.getenv("AZDO_ORG_URL")
    pat = os.getenv("AZDO_PAT")
    
    missing = []
    if not org_url:
        missing.append("AZDO_ORG_URL")
    if not pat:
        missing.append("AZDO_PAT")
        
    if missing:
        print("Error: Missing mandatory environment variables.")
        if "AZDO_PAT" in missing:
            print("Please run the following command to set your Personal Access Token:")
            print('  export AZDO_PAT="your-token-here" (Linux/macOS)')
            print('  $env:AZDO_PAT="your-token-here" (PowerShell)')
        if "AZDO_ORG_URL" in missing:
            print("Please run the following command to set your Organization URL:")
            print('  export AZDO_ORG_URL="https://dev.azure.com/{organization}" (Linux/macOS)')
            print('  $env:AZDO_ORG_URL="https://dev.azure.com/{organization}" (PowerShell)')
        sys.exit(1)
        
    return org_url, pat

def get_auth():
    """
    Returns a Basic Authentication object for requests.
    Username is empty as per Azure DevOps PAT requirements.
    """
    _, pat = validate_env()
    return HTTPBasicAuth("", pat)

def _resolve_identity(email: str) -> str:
    """
    Resolves a user email to an Identity Descriptor using the VSSPS API.
    
    Args:
        email: The user's email address.
        
    Returns:
        The Identity Descriptor string.
        
    Raises:
        RuntimeError: If identity cannot be resolved or API error occurs.
    """
    org_url, _ = validate_env()
    # VSSPS API uses a different base URL
    organization = org_url.rstrip("/").split("/")[-1]
    vssps_url = f"https://vssps.dev.azure.com/{organization}/_apis/identities"
    
    params = {
        "searchFilter": "General",
        "filterValue": email,
        "queryMembership": "None",
        "api-version": "7.1-preview.1"
    }
    
    response = requests.get(vssps_url, auth=get_auth(), params=params)
    
    if response.status_code != 200:
        raise RuntimeError(f"Error resolving identity: {response.status_code} - {response.text}")
        
    data = response.json()
    if data.get("count", 0) == 0:
        raise RuntimeError(f"No identity found for email: {email}")
        
    # Return the first matching identity descriptor
    return data["value"][0]["descriptor"]
