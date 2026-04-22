import unittest
from unittest.mock import patch, MagicMock
from ado_api_package.ado_api.pipeline import run_azure_pipeline

class TestRunAzurePipeline(unittest.TestCase):

    @patch('ado_api.pipeline.requests.get')
    @patch('ado_api.pipeline.requests.post')
    def test_run_azure_pipeline_success(self, mock_post, mock_get):
        # 1. Mock pipeline listing success
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'value': [{'name': 'CI-Build', 'id': 123}]
        }
        mock_get.return_value = mock_get_response

        # 2. Mock pipeline trigger success
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {'id': 'run-1', 'status': 'inProgress'}
        mock_post.return_value = mock_post_response

        result = run_azure_pipeline("my-org", "my-project", "CI-Build", "my-pat", branch="develop")
        
        self.assertEqual(result.get('id'), 'run-1')
        mock_get.assert_called_once()
        mock_post.assert_called_once()
        
        # Verify POST payload branch
        args, kwargs = mock_post.call_args
        payload = kwargs.get('json', {})
        self.assertEqual(payload['resources']['repositories']['self']['refName'], 'refs/heads/develop')

    @patch('ado_api.pipeline.requests.get')
    def test_run_azure_pipeline_not_found(self, mock_get):
        # Mock empty pipeline list
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'value': []}
        mock_get.return_value = mock_get_response

        result = run_azure_pipeline("my-org", "my-project", "NonExistent", "my-pat")
        
        self.assertEqual(result, {})

    @patch('ado_api.pipeline.requests.get')
    @patch('ado_api.pipeline.requests.post')
    def test_run_azure_pipeline_trigger_fail(self, mock_post, mock_get):
        # Mock listing success
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'value': [{'name': 'CI', 'id': 456}]}
        mock_get.return_value = mock_get_response

        # Mock trigger failure
        mock_post_response = MagicMock()
        mock_post_response.status_code = 400
        mock_post_response.text = "Bad Request"
        mock_post.return_value = mock_post_response

        result = run_azure_pipeline("my-org", "my-project", "CI", "my-pat")
        
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
