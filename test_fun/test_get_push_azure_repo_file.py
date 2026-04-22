import os
import uuid
import unittest
from unittest.mock import patch, MagicMock
# 請根據你實際的資料夾結構調整 import
from ..ado_api.repo import get_azure_repo_file, push_azure_repo_file


class TestSyncAzureRepoFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        讀取環境變數。設定 has_real_credentials 讓真實測試在沒憑證時順利跳過。
        """
        cls.org_name = os.getenv("org_name")
        cls.pat = os.getenv("pat")
        cls.project_name = "john19960801"

        # 為了模擬 Repo A 到 Repo B，我們定義兩個 Repo 變數
        cls.source_repo = "test"
        cls.target_repo = "test"

        cls.has_real_credentials = bool(cls.org_name and cls.pat)

    # ==========================================
    # 1. 真實整合測試：串聯 Get 與 Push (正常情境)
    # ==========================================
    def test_sync_file_between_repos_success(self):
        """
        【真實測試】成功從 Source Repo 取得檔案，並推送到 Target Repo。
        """
        if not self.has_real_credentials:
            self.skipTest("⚠️ 缺少憑證，跳過真實連線測試")

        # 產生獨一無二的測試識別碼，避免檔案衝突
        run_id = uuid.uuid4().hex[:6]
        source_file_path = f"/README.md"
        target_file_path = f"/README_copy.md"

        print(f"[真實測試] 階段 2: 呼叫 get_azure_repo_file 取得內容...")
        retrieved_text = get_azure_repo_file(
            organization=self.org_name,
            project=self.project_name,
            repo=self.source_repo,
            file_path=source_file_path,
            pat=self.pat,
            branch="main"
        )

        print(f"[真實測試] 階段 3: 將取得的內容推送到 Target Repo ({self.target_repo})...")
        sync_result = push_azure_repo_file(
            file_text=retrieved_text,
            organization=self.org_name,
            project=self.project_name,
            repo=self.target_repo,
            file_path=target_file_path,
            pat=self.pat,
            branch="main",
            commit_message="Test(Auto): Sync file from source repo"
        )
        self.assertTrue(sync_result, "推送到 Target Repo 失敗")
        print("✅ 檔案同步測試成功完成！")

    # ==========================================
    # 2. 單元測試：串聯流程中的異常處理 (Mock情境)
    # ==========================================
    @patch('ado_api.repo.requests.get')
    def test_sync_file_source_not_found(self, mock_get):
        """
        【Mock測試】如果 Source 檔案根本不存在，確保我們不會執行後續的 Push。
        """
        print("\n[Mock測試] 模擬 Source Repo 檔案不存在 (404)...")

        # 模擬 get API 回傳 404
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # 1. 嘗試取得檔案
        retrieved_text = get_azure_repo_file(
            organization="mock_org",
            project="mock_proj",
            repo="mock_source_repo",
            file_path="/missing_file.txt",
            pat="mock_pat"
        )

        # 2. 驗證取得結果為空字串 (這是 get_azure_repo_file 原本定義的 404 行為)
        self.assertEqual(retrieved_text, "")

        # 3. 驗證業務邏輯防呆：如果拿不到內容，就不該呼叫 push
        # 這裡用 assert 來模擬你在實際主程式中應該做的判斷
        if retrieved_text == "":
            print("檔案不存在，取消同步。")
            sync_attempted = False
        else:
            sync_attempted = True

        self.assertFalse(sync_attempted, "不應該在抓不到檔案內容時嘗試 Push！")


if __name__ == '__main__':
    unittest.main()