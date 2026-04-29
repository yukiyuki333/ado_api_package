import requests
from requests.auth import HTTPBasicAuth

def get_repo_id_by_name(organization: str, project: str, repo_name: str, pat: str) -> str:
    """
    透過 Repo 名稱自動查詢並回傳 repo_id
    """
    auth = HTTPBasicAuth('', pat)
    url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories?api-version=7.1"
    
    try:
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            repos = response.json().get('value', [])
            for r in repos:
                if r['name'] == repo_name:
                    return r['id']
            print(f"❌ 找不到名為 '{repo_name}' 的 Repo")
        else:
            print(f"❌ 無法取得 Repo 列表: {response.status_code}")
    except Exception as e:
        print(f"查詢 Repo ID 時發生錯誤: {str(e)}")
    return None


def create_azure_pipeline_auto(organization: str, project: str, repo_name: str, pipeline_name: str, yaml_path: str, pat: str) -> dict:
    """
    全自動版：給名稱就好，ID 我自己查，查完直接建立 Pipeline。
    """
    # 1. 懶人第一步：自己查 repo_id
    repo_id = get_repo_id_by_name(organization, project, repo_name, pat)
    if not repo_id:
        return {} # 找不到就不用玩了

    # 2. 準備建立 Pipeline 的 API
    auth = HTTPBasicAuth('', pat)
    url = f"https://dev.azure.com/{organization}/{project}/_apis/build/definitions?api-version=7.1"
    
    payload = {
        "name": pipeline_name,
        "type": "build",
        "quality": "definition",
        "process": {
            "yamlFilename": yaml_path, # 例如: "/pipelines/main.yml"
            "type": 2
        },
        "repository": {
            "id": repo_id, # 這裡是剛才查到的 ID
            "name": repo_name,
            "type": "TfsGit"
        },
        "queue": {
            "name": "Azure Pipelines"
        }
    }

    try:
        response = requests.post(url, auth=auth, json=payload)
        if response.status_code in [200, 201]:
            print(f"✅ 成功為 Repo '{repo_name}' 建立 Pipeline: {pipeline_name}")
            return response.json()
        else:
            print(f"❌ 建立 Pipeline 失敗: {response.text}")
            return {}
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        return {}


def run_azure_pipeline(organization: str, project: str, pipeline_name: str, pat: str, branch: str = "main") -> dict:
    """
    Triggers a run for an Azure DevOps pipeline based on its name and branch.

    Args:
        organization (str): The Azure DevOps organization name.
        project (str): The name or ID of the project.
        pipeline_name (str): The display name of the pipeline to search for.
        pat (str): Personal Access Token for authentication.
        branch (str, optional): The target branch for the run. Defaults to "main".

    Returns:
        dict: The JSON response of the pipeline run on success, otherwise an empty dictionary.
    """
    auth = HTTPBasicAuth('', pat)
    
    try:
        # 1. Resolve pipeline name to pipeline ID
        list_url = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines?api-version=7.1"
        list_response = requests.get(list_url, auth=auth)
        
        if list_response.status_code != 200:
            print(f"Execution failed: Could not fetch pipeline list. Status: {list_response.status_code}")
            return {}
            
        pipelines = list_response.json().get('value', [])
        pipeline_id = None
        for p in pipelines:
            if p.get('name') == pipeline_name:
                pipeline_id = p.get('id')
                break
                
        if not pipeline_id:
            print(f"Execution failed: Pipeline '{pipeline_name}' not found.")
            return {}

        # 2. Trigger the pipeline run
        run_url = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines/{pipeline_id}/runs?api-version=7.1"
        
        # Build refName
        if not branch.startswith("refs/"):
            ref_name = f"refs/heads/{branch}"
        else:
            ref_name = branch
            
        run_body = {
            "resources": {
                "repositories": {
                    "self": {
                        "refName": ref_name
                    }
                }
            }
        }
        
        run_response = requests.post(run_url, auth=auth, json=run_body)
        
        if run_response.status_code in [200, 201, 202]:
            return run_response.json()
        else:
            print(f"Execution failed: Trigger API returned status code {run_response.status_code}")
            print(f"Response: {run_response.text}")
            return {}
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return {}

