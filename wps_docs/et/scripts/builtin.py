"""HTTP 版本的 builtins 函数

通过 HTTP 调用 KDocs API。
"""
import json
import time
import urllib.parse

import requests

_API_ORIGIN = 'https://www.kdocs.cn'
_API_BASE_URL = f'{_API_ORIGIN}/api/v3/office'
_WEBOFFICE_BRANCH = 'kdocs-amd-t-master-et-agentmode'


class HTTPBuiltins:
    """HTTP 版本的 builtins 函数"""

    def __init__(self, wps_sid: str, file_id: str):
        self._wps_sid = wps_sid
        self._file_id = file_id
        self._jsa_context = None

    def set_jsa_context(self, context: dict) -> None:
        self._jsa_context = context

    def _core_execute(self, command: str, param_json: str) -> str:
        param = json.loads(param_json)
        body = {
            "command": command,
            "param": param,
            "use_cache": True,
        }

        resp = requests.post(
            f'{_API_BASE_URL}/file/{self._file_id}/core/execute',
            cookies={'wps_sid': self._wps_sid, 'weboffice_branch': _WEBOFFICE_BRANCH},
            headers={'Origin': _API_ORIGIN},
            json=body,
            timeout=60
        )

        return resp.text

    def _evaluate_script(self, data_json: str) -> str:
        data = json.loads(data_json)
        script = data.get('script', '')

        url = f'{_API_BASE_URL}/file/{self._file_id}/script?runtime_version=2.0'
        resp = requests.post(
            url,
            cookies={'wps_sid': self._wps_sid, 'weboffice_branch': _WEBOFFICE_BRANCH},
            headers={'Origin': _API_ORIGIN},
            json={
                'script': script,
                'script_name': 'script',
                'file_id': self._file_id,
                'Context': self._jsa_context or {},
            },
            timeout=60
        )

        if resp.status_code != 200:
            return json.dumps({"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"})

        resp_data = resp.json()
        task_id = resp_data.get('task_id')

        if task_id:
            result = self._poll_task_result(task_id)
            return json.dumps(result)

        return json.dumps({"success": True, "data": self._normalize_script_data(resp_data)})

    @staticmethod
    def _normalize_script_data(data: dict) -> dict:
        """从 script API 返回值中提取 result.return，去除 contextInfo 包装。

        WebOffice /script API 返回: {result: {contextInfo: {...}, return: <脚本return值>}}
        归一化后: {result: <脚本return值>}
        """
        if isinstance(data, dict) and "result" in data:
            result = data["result"]
            if isinstance(result, dict) and "return" in result:
                data = dict(data)
                data["result"] = result["return"]
        return data

    def _poll_task_result(self, task_id: str) -> dict:
        max_poll = 10
        sleep_time = 1
        url_encoded_task_id = urllib.parse.quote(task_id)

        for _ in range(max_poll):
            time.sleep(sleep_time)
            resp = requests.get(
                f'{_API_ORIGIN}/api/v3/script/task?task_id={url_encoded_task_id}',
                cookies={'wps_sid': self._wps_sid, 'weboffice_branch': _WEBOFFICE_BRANCH},
                headers={'Origin': _API_ORIGIN},
                timeout=30
            )

            if resp.status_code != 200:
                continue

            resp_data = resp.json()
            if resp_data.get('status') == 'finished':
                if resp_data.get('error'):
                    return {"success": False, "error": resp_data['error']}
                return {"success": True, "data": self._normalize_script_data(resp_data.get('data', {}))}

        return {"success": False, "error": "Task timeout"}
