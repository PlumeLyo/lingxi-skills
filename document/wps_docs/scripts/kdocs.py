"""
kdocs.py

WPS 365 V7 API 封装模块，提供 Drive（云文档）能力。
认证通过环境变量注入，无需额外配置。

用法示例：
    import kdocs

    result = kdocs.download_file(file_id="xxx", save_dir="/tmp")


"""

import hashlib
import json
import os
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Optional

import requests

from wps_http import BaseClient


# ──────────────────────────────────────────────────────────────────────────────
# 时间工具
# ──────────────────────────────────────────────────────────────────────────────

_TIME_FIELDS = frozenset(
    (
        "ctime",
        "mtime",
        "create_time",
        "update_time",
        "start_time",
        "end_time",
        "regtime",
    )
)


def _ts_to_iso(ts: Any) -> Optional[str]:
    """秒级或毫秒级时间戳 → UTC ISO 8601 字符串。"""
    if ts is None:
        return None
    try:
        t = int(ts)
    except (TypeError, ValueError):
        return None
    if t <= 0:
        return None
    if t > 1e12:
        t = t / 1000.0
    dt = datetime.utcfromtimestamp(t).replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_to_ts(iso: Optional[str]) -> Optional[int]:
    """ISO 8601 字符串 → 秒级时间戳，无时区按 UTC 处理。"""
    if not iso or not isinstance(iso, str):
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except (ValueError, TypeError):
        return None


def _format_time_china(iso_time: str) -> str:
    """
    将 UTC ISO 8601 时间转换为中国时区（UTC+8）的可读格式。

    Args:
        iso_time: UTC ISO 8601 时间字符串，如 "2026-03-12T13:39:57Z"

    Returns:
        中国时区时间字符串，如 "2026-03-12 21:39:57"
    """
    if not iso_time:
        return ""

    try:
        # 解析 UTC 时间
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # 转换为中国时区（UTC+8）
        from datetime import timedelta

        china_tz = timezone(timedelta(hours=8))
        dt_china = dt.astimezone(china_tz)

        # 格式化为易读格式
        return dt_china.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_time  # 如果转换失败，返回原始字符串


def _normalize_times(data: Any) -> Any:
    """递归将响应中已知时间字段由时间戳转为 ISO 8601。"""
    if isinstance(data, dict):
        for k, v in list(data.items()):
            if k in _TIME_FIELDS and v is not None:
                try:
                    data[k] = _ts_to_iso(v)
                except Exception:
                    pass
            else:
                data[k] = _normalize_times(v)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = _normalize_times(item)
    return data


def _wrap(resp: Any) -> dict:
    """统一响应结构，对 data 字段做时间字段转换。"""
    if not isinstance(resp, dict):
        return {}
    out = dict(resp)
    if out.get("data") is not None:
        out["data"] = _normalize_times(out["data"])
    return out