def trash_can_reserve_setter(organization: str, project: str, pat: str, reserve_days_in_trash_can: int) -> bool:
    """
    Sets the retention policy for manually deleted release pipelines (trash can duration).

    Args:
        organization (str): The Azure DevOps organization name.
        project (str): The name or ID of the project.
        pat (str): Personal Access Token for authentication.
        reserve_days_in_trash_can (int): Number of days to keep deleted releases in the trash can.

    Returns:
        bool: True if the setting was successfully updated, False otherwise.
    """
    # 1. Validation
    if not isinstance(reserve_days_in_trash_can, int) or reserve_days_in_trash_can < 0:
        print(f"Validation failed: reserve_days_in_trash_can must be a non-negative integer. Received: {reserve_days_in_trash_can}")
        return False

    auth = HTTPBasicAuth('', pat)
    
    try:
        # 2. Release Retention API URL
        # Note: Release APIs often use the vsrm.dev.azure.com subdomain
        url = f"https://vsrm.dev.azure.com/{organization}/{project}/_apis/release/retention?api-version=7.1-preview.1"
        
        # 3. Request Body
        payload = {
            "daysToKeepDeletedReleases": reserve_days_in_trash_can
        }
        
        # 4. Perform Update (PATCH)
        response = requests.patch(url, auth=auth, json=payload)
        
        if response.status_code == 200:
            return True
        else:
            print(f"Execution failed: Retention API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return False

def release_reserve_setter(organization: str, project: str, pipeline_name: str, pat: str, reserve_generations: int, default_reserve_days: int, reserve_build: bool) -> bool:
    """
    Updates the retention policy for a specific Release Pipeline based on its name.

    Args:
        organization (str): The Azure DevOps organization name.
        project (str): The name or ID of the project.
        pipeline_name (str): The display name of the Release Pipeline.
        pat (str): Personal Access Token for authentication.
        reserve_generations (int): Number of recent releases to keep (releasesToKeep).
        default_reserve_days (int): Number of days to keep a release (daysToKeep).
        reserve_build (bool): Whether to protect associated Build records (retainBuild).

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    auth = HTTPBasicAuth('', pat)
    
    try:
        # 1. Resolve pipeline name to definition ID
        # Note: Classic Release Pipelines use vsrm.dev.azure.com
        list_url = f"https://vsrm.dev.azure.com/{organization}/{project}/_apis/release/definitions?api-version=7.1"
        list_response = requests.get(list_url, auth=auth)
        
        if list_response.status_code != 200:
            print(f"Execution failed: Could not fetch Release Definition list. Status: {list_response.status_code}")
            return False
            
        definitions = list_response.json().get('value', [])
        definition_id = None
        for d in definitions:
            if d.get('name') == pipeline_name:
                definition_id = d.get('id')
                break
                
        if definition_id is None:
            print(f"Execution failed: Release Definition '{pipeline_name}' not found.")
            return False

        # 2. Get full definition object
        get_url = f"https://vsrm.dev.azure.com/{organization}/{project}/_apis/release/definitions/{definition_id}?api-version=7.1"
        get_response = requests.get(get_url, auth=auth)
        
        if get_response.status_code != 200:
            print(f"Execution failed: Could not fetch definition object. Status: {get_response.status_code}")
            return False
            
        definition = get_response.json()

        # 3. Modify retention policy for all environments
        environments = definition.get('environments', [])
        for env in environments:
            if 'retentionPolicy' not in env:
                env['retentionPolicy'] = {}
            
            policy = env['retentionPolicy']
            policy['daysToKeep'] = default_reserve_days
            policy['releasesToKeep'] = reserve_generations
            policy['retainBuild'] = reserve_build

        # 4. Apply Update (PUT)
        update_url = f"https://vsrm.dev.azure.com/{organization}/{project}/_apis/release/definitions/{definition_id}?api-version=7.1"
        update_response = requests.put(update_url, auth=auth, json=definition)
        
        if update_response.status_code == 200:
            return True
        else:
            print(f"Execution failed: Release Update API returned status code {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return False
