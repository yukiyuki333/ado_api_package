import unittest
from unittest.mock import patch, MagicMock
import os
from ado_api.member import get_group

class TestGetGroup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.org_name = os.getenv("org_name")
        cls.pat = os.getenv("pat")
        cls.contri_des = os.getenv("Contributors_descriptor")

    def test_get_group_success(self):
        result = get_group(self.org_name, "ProjectMember", "Contributors", self.pat)
        
        self.assertEqual(result, self.contri_des)


    @patch('ado_api.member.requests.get')
    def test_get_group_with_pagination(self, mock_get):
        # Mock first page response with continuation token
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            'value': [{'displayName': 'Other Group', 'descriptor': 'vssgp.other-123'}]
        }
        mock_response1.headers = {'X-MS-ContinuationToken': 'token123'}
        
        # Mock second page response
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            'value': [{'displayName': 'Target Group', 'descriptor': 'vssgp.target-456'}]
        }
        mock_response2.headers = {}
        
        mock_get.side_effect = [mock_response1, mock_response2]

        result = get_group("my-org", "ProjectManager", "Target Group", "my-pat")
        
        self.assertEqual(result, "vssgp.target-456")
        self.assertEqual(mock_get.call_count, 2)

    def test_get_group_invalid_type(self):
        result = get_group("my-org", "InvalidType", "Group Name", "my-pat")
        self.assertEqual(result, "")

    @patch('ado_api.member.requests.get')
    def test_get_group_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'value': []}
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = get_group("my-org", "ProjectMember", "Non Existent Group", "my-pat")
        
        self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()
