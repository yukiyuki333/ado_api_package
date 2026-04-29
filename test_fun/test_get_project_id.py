import pytest
from unittest.mock import patch, MagicMock
from ado_api.project import get_project_id

@patch('requests.get')
def test_get_project_id_success(mock_get):
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "test-project-uuid",
        "name": "test-project"
    }
    mock_get.return_value = mock_response

    org = "test-org"
    project = "test-project"
    pat = "test-pat"

    result = get_project_id(org, project, pat)

    from unittest.mock import ANY
    assert result == "test-project-uuid"
    mock_get.assert_called_once_with(
        f"https://dev.azure.com/{org}/_apis/projects/{project}?api-version=7.1",
        auth=ANY
    )

@patch('requests.get')
def test_get_project_id_not_found(mock_get):
    # Mock 404 response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    org = "test-org"
    project = "non-existent"
    pat = "test-pat"

    result = get_project_id(org, project, pat)

    assert result is None

@patch('requests.get')
def test_get_project_id_exception(mock_get):
    # Mock exception
    mock_get.side_effect = Exception("Connection error")

    org = "test-org"
    project = "test-project"
    pat = "test-pat"

    result = get_project_id(org, project, pat)

    assert result is None
