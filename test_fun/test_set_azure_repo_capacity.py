import os
import unittest
from unittest.mock import patch, MagicMock
from ado_api.repo import set_azure_repo_capacity


class TestSetAzureRepoCapacity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        讀取環境變數。
        我們用一個布林值 `has_real_credentials` 來記錄是否有真實憑證，
        這樣可以讓 Mock 測試在沒有憑證時依然能順利執行。
        """
        cls.org_name = os.getenv("org_name")
        cls.pat = os.getenv("pat")
        cls.project_name = "john19960801"
        cls.repo_name = "test"

        cls.has_real_credentials = bool(cls.org_name and cls.pat)

    # ==========================================
    # 1. 真實整合測試 (不使用 Mock)
    # ==========================================
    def test_set_azure_repo_capacity_success(self):
        """
        【真實測試】成功為 Repo 設定容量上限。
        """
        if not self.has_real_credentials:
            self.skipTest("⚠️ 缺少 org_name 或 pat，跳過真實連線測試")

        print(f"\n[真實測試] 嘗試為 Repo '{self.repo_name}' 設定容量限制...")

        result = set_azure_repo_capacity(
            organization=self.org_name,
            project=self.project_name,
            repo=self.repo_name,
            pat=self.pat
        )
        self.assertTrue(result)

    def test_set_azure_repo_capacity_repo_not_found(self):
        """
        【真實測試】給予一個根本不存在的 Repo 名稱，系統應回傳 False。
        """
        if not self.has_real_credentials:
            self.skipTest("⚠️ 缺少 org_name 或 pat，跳過真實連線測試")

        fake_repo_name = "invalid-repo-name-9999"
        print(f"\n[真實測試] 嘗試為不存在的 Repo '{fake_repo_name}' 設定容量限制...")

        result = set_azure_repo_capacity(
            organization=self.org_name,
            project=self.project_name,
            repo=fake_repo_name,
            pat=self.pat
        )
        self.assertFalse(result)

    # ==========================================
    # 2. 單元測試 (使用 Mock 模擬極端異常)
    # ==========================================
    @patch('ado_api.repo.requests.post')
    @patch('ado_api.repo.requests.get')
    def test_set_azure_repo_capacity_policy_failure(self, mock_get, mock_post):
        """
        【Mock測試】模擬 Azure API 發生 400 Bad Request 的罕見情況。
        因為是 Mock，所以不需要真實的 PAT 也能跑。
        注意：@patch 裝飾器的順序與參數順序是相反的！(post 在上，所以對應 mock_post 在後)
        """
        print("\n[Mock測試] 模擬 API 拒絕設定 Policy (400 Bad Request)...")

        # 第一步：模擬 GET 成功取得 Repo ID
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'id': 'repo-guid-123'}
        mock_get.return_value = mock_get_response

        # 第二步：模擬 POST 建立 Policy 時被伺服器拒絕 (400)
        mock_post_response = MagicMock()
        mock_post_response.status_code = 400
        mock_post_response.text = "Bad Request: Invalid Policy Settings"
        mock_post.return_value = mock_post_response

        # 呼叫函數 (這裡帶入什麼假字串都沒關係，因為 requests 已經被攔截了)
        result = set_azure_repo_capacity("mock-org", "mock-project", "mock-repo", "mock-pat")

        # 斷言結果為 False，並確認兩個假 API 都有被呼叫過一次
        self.assertFalse(result)
        mock_get.assert_called_once()
        mock_post.assert_called_once()


if __name__ == '__main__':
    unittest.main()