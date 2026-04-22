import os
import unittest
from unittest.mock import patch, MagicMock
from ado_api_package.ado_api.project import check_project_exists

class TestCheckProjectExists(unittest.TestCase):
    @patch('ado_api.project.requests.get')
    def test_project_exists_success(self):
        org_name = os.getenv("org_name")
        pat = os.getenv("pat")

        result = check_project_exists(org_name, "john19960801", pat)
        self.assertTrue(result)

    @patch('ado_api.project.requests.get')
    def test_project_not_found(self):
        org_name = os.getenv("org_name")
        pat = os.getenv("pat")

        result = check_project_exists(org_name, "1234567", pat)
        self.assertFalse(result)

    @patch('ado_api.project.requests.get')
    def test_api_failure_unauthorized(self, mock_get):
        # Mock 401 Unauthorized response
        mock_response = MagicMock()
        mock_response.status_code = 401
        # requests raise_for_status would be called if used, but we catch generic exceptions
        mock_get.return_value = mock_response

        # This should print debug info and return False
        result = check_project_exists("org", "project", "invalid-pat")
        self.assertFalse(result)

    @patch('ado_api.project.requests.get')
    def test_api_failure_exception(self, mock_get):
        # Mock a generic exception being raised during the request (e.g., Network timeout or DNS failure)
        # 使用 side_effect 來強制拋出錯誤，模擬根本連不上伺服器的情況
        mock_get.side_effect = Exception("Simulated network connection error")

        # This should enter the except block, print debug info, and return False
        result = check_project_exists("org", "project", "invalid-pat")

        # 斷言結果必須為 False
        self.assertFalse(result)
if __name__ == '__main__':
    unittest.main()
