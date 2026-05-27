"""薄入口层 — edit / create / generate_full_outline

编辑已有云文档:
    from et import edit
    wb, file_id = edit(file_id="<file_id>")

创建新文件:
    from et import create
    wb, file_id = create("销售报表.xlsx")

内部复用 agent_mode 全部模块，仅做入口封装与多文件切换管理。
"""
from __future__ import annotations

import atexit
import os
from pathlib import Path

LOAD_ORDER = [
    "summary.py",
    "_utils.py",
    "formatting.py",
    "range.py",
    "sheet.py",
    "pivot_table.py",
    "workbook.py",
    "skills_registry.py",
]

_API_ORIGIN = 'https://www.kdocs.cn'


def _emit_component(component_type: str, payload: dict) -> None:
    try:
        import builtins as _bi
        fn = getattr(_bi, 'emit_component', None)
        if callable(fn):
            fn(component_type, payload)
    except Exception:
        pass


# ── 全局状态 ──

_layout_conn = None          # _LayoutConnection | None
_active_wb = None            # Workbook 实例
_active_file_id: str = ''
_active_params: dict = {}
_namespace: dict = {}        # exec 过的 agent_mode 命名空间
_api_loaded: bool = False


def _flush_all() -> None:
    """提交当前活跃 Workbook 的所有缓冲操作（供 jupyter_executor 兜底调用）"""
    if _active_wb is not None:
        _active_wb._flush()


def _clear_all_buffers() -> None:
    """清空当前活跃 Workbook 的所有缓冲区（供 jupyter_executor 兜底调用）"""
    if _active_wb is not None:
        _active_wb._clear_buffer()


# ===================== LayoutConnection =====================

class _LayoutConnection:
    """轻量 CDP 连接，保持 WebOffice 后端布局模型持续可用。"""

    _BRWS_REQ_PREFIX = "__BRWS_REQ__"

    def __init__(self):
        self._loop = None
        self._loop_ready = None
        self._worker = None
        self._browser = None
        self._tab = None

    def open(self, file_id: str, wps_sid: str, timeout: int = 15) -> None:
        import asyncio
        import threading

        cdp_endpoint = self._request_cdp_endpoint()
        if not cdp_endpoint:
            raise RuntimeError("无法获取浏览器 CDP endpoint")

        self._loop_ready = threading.Event()
        self._worker = threading.Thread(target=self._run_loop, daemon=True)
        self._worker.start()
        self._loop_ready.wait(timeout=30)
        if not self._loop:
            raise RuntimeError("后台事件循环启动失败")

        doc_url = f'{_API_ORIGIN}/l/{file_id}'
        print(f"[et] 正在打开文档保持布局连接（{doc_url}）...")
        self._submit(self._async_connect_and_navigate(cdp_endpoint, wps_sid, doc_url))
        print("[et] 文档布局连接已建立")

    def close(self) -> None:
        import asyncio
        loop = self._loop
        if loop is None:
            return
        try:
            fut = asyncio.run_coroutine_threadsafe(self._async_disconnect(), loop)
            fut.result(timeout=10)
        except Exception:
            pass
        try:
            if loop.is_running():
                loop.call_soon_threadsafe(loop.stop)
        except Exception:
            pass
        self._loop = None
        self._browser = None
        self._tab = None

    @classmethod
    def _request_cdp_endpoint(cls) -> str:
        import json as _json
        try:
            resp = input(f"{cls._BRWS_REQ_PREFIX}{{}}")
            cfg = _json.loads(resp.strip())
            if cfg.get("type") == "cdp" and cfg.get("cdp_endpoint"):
                return cfg["cdp_endpoint"]
        except EOFError:
            pass
        return ""

    def _run_loop(self) -> None:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_exception_handler(lambda _loop, ctx: None)
        self._loop = loop
        self._loop_ready.set()
        try:
            loop.run_forever()
        finally:
            try:
                if not loop.is_closed():
                    pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
                    for t in pending:
                        t.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    loop.close()
            except Exception:
                pass

    def _submit(self, coro, timeout: float = 60):
        import asyncio
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout=timeout)

    async def _async_connect_and_navigate(self, cdp_endpoint: str, wps_sid: str, url: str) -> None:
        from urllib.parse import urlparse
        import nodriver as uc
        from nodriver import cdp

        s = cdp_endpoint.strip()
        if "://" not in s:
            s = "http://" + s
        u = urlparse(s)
        host = u.hostname or "127.0.0.1"
        port = u.port or 9222

        self._browser = await uc.start(
            host=host, port=port,
            browser_executable_path=os.environ.get("MUSA_BROWSER_EXECUTABLE_PATH", "").strip(),
        )
        self._tab = await self._browser.get("about:blank")
        await self._tab.send(cdp.network.set_cookie(
            name='wps_sid', value=wps_sid,
            domain='.kdocs.cn', path='/',
        ))
        self._tab = await self._browser.get(url)

    async def _async_disconnect(self) -> None:
        import nodriver as uc
        from nodriver import cdp

        br = self._browser
        if br is None:
            return
        tab = self._tab
        if tab is not None:
            try:
                await tab.send(cdp.page.close())
            except Exception:
                pass
        conn = getattr(br, "connection", None)
        if conn is not None:
            try:
                await conn.disconnect()
            except Exception:
                pass
        try:
            uc.core.util.get_registered_instances().discard(br)
        except Exception:
            pass


