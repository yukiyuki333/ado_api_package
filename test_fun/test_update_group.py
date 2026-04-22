import unittest
from unittest.mock import patch, MagicMock
from ado_api.member import update_group

class TestUpdateGroup(unittest.TestCase):

    @patch('ado_api.member.requests.post')
    @patch('ado_api.member.requests.put')
    def test_update_group_add_success(self, mock_put, mock_post):
        # 1. Mock user resolution
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'value': [{'descriptor': 'vssgp.user-123'}]
        }
        mock_post.return_value = mock_post_response

        # 2. Mock membership PUT
        mock_put_response = MagicMock()
        mock_put_response.status_code = 201
        mock_put.return_value = mock_put_response

        result = update_group("my-org", "vssgp.group-456", "test@user.com", True, "my-pat")
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        mock_put.assert_called_once()
        
        # Verify PUT URL contains descriptors
        put_url = mock_put.call_args[0][0]
        self.assertIn("vssgp.user-123", put_url)
        self.assertIn("vssgp.group-456", put_url)

    @patch('ado_api.member.requests.post')
    @patch('ado_api.member.requests.delete')
    def test_update_group_remove_success(self, mock_delete, mock_post):
        # 1. Mock user resolution
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'value': [{'descriptor': 'vssgp.user-123'}]
        }
        mock_post.return_value = mock_post_response

        # 2. Mock membership DELETE
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        mock_delete.return_value = mock_delete_response

        result = update_group("my-org", "vssgp.group-456", "test@user.com", False, "my-pat")
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        mock_delete.assert_called_once()

    @patch('ado_api.member.requests.post')
    def test_update_group_user_not_found(self, mock_post):
        # Mock empty user resolution
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {'value': []}
        mock_post.return_value = mock_post_response

        result = update_group("my-org", "vssgp.group-456", "non@existent.com", True, "my-pat")
        
        self.assertFalse(result)

    @patch('ado_api.member.requests.post')
    @patch('ado_api.member.requests.put')
    def test_update_group_membership_failure(self, mock_put, mock_post):
        # Mock user resolution
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'value': [{'descriptor': 'vssgp.user-123'}]
        }
        mock_post.return_value = mock_post_response

        # Mock membership failure
        mock_put_response = MagicMock()
        mock_put_response.status_code = 400
        mock_put_response.text = "Bad Request"
        mock_put.return_value = mock_put_response

        result = update_group("my-org", "vssgp.group-456", "test@user.com", True, "my-pat")
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