def _format_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读的格式。

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的字符串，如 "1.23 MB", "456.78 KB", "123 B"
    """
    if size_bytes < 0:
        return "0 B"

    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        size_kb = size_bytes / 1024
        return f"{size_kb:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.2f} MB"
    else:
        size_gb = size_bytes / (1024 * 1024 * 1024)
        return f"{size_gb:.2f} GB"


def _encode_query_value(s: str) -> str:
    """对 query 参数值做最小化编码：只转义会破坏 URL 结构的 ASCII 特殊字符，保留中文等非 ASCII 字符可读性。"""
    _must_encode = set(' \t\n\r&=?#%+;,<>[]{}|\\^`"\'')
    return "".join(
        urllib.parse.quote(c, safe="") if (c.isascii() and c in _must_encode) else c
        for c in s
    )


def _append_link_params(url: str, file_name: str) -> str:
    """在云文档 URL 后拼接 lingxi_file_name query 参数。"""
    if not url or not file_name:
        return url
    sep = "&" if "?" in url else "?"
    return url + sep + f"lingxi_file_name={_encode_query_value(file_name)}"


def _make_result(success: bool, data: Any = None, message: str = "", error: str = "") -> dict:
    """
    创建统一的返回结果格式。
    空值字段将被移除，只返回有实际内容的字段。

    Args:
        success: 是否成功
        data: 返回的数据
        message: 成功消息
        error: 错误消息

    Returns:
        {
            "success": bool,
            "data": Any (如果不为 None),
            "message": str (如果不为空),
            "error": str (如果不为空)
        }
    """
    result = {"success": success}

    # 只添加非空值
    if data is not None:
        result["data"] = data
    if message:
        result["message"] = message
    if error:
        result["error"] = error

    return result


def _extract_data(resp: dict, error_prefix: str = "操作失败") -> dict:
    """
    从 API 响应中提取数据，返回友好的结果格式。

    Args:
        resp: API 原始响应 {code, msg, data}
        error_prefix: 错误消息前缀

    Returns:
        友好的结果格式
    """
    if not isinstance(resp, dict):
        return _make_result(False, error=f"{error_prefix}: 无效响应")

    code = resp.get("code", -1)
    if code == 0:
        return _make_result(True, data=resp.get("data"), message="操作成功")
    else:
        error_msg = resp.get("msg", "未知错误")
        return _make_result(False, error=f"{error_prefix}: {error_msg}")


# ──────────────────────────────────────────────────────────────────────────────
# WpsClient
# ──────────────────────────────────────────────────────────────────────────────


class WpsClient(BaseClient):
    """
    WPS 365 V7 API 统一客户端。
    HTTP 请求层由内部 WpsSession 对象统一管理，Cookie / Header 集中注入。

    能力：
      Drive（云文档）：下载文件、上传文件、获取文件内容详情
    """

    _instance: Optional["WpsClient"] = None

    def __new__(cls, base_url: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # v5 接口 base（纯数字 ID 文件）
    _V5_BASE = "https://365.kdocs.cn/3rd/drive"
    # v7 接口 base（非纯数字 ID 文件，默认）
    _V7_BASE = "https://api.wps.cn"

    def __init__(self, base_url: Optional[str] = None):
        if hasattr(self, "_session"):
            return
        super().__init__(base_url)
        self._session = self._s
        self._v7_base = self._v7
        self._v5_base = os.environ.get("WPS_V5_API_BASE", self._V5_BASE).rstrip("/")

    # ──────────────────────────────────────────────────────────────────────────
    # Drive：云文档
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_file_info(self, meta: dict, file_id: str, drive_id: str) -> dict:
        """
        从 API 返回的元数据中提取关键文件信息。
        返回统一格式的文件信息字典。
        """
        size_bytes = meta.get("size", 0)
        name = meta.get("name", "")
        file_info = {
            "file_id": file_id,
            "name": name,
            "link_url": _append_link_params(meta.get("link_url", ""), name),
            "size": _format_size(size_bytes),
            "ctime": meta.get("ctime", ""),
        }

        # 提取创建者信息
        created_by = meta.get("created_by", {})
        if created_by:
            file_info["created_by"] = {
                "id": created_by.get("id", ""),
                "name": created_by.get("name", ""),
            }

        return file_info

    def _resolve_drive_id(self, drive_id: str) -> str:
        """将 private/roaming 名称解析为实际 drive_id；已是 ID 则原样返回。"""
        if drive_id not in ("private", "roaming"):
            return drive_id
        resp = self._session.get(
            f"{self._v7_base}/v7/drives",
            params={"allotee_type": "user", "page_size": 10},
        )
        if resp.get("code") != 0:
            raise ValueError(resp.get("msg") or "获取云盘列表失败")
        items = (resp.get("data") or {}).get("items") or []
        for item in items:
            if drive_id == "private" and item.get("name") == "我的企业文档":
                return item["id"]
            if drive_id == "roaming" and item.get("name") == "自动备份":
                return item["id"]
        if items:
            return items[0]["id"]
        raise ValueError(f"未找到云盘: {drive_id}")

    def create_folder(self, folder_name: str, parent_id: str = "0", drive_id: Optional[str] = None) -> dict:
        """
        在云端创建文件夹。

        folder_name: 文件夹名称。
        parent_id: 父文件夹 ID，默认 "0" 表示根目录。
        drive_id: 云盘 ID，不传时使用私人云盘。
        """
        try:
            did = drive_id or self._resolve_drive_id("private")
            resp = _wrap(
                self._session.post(
                    f"{self._v7_base}/v7/drives/{did}/files/{parent_id}/create",
                    {"name": folder_name, "file_type": "folder"},
                )
            )
            if resp.get("code") != 0:
                return _make_result(False, error=f"创建文件夹失败: {resp.get('msg', '未知错误')}")
            raw = resp.get("data") or {}
            folder_id = str(raw.get("id") or "")
            if not folder_id:
                return _make_result(False, error="创建文件夹成功但未返回 id")
            return _make_result(True, data=folder_id, message=f"文件夹「{folder_name}」创建成功，file_id: {folder_id}")
        except Exception as e:
            return _make_result(False, error=f"创建文件夹失败: {str(e)}")

    def find_folder_by_path(self, folder_path: str, drive_id: Optional[str] = None) -> str:
        """
        按名称或路径查找文件夹，返回其 file_id。

        folder_path:
          - 单层名称，如 "lingxiClaw" → 在根目录下查找该名称的文件夹
          - 多层路径（用"/"分隔），如 "工作/项目A" → 从根目录逐层查找

        drive_id 不传时自动使用私人云盘。
        找不到时抛出 ValueError。
        """
        did = drive_id or self._resolve_drive_id("private")
        parts = [p.strip() for p in folder_path.split("/") if p.strip()]
        if not parts:
            raise ValueError("folder_path 不能为空")

        current_id = "0"
        for part in parts:
            found = None
            page_token = None
            while True:
                params: dict = {"page_size": 500, "filter_type": "folder"}
                if page_token:
                    params["page_token"] = page_token
                resp = _wrap(
                    self._session.get(
                        f"{self._v7_base}/v7/drives/{did}/files/{current_id}/children",
                        params=params,
                    )
                )
                if resp.get("code") != 0:
                    raise ValueError(f"查询文件夹失败: {resp.get('msg', '未知错误')}")
                data = resp.get("data") or {}
                for item in data.get("items") or []:
                    if item.get("name") == part and item.get("type") == "folder":
                        found = item["id"]
                        break
                if found:
                    break
                page_token = data.get("next_page_token")
                if not page_token:
                    break

            if not found:
                raise ValueError(
                    f"未找到文件夹「{part}」（路径: {folder_path}）。"
                )
            current_id = found

        return current_id

    # 直接走二进制下载接口的后缀（Office 格式）
    _DIRECT_DOWNLOAD_EXTS = frozenset((".docx", ".pptx", ".xlsx", ".doc", ".ppt", ".xls", ".pdf"))
    # ksheet 专属后缀
    _KSHEET_EXT = ".ksheet"
    # 智能文档后缀
    _OTL_EXT = ".otl"
    _KDOCS_BASE = "https://365.kdocs.cn"

    def get_file_info(self, file_id: str) -> dict:
        """
        获取云文档文件信息（元数据）。
        file_id: 文件ID（内部自动查找所在云盘）
        返回格式：
        {
            "success": True/False,
            "data": {
                "file_id": "文件ID",
                "name": "文件名",
                "link_url": "云文档链接",
                "size": "文件大小（如 '1.23 MB', '456.78 KB', '123 B'）",
                "ctime": "创建时间(ISO 8601)",
                "created_by": {
                    "id": "创建者ID",
                    "name": "创建者名称"
                }
            },
            "message": "成功获取文件信息: xxx.ksheet",
            "error": ""
        }
        """
        try:
            did, meta = self._find_drive_and_meta(file_id)
            file_info = self._extract_file_info(meta, file_id, did)
            return _make_result(True, data=file_info, message=f"成功获取文件信息: {file_info['name']}")
        except Exception as e:
            err_msg = str(e)
            if "权限" in err_msg or "403" in err_msg:
                return _make_result(False, error="获取文件信息失败: 无权限。请停止当前操作，并提示用户向文件所有者申请访问权限后重试。")
            return _make_result(False, error=f"获取文件信息失败: {err_msg}")

    def download_file(
        self,
        file_id: str,
        save_dir: Optional[str] = None,
    ) -> dict:
        """
        下载云文档文件到本地，根据文件后缀自动选择下载策略：
          - .docx / .pptx / .xlsx 等 Office 格式：直接下载
          - .otl 智能文档：自动转换为 .md 文件
          - .ksheet 金山表格：自动转换为 .xlsx 文件
        返回格式：
        {
            "success": True/False,
            "data": {
                "file_id": "文件ID",
                "name": "云端文件名",
                "link_url": "云文档链接",
                "size": "文件大小（如 '1.23 MB', '456.78 KB'）",
                "ctime": "创建时间",
                "created_by": {"id": "创建者ID", "name": "创建者名称"}
            },
            "message": "下载成功，保存路径为: /path/to/file.xlsx，由于 .ksheet 格式无法直接下载，已自动转换为 .xlsx 格式",
            "error": ""
        }
        """
        try:
            # 获取文件元数据
            did, meta = self._find_drive_and_meta(file_id)

            # 使用公共函数提取文件信息
            file_info = self._extract_file_info(meta, file_id, did)

            file_name = file_info["name"] or file_id
            ext = os.path.splitext(file_name)[1].lower()

            save_dir = save_dir or os.getcwd()
            os.makedirs(save_dir, exist_ok=True)

            # 根据文件类型选择下载策略
            if ext in self._DIRECT_DOWNLOAD_EXTS:
                result = self._download_direct(did, file_id, file_name, save_dir, strategy="direct")
                local_path = result["file_path"]
                local_name = result["name"]
                local_size = result["size"]
                converted_msg = ""
            elif ext == self._OTL_EXT:
                return _make_result(
                    False,
                    error="智能文档（.otl）请使用 AP 模块的 ap.download_otl(file_id) 进行下载",
                )
            elif ext == self._KSHEET_EXT:
                result = self._download_ksheet(file_id, file_name, save_dir)
                local_path = result["file_path"]
                local_name = result["name"]
                local_size = result["size"]
                converted_msg = f"，由于 .ksheet 格式无法直接下载，已自动转换为 .xlsx 格式"
            else:
                # 未知格式，尝试直接下载
                result = self._download_direct(did, file_id, file_name, save_dir, strategy="direct_fallback")
                local_path = result["file_path"]
                local_name = result["name"]
                local_size = result["size"]
                converted_msg = ""

            # 格式化文件大小
            size_mb = local_size / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{local_size / 1024:.2f} KB"

            # 根据本地文件后缀名生成处理建议
            local_ext = os.path.splitext(local_name)[1].lower()
            if local_ext == ".md":
                read_suggestion = "。可调用 `python_cell_exec` 工具读取文档内容"
            elif local_ext in (".xlsx", ".xls"):
                read_suggestion = "。可读取 xlsx skill 明确处理 Excel 文档的方式"
            else:
                read_suggestion = ""

            # 构建消息
            message = f"下载成功，保存路径为: {local_path}{converted_msg}{read_suggestion}"

            return _make_result(True, data=file_info, message=message)
        except Exception as e:
            err_msg = str(e)
            if "无权限" in err_msg or "403" in err_msg:
                return _make_result(False, error="下载失败: 无权限。请停止当前操作，并提示用户向文件所有者申请访问权限后重试。")
            return _make_result(False, error=f"下载失败: {err_msg}")

    @staticmethod
    def _is_numeric_id(file_id: str) -> bool:
        """判断 file_id 是否为纯数字（对应旧版 v5 接口）。"""
        try:
            int(file_id)
            return True
        except (TypeError, ValueError):
            return False

    def _find_drive_and_meta(self, file_id: str) -> tuple:
        """
        给定 file_id，自动选择接口获取文件元数据，返回 (drive_id, meta_dict)。
          - 纯数字 ID：使用 v5 接口 GET /api/v5/files/{file_id}/metadata
          - 非纯数字 ID：使用 v7 接口 GET /v7/files/{file_id}/meta
        """
        if self._is_numeric_id(file_id):
            return self._find_meta_v5(file_id)
        return self._find_meta_v7(file_id)

    def _find_meta_v5(self, file_id: str) -> tuple:
        """
        通过 v5 接口获取纯数字 ID 文件的元数据，返回 ("", meta_dict)。
        v5 响应：{result:"ok", fileinfo:{fname,fsize,link_id,link_url,ctime,mtime,...}}
        统一映射为与 v7 兼容的字段格式。
        """
        resp = self._session.get(
            f"{self._v5_base}/api/v5/files/{file_id}/metadata",
            params={"with_link": "true"},
        )
        if resp.get("result") != "ok":
            raise ValueError(f"v5 接口无法获取文件元数据，请确认 file_id 正确且有访问权限: {file_id}")
        fi = resp.get("fileinfo") or {}
        meta = {
            "name": fi.get("fname", ""),
            "size": fi.get("fsize", 0),
            "link_url": fi.get("link_url", ""),
            "link_id": fi.get("link_id", ""),
            "ctime": _ts_to_iso(fi.get("ctime")),
            "mtime": _ts_to_iso(fi.get("mtime")),
            "created_by": {
                "id": str(fi.get("groupid", "")),
                "name": fi.get("user_nickname", ""),
            },
            "modified_by": {
                "id": str(fi.get("groupid", "")),
                "name": fi.get("user_nickname", ""),
            },
        }
        return "", meta

    def _find_meta_v7(self, file_id: str) -> tuple:
        """通过 v7 接口获取非纯数字 ID 文件的元数据，返回 (drive_id, meta_dict)。"""
        resp = _wrap(self._session.get(f"{self._v7_base}/v7/files/{file_id}/meta"))
        if resp.get("code") == 0 and resp.get("data"):
            meta = resp["data"]
            drive_id = meta.get("drive_id", "")
            return drive_id, meta
        raise ValueError(f"v7 接口无法获取文件元数据，请确认 file_id 正确且有访问权限: {file_id}")

    def _save_bytes(self, content: bytes, save_dir: str, file_name: str) -> str:
        """将字节写入 save_dir/file_name，返回完整路径。"""
        save_path = os.path.join(save_dir, file_name)
        with open(save_path, "wb") as f:
            f.write(content)
        return save_path

    def _download_direct(self, drive_id: str, file_id: str, file_name: str, save_dir: str, strategy: str) -> dict:
        """
        获取临时下载 URL 后下载二进制文件。
          - 纯数字 ID：v5 接口 GET /api/v5/files/{file_id}/download，响应 {result:"ok", url:...}
          - 非纯数字 ID：v7 接口 GET /v7/drives/{drive_id}/files/{file_id}/download，响应 {code:0, data:{url:...}}
        """
        if self._is_numeric_id(file_id):
            url_resp = self._session.get(
                f"{self._v5_base}/api/v5/files/{file_id}/download",
                params={"with_link": "true"},
            )
            if url_resp.get("result") != "ok":
                raise ValueError(url_resp.get("msg") or "v5 获取下载地址失败")
            url = url_resp.get("url") or url_resp.get("download_url")
        else:
            url_resp = _wrap(self._session.get(f"{self._v7_base}/v7/drives/{drive_id}/files/{file_id}/download"))
            if url_resp.get("code") != 0:
                raise ValueError(url_resp.get("msg") or "v7 获取下载地址失败")
            url = (url_resp.get("data") or {}).get("url") or (url_resp.get("data") or {}).get("download_url")

        if not url:
            raise ValueError("获取下载地址失败：响应中无 url 字段")

        r = self._session.download(url)
        r.raise_for_status()
        save_path = self._save_bytes(r.content, save_dir, file_name)
        return {
            "file_path": save_path,
            "name": file_name,
            "size": len(r.content),
            "strategy": strategy,
        }

    def _download_ksheet(self, file_id: str, file_name: str, save_dir: str) -> dict:
        """
        ksheet 异步导出：
          1. POST /api/v3/office/file/{file_id}/export/ksheet/async-export  创建导出任务
          2. GET  /api/v3/office/file/{file_id}/export/ksheet/export-progress  轮询获取下载链接
          3. 下载二进制内容
        """
        import time

        export_url = f"{self._KDOCS_BASE}/api/v3/office/file/{file_id}/export/ksheet/async-export"
        progress_url = f"{self._KDOCS_BASE}/api/v3/office/file/{file_id}/export/ksheet/export-progress"

        # 步骤一：创建导出任务
        r = self._session._http.post(export_url, json={}, timeout=30)
        task_resp = r.json() if r.content else {}
        if task_resp.get("result") != "ok":
            raise ValueError(f"创建 ksheet 导出任务失败: {task_resp}")

        task_key = (task_resp.get("data") or {}).get("key")
        download_url = (task_resp.get("data") or {}).get("url")

        # 步骤二：若首次响应已含 url 则直接使用，否则轮询进度
        if not download_url:
            for _ in range(20):
                time.sleep(2)
                pr = self._session._http.get(
                    progress_url,
                    params={"key": task_key} if task_key else None,
                    timeout=30,
                )
                progress_resp = pr.json() if pr.content else {}
                download_url = (progress_resp.get("data") or {}).get("url")
                if download_url:
                    break
            else:
                raise ValueError("ksheet 导出超时，未获取到下载链接")

        # 步骤三：下载文件
        r = self._session.download(download_url)
        r.raise_for_status()
        # 导出后文件格式为 xlsx
        xlsx_name = os.path.splitext(file_name)[0] + ".xlsx"
        save_path = self._save_bytes(r.content, save_dir, xlsx_name)
        return {
            "file_path": save_path,
            "name": xlsx_name,
            "size": len(r.content),
            "strategy": "ksheet_export",
        }

    def _upload_md_as_otl(self, file_path: str, folder_id: Optional[str] = None) -> dict:
        """
        将本地 .md 文件转换为 .otl 智能文档上传到云端。
        流程：
          1. 在云端云盘指定文件夹（默认根目录）新建同名 .otl 文件
          2. 读取本地 .md 内容，通过 core/execute insertContent 接口写入
        """
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        otl_name = base_name + ".otl"
        did = self._resolve_drive_id("private")
        pid = folder_id if folder_id else "0"

        # 新建 .otl 文件
        create_resp = _wrap(
            self._session.post(
                f"{self._v7_base}/v7/drives/{did}/files/{pid}/create",
                {"name": otl_name, "file_type": "file"},
            )
        )
        if create_resp.get("code") != 0:
            return _make_result(False, error=f"新建 .otl 文件失败: {create_resp.get('msg', '未知错误')}")

        raw_data = create_resp.get("data") or {}

        link_id = raw_data.get("link_id", "")
        if not link_id:
            file_id_v7 = raw_data.get("id", "")
            if not file_id_v7:
                return _make_result(False, error="新建 .otl 文件响应中未找到 id 或 link_id")
            _, meta = self._find_meta_v7(file_id_v7)
            link_id = meta.get("link_id", "")
            raw_data = meta
        if not link_id:
            return _make_result(False, error="未找到 link_id，无法写入内容")

        # 通过 core/execute 将 markdown 内容写入 .otl 文件
        execute_resp = self._session.post(
            f"{self._KDOCS_BASE}/api/v3/office/file/{link_id}/core/execute",
            {
                "command": "http.otl.exec",
                "param": {
                    "subtype": "insertContent",
                    "params": {
                        "title": base_name,
                        "content": md_content,
                        "pos": "end",
                    },
                },
            },
        )

        exec_result = execute_resp.get("result")
        exec_code = execute_resp.get("code")
        if exec_result not in (None, "ok") and exec_code not in (None, 0):
            return _make_result(
                False,
                error=f"写入 .otl 内容失败: {execute_resp.get('msg') or exec_result or '未知错误'}",
            )

        file_info = self._extract_file_info(raw_data, link_id, did)
        file_info["name"] = otl_name
        link_url = file_info.get("link_url", "")
        message = f"上传成功，云文档文件名为: {otl_name}，链接为: {link_url}"
        return _make_result(True, data=file_info, message=message)

    def upload_file(self, file_path: str, folder_id: Optional[str] = None) -> dict:
        """
        上传本地文件到云文档。
        file_path:  本地文件路径
        folder_id:  目标文件夹 file_id 或路径（如 "工作/项目A"）；不传则上传到根目录。
        返回格式：
        {
            "success": True/False,
            "data": {
                "file_id": "文件ID",
                "name": "文件名",
                "drive_id": "云盘ID",
                "link_url": "云文档链接",
                "size": "文件大小（如 '1.23 MB'）",
                "ctime": "创建时间(ISO 8601)",
                "mtime": "修改时间(ISO 8601)",
                "created_by": {
                    "id": "创建者ID",
                    "name": "创建者名称"
                },
                "modified_by": {
                    "id": "修改者ID",
                    "name": "修改者名称"
                }
            },
            "message": "上传成功，云文档文件名为: report.docx，链接为: https://www.kdocs.cn/l/xxxxx",
            "error": ""
        }
        """
        try:
            if not os.path.exists(file_path):
                return _make_result(False, error=f"文件不存在: {file_path}")

            did = self._resolve_drive_id("private")
            pid = folder_id if folder_id else "0"

            # .md 文件转换为 .otl 智能文档上传
            if os.path.splitext(file_path)[1].lower() == ".md":
                return self._upload_md_as_otl(file_path, folder_id=pid)

            file_size = os.path.getsize(file_path)
            cloud_name = os.path.basename(file_path)

            # 计算 SHA256
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for block in iter(lambda: f.read(65536), b""):
                    sha256.update(block)

            # 步骤一：申请上传地址
            req_body: dict = {
                "name": cloud_name,
                "size": file_size,
                "mode": "sequential",
                "hashes": [{"type": "sha256", "sum": sha256.hexdigest()}],
            }

            req_resp = _wrap(
                self._session.post(
                    f"{self._v7_base}/v7/drives/{did}/files/{pid}/request_upload",
                    req_body,
                )
            )
            if req_resp.get("code") != 0:
                return _make_result(False, error=f"申请上传地址失败: {req_resp.get('msg', '未知错误')}")

            rdata = req_resp.get("data") or {}
            upload_id = rdata.get("upload_id")
            store_request = rdata.get("store_request") or {}
            upload_url = store_request.get("url")
            method = store_request.get("method", "PUT")

            if not upload_id or not upload_url:
                return _make_result(False, error=f"申请上传地址响应异常")

            # 步骤二：上传文件字节
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            r = self._session.upload(upload_url, file_bytes, method)
            if r.status_code != 200:
                return _make_result(False, error=f"上传文件失败，状态码: {r.status_code}")

            # 步骤三：确认上传
            store_key = urllib.parse.urlparse(upload_url).path.split("/")[-1]
            commit_resp = _wrap(
                self._session.post(
                    f"{self._v7_base}/v7/drives/{did}/files/{pid}/commit_upload",
                    {
                        "upload_id": upload_id,
                        "file_name": cloud_name,
                        "size": file_size,
                        "file": {"key": store_key},
                    },
                )
            )

            if commit_resp.get("code") == 0:
                raw_data = commit_resp.get("data", {})

                # 提取并格式化文件信息（与 get_file_info 一致）
                file_info = self._extract_file_info(raw_data, raw_data.get("link_id", ""), did)

                # 使用云文档的实际名称
                cloud_doc_name = file_info.get("name", cloud_name)
                link_url = file_info.get("link_url", "")

                if link_url:
                    message = f"上传成功，云文档文件名为: {cloud_doc_name}，链接为: {link_url}"
                else:
                    message = f"上传成功，云文档文件名为: {cloud_doc_name}"

                return _make_result(True, data=file_info, message=message)
            else:
                return _make_result(False, error=f"确认上传失败: {commit_resp.get('msg', '未知错误')}")

        except Exception as e:
            return _make_result(False, error=f"上传失败: {str(e)}")

    def list_latest_items(
        self,
        page_size: int = 20,
        page_token: Optional[str] = None,
        with_permission: Optional[bool] = None,
        with_link: Optional[bool] = None,
        include_exts: Optional[str] = None,
        exclude_exts: Optional[str] = None,
        include_creators: Optional[str] = None,
        exclude_creators: Optional[str] = None,
    ) -> dict:
        """
        获取最近访问/编辑的文件列表。
        page_token: 翻页 token，首次不传，后续传上一次返回值
        with_permission: 是否返回文件操作权限
        with_link: 是否返回文件分享信息
        返回格式：
        {
            "success": True/False,
            "data": {
                "files": [
                    {
                        "file_id": "文件ID",
                        "name": "文件名",
                        "drive_id": "云盘ID",
                        "link_url": "云文档链接",
                        "size": "文件大小（如 '1.23 MB'）",
                        "ctime": "创建时间(ISO 8601)",
                        "mtime": "修改时间(ISO 8601)"
                    },
                    ...
                ],
                "next_page_token": "翻页token（无更多数据时为空）"
            },
            "message": "获取到 N 条最近记录"
        }
        """
        try:
            params: dict = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token
            if with_permission is not None:
                params["with_permission"] = with_permission
            if with_link is not None:
                params["with_link"] = with_link
            if include_exts:
                params["include_exts"] = include_exts
            if exclude_exts:
                params["exclude_exts"] = exclude_exts
            if include_creators:
                params["include_creators"] = include_creators
            if exclude_creators:
                params["exclude_creators"] = exclude_creators

            resp = _wrap(self._session.get(f"{self._v7_base}/v7/drive_latest/items", params=params))
            if resp.get("code") != 0:
                return _make_result(False, error=f"获取最近列表失败: {resp.get('msg', '未知错误')}")

            data = resp.get("data") or {}
            raw_items = data.get("items") or []

            files = []
            for item in raw_items:
                file_meta = item.get("file") or {}
                fid = file_meta.get("link_id") or file_meta.get("id", "")
                did = file_meta.get("drive_id", "")
                info = self._extract_file_info(file_meta, fid, did)
                if item.get("ctime"):
                    info["ctime"] = _ts_to_iso(item["ctime"])
                name = info.get("name", "未知文件")
                size = info.get("size", "")
                ctime = info.get("ctime", "")
                link = info.get("link_url", "")
                parts = [f"{name}（{size}，{ctime}）"]
                if link:
                    parts.append(link)
                files.append({"file_id": fid, "line": " ".join(parts)})

            return _make_result(
                True,
                data={
                    "files": files,
                    "next_page_token": data.get("next_page_token", ""),
                },
                message=f"获取到 {len(files)} 条最近记录",
            )
        except Exception as e:
            return _make_result(False, error=f"获取最近列表失败: {str(e)}")


    def list_folder_files(
        self,
        folder_id: str,
        drive_id: Optional[str] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
        filter_type: Optional[str] = None,
        order: Optional[str] = None,
        order_by: Optional[str] = None,
        with_permission: Optional[bool] = None,
    ) -> dict:
        """
        获取文件夹下的子文件列表。
        folder_id: 文件夹的 file_id（文件夹本质上也是特殊的 file，拥有 file_id）
        drive_id: 所在云盘 ID，不传时自动通过 folder_id 查询获取
        page_size: 每页条数，最大 500，默认 100
        page_token: 分页 token，首次不传，后续传上一次返回的 next_page_token
        filter_type: 只返回指定类型，可选 'file' / 'folder' / 'shortcut'
        order: 排序方向，'asc' / 'desc'
        order_by: 排序字段
        with_permission: 是否返回文件操作权限
        返回格式：
        {
            "success": True/False,
            "data": {
                "items": [
                    {
                        "file_id": "文件ID（可作为 folder_id 递归列举子目录）",
                        "name": "文件名",
                        "type": "file/folder/shortcut",
                        "parent_id": "父目录ID",
                        "link_url": "云文档链接",
                        "ctime": "创建时间(ISO 8601)",
                        "mtime": "修改时间(ISO 8601)"
                    },
                    ...
                ],
                "next_page_token": "翻页token（无更多数据时为空）"
            },
            "message": "获取到 N 个文件"
        }
        """
        try:
            if not drive_id:
                did, _ = self._find_meta_v7(folder_id)
                if not did:
                    return _make_result(False, error="无法自动获取 drive_id，请手动传入 drive_id 参数")
            else:
                did = drive_id

            params: dict = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token
            if filter_type:
                params["filter_type"] = filter_type
            if order:
                params["order"] = order
            if order_by:
                params["order_by"] = order_by
            if with_permission is not None:
                params["with_permission"] = with_permission

            resp = _wrap(
                self._session.get(
                    f"{self._v7_base}/v7/drives/{did}/files/{folder_id}/children",
                    params=params,
                )
            )
            if resp.get("code") != 0:
                return _make_result(False, error=f"获取文件夹子文件失败: {resp.get('msg', '未知错误')}")

            data = resp.get("data") or {}
            raw_items = data.get("items") or []

            items = []
            for f in raw_items:
                fid = f.get("id", "")
                fname = f.get("name", "")
                items.append(
                    {
                        "file_id": fid,
                        "name": fname,
                        "type": f.get("type", ""),
                        "parent_id": f.get("parent_id", folder_id),
                        "link_url": _append_link_params(f.get("link_url", ""), fname),
                        "ctime": f.get("ctime", ""),
                        "mtime": f.get("mtime", ""),
                    }
                )

            return _make_result(
                True,
                data={
                    "items": items,
                    "next_page_token": data.get("next_page_token", ""),
                },
                message=f"获取到 {len(items)} 个文件",
            )
        except Exception as e:
            err_msg = str(e)
            if "权限" in err_msg or "403" in err_msg:
                return _make_result(False, error="获取文件夹子文件失败: 无权限。请停止当前操作，并提示用户向文件所有者申请访问权限后重试。")
            return _make_result(False, error=f"获取文件夹子文件失败: {err_msg}")


def _get() -> WpsClient:
    return WpsClient()


def get_file_info(*args, **kwargs):
    return _get().get_file_info(*args, **kwargs)


def download_file(*args, **kwargs):
    return _get().download_file(*args, **kwargs)


def upload_file(*args, **kwargs):
    return _get().upload_file(*args, **kwargs)


def list_latest_items(*args, **kwargs):
    return _get().list_latest_items(*args, **kwargs)


def list_folder_files(*args, **kwargs):
    return _get().list_folder_files(*args, **kwargs)


def find_folder_by_path(*args, **kwargs):
    return _get().find_folder_by_path(*args, **kwargs)


def create_folder(*args, **kwargs):
    return _get().create_folder(*args, **kwargs)