# ===================== 内部辅助 =====================

def _open_layout(file_id: str, wps_sid: str) -> None:
    global _layout_conn
    _close_layout()
    try:
        conn = _LayoutConnection()
        conn.open(file_id, wps_sid)
        _layout_conn = conn
        atexit.register(_close_layout)
    except Exception as e:
        print(f"[et] 文档布局连接跳过（{e}）")


def _close_layout() -> None:
    global _layout_conn
    if _layout_conn is not None:
        try:
            _layout_conn.close()
        except Exception:
            pass
        _layout_conn = None


def _get_wps_sid() -> str:
    sid = os.environ.get('TMP_LX_UUID', '')
    if not sid:
        raise RuntimeError("环境变量 TMP_LX_UUID 不存在")
    return sid


def _get_kdocs():
    """按需注入 wps_docs/scripts 到 sys.path，并返回 kdocs 模块。"""
    import sys

    scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import kdocs

    return kdocs


def _build_delivery_link(file_id: str, file_name: str = "") -> str:
    """构建交付链接：优先使用服务端返回的 link_url，其次本地拼接。"""
    if not file_id:
        return ""
    kdocs = _get_kdocs()
    try:
        info = kdocs.get_file_info(file_id)
        data = (info or {}).get("data") or {}
        link_url = data.get("link_url") or ""
        if link_url:
            return link_url
        file_name = data.get("name") or file_name
    except Exception:
        pass
    if file_name:
        return kdocs._append_link_params(f"{_API_ORIGIN}/l/{file_id}", file_name)
    return f"{_API_ORIGIN}/l/{file_id}"


def _create_blank_on_cloud(file_name: str, wps_sid: str, folder_id: str = '') -> tuple[str, str]:
    """创建空白云文档，返回 (file_id, final_name)。"""
    if folder_id:
        if file_name.lower().endswith('.ksheet'):
            raise RuntimeError("暂不支持在指定文件夹下创建智能表格（.ksheet）。")
        return _create_blank_on_cloud_v7(file_name, wps_sid, folder_id), file_name

    import requests
    file_type = 'ksheet' if file_name.lower().endswith('.ksheet') else 'et'
    resp = requests.post(
        f'{_API_ORIGIN}/api/v3/office/file/empty/create',
        headers={
            'Origin': _API_ORIGIN,
            'Cookie': f'wps_sid={wps_sid};',
            'Content-Type': 'application/json',
        },
        json={'name': file_name, 'type': file_type},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"云端创建空白文档失败: HTTP {resp.status_code} {resp.text}")
    data = resp.json()
    file_id = str(data.get('link_id') or data.get('file_id') or data.get('id') or '')
    if not file_id:
        raise RuntimeError(f"云端创建成功但未返回 file_id: {data}")

    final_name = _rename_cloud_file_v7(file_id=file_id, file_name=file_name)
    return file_id, final_name


