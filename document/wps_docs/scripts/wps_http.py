"""
wps_http.py — WPS 365 公共 HTTP 会话与基础客户端。
供 kdocs、ap、dbsheet 等子技能共享，无需单独实例化。

子技能引入方式（以 ap 为例）：
    import sys, os
    _shared = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
    if _shared not in sys.path:
        sys.path.insert(0, _shared)
    from wps_http import WpsSession, BaseClient
"""

import os
from typing import Optional

import requests


_V7_BASE = "https://api.wps.cn"
_V5_BASE = "https://365.kdocs.cn/3rd/drive"


def _resolve_sid() -> str:
    """从环境变量读取认证 SID，优先级：TMP_LX_UUID > WPS_SID。"""
    for key in ("TMP_LX_UUID", "WPS_SID"):
        val = os.environ.get(key)
        if val:
            return val
    raise ValueError("缺少认证凭证：请设置环境变量 TMP_LX_UUID 或 WPS_SID")


def _resolve_v7_base(override: Optional[str] = None) -> str:
    """解析 v7 API base URL，支持通过参数或 WPS_API_BASE 环境变量覆盖默认值。"""
    return (override or os.environ.get("WPS_API_BASE") or _V7_BASE).rstrip("/")


class WpsSession:
    """
    WPS 365 底层 HTTP 会话，统一管理认证 Cookie 和公共请求头。
    所有出站请求均经此对象发出，业务层无需关心凭证细节。

    参数：
        sid           认证 Cookie 值（wps_sid）
        base_url      若传入，get/post 的路径会自动加上此前缀（用于 path-based 路由）
        csrf          是否同时写入 csrf Cookie（默认 True）
        extra_headers 额外请求头，会覆盖同名的公共头
    """

    _BASE_HEADERS = {
        "Origin": "https://365.kdocs.cn",
        "Referer": "https://365.kdocs.cn/",
    }

    def __init__(
        self,
        sid: str,
        base_url: str = "",
        *,
        csrf: bool = True,
        extra_headers: Optional[dict] = None,
    ):
        self._base = base_url.rstrip("/") if base_url else ""
        self._http = requests.Session()
        self._http.cookies.set("wps_sid", sid)
        if csrf:
            self._http.cookies.set("csrf", sid)
        hdrs = dict(self._BASE_HEADERS)
        if extra_headers:
            hdrs.update(extra_headers)
        self._http.headers.update(hdrs)

    def _parse(self, r: requests.Response) -> dict:
        if not r.content:
            return {}
        try:
            return r.json()
        except Exception:
            return {"code": -1, "msg": "非JSON响应", "text": (r.text or "")[:500]}

    @staticmethod
    def _normalize_params(params: Optional[dict]) -> Optional[dict]:
        """将 bool 值转为小写字符串（requests 默认大写，部分 WPS 接口不认）。"""
        if not params:
            return params
        result = {}
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, bool):
                result[k] = "true" if v else "false"
            elif isinstance(v, list):
                result[k] = [("true" if i is True else "false" if i is False else i) for i in v]
            else:
                result[k] = v
        return result

    def get(self, url_or_path: str, params: Optional[dict] = None) -> dict:
        """GET 请求。设置了 base_url 时 url_or_path 为相对路径，否则为完整 URL。"""
        url = f"{self._base}{url_or_path}" if self._base else url_or_path
        return self._parse(self._http.get(
            url,
            headers={"Content-Type": "application/json"},
            params=self._normalize_params(params),
            timeout=30,
        ))

    def post(self, url_or_path: str, body: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        """JSON POST 请求。"""
        url = f"{self._base}{url_or_path}" if self._base else url_or_path
        return self._parse(self._http.post(
            url,
            headers={"Content-Type": "application/json"},
            json=body,
            params=params,
            timeout=30,
        ))

    def upload(self, url: str, data: bytes, method: str = "PUT") -> requests.Response:
        """上传原始字节到指定 URL（Content-Type: application/octet-stream）。"""
        return self._http.request(
            method.upper(),
            url,
            headers={"Content-Type": "application/octet-stream"},
            data=data,
            timeout=120,
        )

    def download(self, url: str) -> requests.Response:
        """从指定 URL 下载文件字节流。"""
        return self._http.get(url, timeout=120)


class BaseClient:
    """
    WPS 365 客户端基类。
    统一处理认证凭证读取、v7 base URL 解析和 WpsSession 初始化。
    子类通过 super().__init__() 完成通用设置，再按需扩展业务方法。

    初始化后可用属性：
        self._sid  认证 SID 字符串
        self._v7   v7 API base URL（已去除尾部 /）
        self._s    WpsSession 实例

    参数：
        base_url      覆盖 v7 base URL（默认读 WPS_API_BASE 环境变量或 api.wps.cn）
        session_base  传给 WpsSession 的 base_url（用于 path-based 路由，如 dbsheet）
        csrf          是否注入 csrf Cookie（默认 True）
        extra_headers 传给 WpsSession 的额外请求头
    """

    _V7_BASE = _V7_BASE
    _V5_BASE = _V5_BASE

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        session_base: str = "",
        csrf: bool = True,
        extra_headers: Optional[dict] = None,
    ):
        self._sid = _resolve_sid()
        self._v7 = _resolve_v7_base(base_url)
        self._s = WpsSession(self._sid, session_base, csrf=csrf, extra_headers=extra_headers)
