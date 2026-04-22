import unittest
from unittest.mock import patch, MagicMock
from ado_api_package.ado_api.pipeline import release_reserve_setter

class TestReleaseReserveSetter(unittest.TestCase):

    @patch('ado_api.pipeline.requests.get')
    @patch('ado_api.pipeline.requests.put')
    def test_release_reserve_setter_success(self, mock_put, mock_get):
        # 1. Mock List Definitions
        mock_list_response = MagicMock()
        mock_list_response.status_code = 200
        mock_list_response.json.return_value = {
            'value': [{'name': 'My Release', 'id': 123}]
        }
        
        # 2. Mock Get Definition
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'id': 123,
            'name': 'My Release',
            'environments': [
                {'name': 'Dev', 'retentionPolicy': {'daysToKeep': 1, 'releasesToKeep': 1, 'retainBuild': False}}
            ]
        }
        
        mock_get.side_effect = [mock_list_response, mock_get_response]

        # 3. Mock Put Update
        mock_put_response = MagicMock()
        mock_put_response.status_code = 200
        mock_put.return_value = mock_put_response

        result = release_reserve_setter("org", "proj", "My Release", "pat", 5, 30, True)
        
        self.assertTrue(result)
        self.assertEqual(mock_get.call_count, 2)
        mock_put.assert_called_once()
        
        # Verify PUT payload
        args, kwargs = mock_put.call_args
        payload = kwargs.get('json', {})
        policy = payload['environments'][0]['retentionPolicy']
        self.assertEqual(policy['daysToKeep'], 30)
        self.assertEqual(policy['releasesToKeep'], 5)
        self.assertEqual(policy['retainBuild'], True)

    @patch('ado_api.pipeline.requests.get')
    def test_release_reserve_setter_not_found(self, mock_get):
        mock_list_response = MagicMock()
        mock_list_response.status_code = 200
        mock_list_response.json.return_value = {'value': []}
        mock_get.return_value = mock_list_response

        result = release_reserve_setter("org", "proj", "NonExistent", "pat", 5, 30, True)
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