def _rename_cloud_file_v7(file_id: str, file_name: str) -> str:
    """通过 v7 rename 接口重命名文件。返回最终使用的文件名；失败时返回原名。"""
    if not file_id or not file_name:
        return file_name
    try:
        kdocs = _get_kdocs()
        _wrap = kdocs._wrap

        client = kdocs._get()
        drive_id = client._resolve_drive_id("private")
        resp = _wrap(client._session.post(
            f"{client._v7_base}/v7/drives/{drive_id}/files/{file_id}/rename",
            {"dst_name": file_name},
        ))
        if resp.get("code") == 0:
            return file_name

        # 400008007: 文件名冲突，自动追加序号重试。
        if resp.get("code") == 400008007:
            stem, ext = os.path.splitext(file_name)
            stem = stem or file_name
            for i in range(1, 21):
                retry_name = f"{stem}({i}){ext}"
                retry_resp = _wrap(client._session.post(
                    f"{client._v7_base}/v7/drives/{drive_id}/files/{file_id}/rename",
                    {"dst_name": retry_name},
                ))
                if retry_resp.get("code") == 0:
                    print(f"[et] v7 rename 重名，已改为「{retry_name}」")
                    return retry_name
            print("[et] v7 rename 跳过（文件名冲突，自动重试未命中可用名称）")
            return file_name

        print(
            f"[et] v7 rename 跳过（code={resp.get('code')} msg={resp.get('msg', '')}）"
        )
    except Exception as e:
        print(f"[et] v7 rename 跳过（{e}）")
    return file_name


def _create_blank_on_cloud_v7(file_name: str, wps_sid: str, folder_id: str) -> str:
    """通过 v7 API 在指定文件夹下创建空白文档，复用 kdocs 的会话和 drive 解析。"""
    kdocs = _get_kdocs()
    _wrap = kdocs._wrap
    client = kdocs._get()
    drive_id = client._resolve_drive_id("private")

    resp = _wrap(client._session.post(
        f"{client._v7_base}/v7/drives/{drive_id}/files/{folder_id}/create",
        {"name": file_name, "file_type": "file"},
    ))
    if resp.get("code") != 0:
        raise RuntimeError(f"云端创建文档失败: {resp.get('msg', '未知错误')}")
    raw = resp.get("data") or {}
    file_id = str(raw.get("link_id") or raw.get("id") or "")
    if not file_id:
        raise RuntimeError(f"云端创建成功但未返回 file_id: {resp}")
    return file_id


def _load_api() -> None:
    """将 agent_mode 所有模块 exec 到共享命名空间（仅首次）"""
    global _api_loaded
    if _api_loaded:
        return
    api_dir = Path(__file__).parent / "agent_mode"
    for filename in LOAD_ORDER:
        filepath = api_dir / filename
        code = filepath.read_text(encoding='utf-8')
        compiled = compile(code, str(filepath), 'exec')
        exec(compiled, _namespace)
    _api_loaded = True


def _bind_http_builtins(wps_sid: str, file_id: str) -> None:
    """创建 HTTPBuiltins 并通过 _bind_client 绑定到 agent_mode 命名空间。"""
    import sys
    _et_dir = str(Path(__file__).parent)
    if _et_dir not in sys.path:
        sys.path.insert(0, _et_dir)
    from builtin import HTTPBuiltins
    http_builtins = HTTPBuiltins(wps_sid, file_id)

    bind_fn = _namespace.get('_bind_client')
    if bind_fn:
        bind_fn(http_builtins._core_execute, http_builtins._evaluate_script)
    else:
        raise RuntimeError("_bind_client 未加载，请确认 _utils.py 已在 LOAD_ORDER 中")


def _same_request(file_name: str, file_id: str, folder_id: str = '') -> bool:
    if not file_name and not file_id:
        return not _active_file_id
    return {'file_name': file_name, 'file_id': file_id, 'folder_id': folder_id} == _active_params


