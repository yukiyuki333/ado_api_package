import unittest
import os
import uuid
from ado_api.branch import create_branch, set_git_branch_policy

org_name = os.getenv("org_name")
pat = os.getenv("pat")


class TestAzureBranchAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        在整個測試類別 (Class) 開始執行前，只會跑一次的準備工作。
        我們在這裡讀取環境變數，這樣每個 test case 都能共用。
        """
        cls.org_name = os.getenv("org_name")
        cls.pat = os.getenv("pat")

        # 建議你也在 Pipeline 或本機環境變數設定這兩個值
        cls.project_name = "john19960810"
        cls.repo_name = "test"

        # 防呆機制：如果沒抓到變數，直接跳過這個 Class 裡面的所有測試
        if not cls.org_name or not cls.pat:
            raise unittest.SkipTest("⚠️ 缺少 org_name 或 pat 環境變數，跳過真實連線測試")

    # ==========================================
    # 測試：建立分支 (create_branch)
    # ==========================================
    def test_create_branch_success(self):
        """
        測試成功建立分支。使用 UUID 確保每次跑測試分支名稱都不一樣。
        """
        random_suffix = uuid.uuid4().hex[:6]
        new_branch = f"feature/test-auto-{random_suffix}"
        source_branch = "main"

        print(f"\n嘗試從 {source_branch} 建立新分支: {new_branch} ...")

        result = create_branch(
            organization=self.org_name,
            project=self.project_name,
            repo=self.repo_name,
            pat=self.pat,
            new_branch_name=new_branch,
            source_branch_name=source_branch
        )

        # 使用 unittest 專用的斷言語法
        self.assertTrue(result)

    def test_create_branch_source_not_found(self):
        """
        測試失敗情境：給予一個根本不存在的來源分支，系統應回傳 False
        """
        result = create_branch(
            organization=self.org_name,
            project=self.project_name,
            repo=self.repo_name,
            pat=self.pat,
            new_branch_name="feature/should-fail",
            source_branch_name="non-existent-branch-9999"
        )

        self.assertFalse(result)

    # ==========================================
    # 測試：設定分支 Policy (set_git_branch_policy)
    # ==========================================
    def test_set_git_branch_policy_success(self):
        """
        測試成功為分支設定 Policy。
        """
        target_branch = "main"

        print(f"\n嘗試為分支 {target_branch} 設定 3 項 Policy ...")

        result = set_git_branch_policy(
            organization=self.org_name,
            project=self.project_name,
            repo=self.repo_name,
            branch=target_branch,
            pat=self.pat
        )

        self.assertTrue(result)

    def test_set_git_branch_policy_repo_not_found(self):
        """
        測試失敗情境：給予一個錯誤的 Repo 名稱，系統應回傳 False
        """
        result = set_git_branch_policy(
            organization=self.org_name,
            project=self.project_name,
            repo="invalid_repo_name_9999",
            branch="main",
            pat=self.pat
        )

        self.assertFalse(result)


if __name__ == '__main__':
    # 讓你可以直接用 python test_branch.py 來執行測試
    unittest.main()