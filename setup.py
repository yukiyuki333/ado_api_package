from setuptools import setup, find_packages

setup(
    name="ado_api_package",                   # 套件名稱，不一定要跟資料夾同名，但建議一致
    version="0.1.0",                  # 版本號
    author="yukiyuki333",               # 你的名字
    author_email="713883441ohya@gmail.com",
    description="A Python API wrapper for Azure DevOps",
    long_description=open("README.md", encoding="utf-8").read(), # 讀取 README 作為詳細說明
    long_description_content_type="text/markdown",
    
    # package_dir={"": "ado_api"},
    # packages=find_packages(where="ado_api"),
    packages=["ado_api"],
    
    # 如果你的套件有依賴其他的第三方套件 (例如 requests)，要在這裡列出
    install_requires=[
        "requests>=2.25.1",
        # "pandas>=1.0.0", 
    ],
    
    python_requires=">=3.7",          # 支援的最低 Python 版本
)