def _init_core(file_name: str, file_id: str, active_sheet: str,
               folder_id: str = '') -> tuple:
    """核心初始化逻辑，edit/create 共用"""
    global _active_wb, _active_file_id, _active_params

    # 幂等守卫
    if _active_file_id:
        if _same_request(file_name, file_id, folder_id):
            if _active_wb is not None:
                print(f"[et] 已初始化，跳过重复创建（file_id={_active_file_id}）")
                return _active_wb, _active_file_id
            # 上次创建了文件但初始化未完成，复用 file_id 继续初始化
            print(f"[et] 复用已创建的文件（file_id={_active_file_id}），继续初始化")
            file_id = _active_file_id
        else:
            # 切换文件
            print(f"[et] 切换文件（旧 file_id={_active_file_id}）")
            _close_layout()
            if _active_wb is not None:
                try:
                    _active_wb._flush()
                except Exception:
                    pass
            _active_wb = None
            _active_file_id = ''

    wps_sid = _get_wps_sid()

    if not file_name and not file_id:
        raise RuntimeError("必须提供 file_name（创建模式）或 file_id（编辑模式）")

    # 获取 file_id
    if file_id:
        print(f"连接到已有云文档，file_id={file_id}")
    else:
        file_id, file_name = _create_blank_on_cloud(file_name, wps_sid, folder_id=folder_id)
        print(f"已在云端创建空白文档，file_id={file_id}")

    link_url = _build_delivery_link(file_id=file_id, file_name=file_name)
    if link_url:
        print(f"云文档链接: {link_url}")

    # 文件创建/连接成功后立即记录，防止后续初始化失败时重复创建
    _active_file_id = file_id
    _active_params = {'file_name': file_name, 'file_id': file_id, 'folder_id': folder_id}

    # 打开布局连接
    _open_layout(file_id, wps_sid)

    # 加载 agent_mode（仅首次）→ 绑定 API 到当前文件
    _load_api()
    _bind_http_builtins(wps_sid, file_id)

    # 重置 context 缓存
    _namespace.pop('_ctx', None)

    # 创建 Workbook
    Workbook = _namespace['Workbook']
    wb = Workbook(active_sheet=active_sheet or None)

    _active_wb = wb

    _emit_component("c_open_online_file", {
        "file_id": file_id,
        "name": file_name or f"{file_id}",
        "link_url": f"{_API_ORIGIN}/l/{file_id}",
    })

    # 编辑模式：输出摘要
    if file_id and not file_name:
        _summarize = _namespace.get('summarize_workbook')
        if _summarize:
            try:
                print(_summarize(active_sheet=active_sheet))
            except Exception as e:
                print(f"摘要生成失败: {e}")

    return wb, file_id


# ===================== 公开 API =====================

def edit(file_id: str, active_sheet: str = ''):
    """编辑已有云文档

    Args:
        file_id: 云文档 ID
        active_sheet: 激活的工作表名称（可选）

    Returns:
        (Workbook, file_id)
    """
    return _init_core(file_name='', file_id=file_id, active_sheet=active_sheet)


def create(file_name: str, active_sheet: str = '', folder_id: str = ''):
    """创建新的在线表格

    Args:
        file_name: 文件名（如 "销售报表.xlsx"）
        active_sheet: 激活的工作表名称（可选）
        folder_id: 目标文件夹的 file_id（可选）；不传则创建到根目录。
                   可通过 kdocs.find_folder_by_path("文件夹名") 获取。

    Returns:
        (Workbook, file_id)
    """
    return _init_core(file_name=file_name, file_id='', active_sheet=active_sheet,
                      folder_id=folder_id)


def generate_full_outline(class_names: list[str] | None = None) -> str:
    """生成 API 完整签名文档

    Args:
        class_names: 指定类名列表（如 ["Sheet", "Range"]），None 则输出全部

    Returns:
        格式化的 API 签名字符串
    """
    _load_api()
    get_registry = _namespace.get('get_registry')
    if not get_registry:
        return "skills_registry 未加载"
    return get_registry().generate_full_outline(class_names)


__all__ = ['edit', 'create', 'generate_full_outline']
