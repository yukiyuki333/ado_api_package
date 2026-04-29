import pytest
from unittest.mock import patch, MagicMock
from ado_api.project import create_project

@patch('requests.post')
def test_create_project_success(mock_post):
    # Mock successful response (202 Accepted)
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.json.return_value = {
        "id": "operation-id",
        "status": "queued",
        "url": "https://dev.azure.com/org/_apis/operations/operation-id"
    }
    mock_post.return_value = mock_response

    org_name = "test-org"
    pat = "test-pat"
    project_name = "test-project"
    description = "Test project description"

    result = create_project(org_name, pat, project_name, description)

    assert result is not None
    assert result["id"] == "operation-id"
    assert result["status"] == "queued"
    
    # Verify the API call
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == f"https://dev.azure.com/{org_name}/_apis/projects?api-version=7.1"
    
    payload = kwargs['json']
    assert payload['name'] == project_name
    assert payload['description'] == description
    assert payload['visibility'] == "private"
    assert payload['capabilities']['versioncontrol']['sourceControlType'] == "Git"
    assert payload['capabilities']['processTemplate']['templateTypeId'] == "adcc42ab-9882-485e-a3ed-7678f01f66bc"

@patch('requests.post')
def test_create_project_failure(mock_post):
    # Mock failure response (401 Unauthorized)
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_post.return_value = mock_response

    org_name = "test-org"
    pat = "invalid-pat"
    project_name = "test-project"

    result = create_project(org_name, pat, project_name)

    assert result is None
