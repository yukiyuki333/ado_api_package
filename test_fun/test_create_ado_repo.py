import pytest
from unittest.mock import patch, MagicMock, ANY
from ado_api.repo import create_ado_repo

@patch('ado_api.repo.get_project_id')
@patch('requests.post')
def test_create_ado_repo_success(mock_post, mock_get_project_id):
    # Mock project ID retrieval
    mock_get_project_id.return_value = "project-uuid"

    # Mock successful repo creation
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": "new-repo-uuid",
        "name": "new-repo",
        "remoteUrl": "https://dev.azure.com/org/proj/_git/new-repo"
    }
    mock_post.return_value = mock_response

    org = "test-org"
    project = "test-project"
    repo = "new-repo"
    pat = "test-pat"

    result = create_ado_repo(org, project, repo, pat)

    assert result is not None
    assert result["id"] == "new-repo-uuid"
    assert result["name"] == "new-repo"
    
    mock_get_project_id.assert_called_once_with(org, project, pat)
    mock_post.assert_called_once_with(
        f"https://dev.azure.com/{org}/project-uuid/_apis/git/repositories?api-version=7.1",
        auth=ANY,
        json={"name": repo}
    )

@patch('ado_api.repo.get_project_id')
def test_create_ado_repo_project_not_found(mock_get_project_id):
    # Mock project ID retrieval failure
    mock_get_project_id.return_value = None

    org = "test-org"
    project = "non-existent"
    repo = "new-repo"
    pat = "test-pat"

    result = create_ado_repo(org, project, repo, pat)

    assert result is None

@patch('ado_api.repo.get_project_id')
@patch('requests.post')
def test_create_ado_repo_api_failure(mock_post, mock_get_project_id):
    # Mock project ID retrieval
    mock_get_project_id.return_value = "project-uuid"

    # Mock API failure
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_post.return_value = mock_response

    org = "test-org"
    project = "test-project"
    repo = "new-repo"
    pat = "test-pat"

    result = create_ado_repo(org, project, repo, pat)

    assert result is None

@patch('ado_api.repo.get_project_id')
@patch('requests.post')
def test_create_ado_repo_multi_repo(mock_post, mock_get_project_id):
    # T008: US2 Multi-repo support
    mock_get_project_id.return_value = "project-uuid"
    
    # First call success
    mock_response1 = MagicMock()
    mock_response1.status_code = 201
    mock_response1.json.return_value = {"id": "repo1-uuid", "name": "repo1"}
    
    # Second call success
    mock_response2 = MagicMock()
    mock_response2.status_code = 201
    mock_response2.json.return_value = {"id": "repo2-uuid", "name": "repo2"}
    
    mock_post.side_effect = [mock_response1, mock_response2]

    org = "test-org"
    project = "test-project"
    pat = "test-pat"

    res1 = create_ado_repo(org, project, "repo1", pat)
    res2 = create_ado_repo(org, project, "repo2", pat)

    assert res1["name"] == "repo1"
    assert res2["name"] == "repo2"
    assert mock_post.call_count == 2
