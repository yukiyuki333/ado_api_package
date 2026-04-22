import unittest
from unittest.mock import patch, MagicMock
from ..ado_api.pipeline import trash_can_reserve_setter

class TestTrashCanReserveSetter(unittest.TestCase):

    @patch('ado_api.pipeline.requests.patch')
    def test_trash_can_reserve_setter_success(self, mock_patch):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        result = trash_can_reserve_setter("my-org", "my-project", "my-pat", 30)
        
        self.assertTrue(result)
        mock_patch.assert_called_once()
        
        # Verify PATCH payload
        args, kwargs = mock_patch.call_args
        payload = kwargs.get('json', {})
        self.assertEqual(payload['daysToKeepDeletedReleases'], 30)
        
        # Verify subdomain is vsrm
        url = args[0]
        self.assertIn("vsrm.dev.azure.com", url)

    @patch('ado_api.pipeline.requests.patch')
    def test_trash_can_reserve_setter_api_failure(self, mock_patch):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_patch.return_value = mock_response

        result = trash_can_reserve_setter("my-org", "my-project", "my-pat", 14)
        
        self.assertFalse(result)

    def test_trash_can_reserve_setter_validation_failure(self):
        # Test negative value
        result = trash_can_reserve_setter("my-org", "my-project", "my-pat", -1)
        self.assertFalse(result)

        # Test non-integer value
        result = trash_can_reserve_setter("my-org", "my-project", "my-pat", "30") # type: ignore
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
