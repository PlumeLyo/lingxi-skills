from __future__ import annotations

"""
PPT HTML 工具（同步调用）
────────────────────────
依赖：
    pip install nodriver html5lib

浏览器复用 browser.py 的 CDP 接入方式：通过 `_request_browser()` 向前端发起 `__BRWS_REQ__`
请求获取 `cdp_endpoint`，再用 nodriver 连接到同一个 Chromium。生成期间会在该浏览器中
临时新建一个标签页，结束后立刻关闭，避免污染用户的浏览会话。

检测顺序（check_slides_layout）：UTF-8 → 是否混入非 HTML 正文 → html5lib 标签结构 → 浏览器（脚本 / DOM）→ 跑版。

对外接口：
    html_slide_to_pptx(html_files, output_path)  — HTML 幻灯片列表 → .pptx
    screenshot_slides(html_files)               — HTML 幻灯片截图为 PNG 预览图
    check_slides_layout(html_paths)             — 批量跑版检测（单浏览器会话）
    check_slide_layout(html_path)               — 单页检测
    apply_safe_layout_css(...)                  — 可选：注入防滚动/固定画布 CSS

nodriver 在专用后台线程中以独立 asyncio 事件循环运行（与 browser.py 同样的线程隔离模型），
可安全地在 Jupyter / asyncio 环境中以同步 API 调用。
"""

import asyncio
import base64
import functools
import http.server
import json
import os
import re
import shutil
import socket
import sys
import threading
import time
from io import StringIO
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import quote, unquote, urlparse

# <img src="..."> / src='...' / src=unquoted：用于将本地路径改写为 http://127.0.0.1:{port}/... 供 bridge 页加载
_RE_IMG_SRC = re.compile(
    r'(<img\b[^>]*\bsrc\s*=\s*)(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))',
    re.IGNORECASE | re.DOTALL,
)

# CSS 必须用 \burl，避免匹配 myurl(、fetchUrl( 等标识符后缀，造成海量误匹配与极慢/卡死
_RE_CSS_URL_QUOTED = re.compile(
    r"(\burl\s*\(\s*)(['\"])([^'\"]*)\2\s*\)",
    re.IGNORECASE,
)
# 无引号 url(...)；在「带引号 url」替换之后执行；跳过仍以引号开头的 inner
_RE_CSS_URL_UNQUOTED = re.compile(
    r"(\burl\s*\(\s*)([^)]*)(\))",
    re.IGNORECASE,
)

# 正文若含 http://127.0.0.1:port/... 路径资源，需额外挂载目录以便重写
_RE_LOOPBACK_HTTP_IN_HTML = re.compile(
    r"https?://(?:127\.0\.0\.1|localhost)(?::\d+)?/.",
    re.IGNORECASE,
)

# pptx_bridge.html 与 index.js 和本脚本在同一目录（skills/pptx/scripts/）下
_SERVE_DIR = Path(__file__).parent


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(str(raw).strip(), 10)
    except ValueError:
        return default


def _pptx_diag_enabled() -> bool:
    return os.environ.get("LX_PPTX_DIAG", "").strip().lower() in ("1", "true", "yes", "on")


def _pptx_diag_line(msg: str) -> None:
    if _pptx_diag_enabled():
        print(f"[LX_PPTX_DIAG] {msg}", file=sys.stderr)


def _pptx_render_wh() -> tuple[int, int]:
    """htmlArrayToPptxBlob 的 width/height；可用环境变量缩小以加速（幻灯片英寸不变）。"""
    scale_s = os.environ.get("LX_PPTX_VIEWPORT_SCALE", "").strip()
    if scale_s:
        try:
            sc = float(scale_s)
            if 0.2 <= sc <= 1.5:
                return max(320, int(round(1280 * sc))), max(180, int(round(720 * sc)))
        except ValueError:
            pass
    w = _env_int("LX_PPTX_VIEWPORT_W", 1280)
    h = _env_int("LX_PPTX_VIEWPORT_H", 720)
    return max(320, min(3840, w)), max(180, min(2160, h))


# html_slide_to_pptx 超时：主线程 wait 含浏览器冷启动 + HTML 重写 + 整段 evaluate；须 > 单次 evaluate 上限。
_PPTX_PLAYWRIGHT_DEFAULT_TIMEOUT_MS = _env_int("LX_PPTX_PLAYWRIGHT_TIMEOUT_MS", 240_000)  # evaluate 默认 4 分钟
_HTML_SLIDE_TO_PPTX_WAIT_S = _env_int("LX_PPTX_TOTAL_TIMEOUT_S", 300)  # 整次默认 5 分钟（含 ~1 分钟冷启动余量）

# 无界面转换：减轻冷启动与非必要后台任务（安全范围内）
_PPTX_CHROMIUM_ARGS: tuple[str, ...] = (
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-backgrounding-occluded-windows",
    "--mute-audio",
    "--no-first-run",
)


# ── CDP 入口：与 browser.py 共用同一套通信协议 ─────────────────────────────

_BRWS_REQ_PREFIX = "__BRWS_REQ__"


def _request_browser() -> str:
    """通过 input("__BRWS_REQ__{}") 让 JupyterExecutor 转发到前端，拿回 cdp_endpoint。"""
    try:
        response = input(f"{_BRWS_REQ_PREFIX}{{}}")
        cfg = json.loads(response.strip())
        if cfg.get("type") == "cdp" and cfg.get("cdp_endpoint"):
            return cfg.get("cdp_endpoint")
        return ""
    except EOFError:
        return ""


def _parse_cdp_endpoint(raw: str) -> tuple[str, int]:
    """解析形如 http://127.0.0.1:9222 的 endpoint → (host, port)。"""
    s = raw.strip()
    if not s:
        raise RuntimeError("CDP endpoint 为空")
    if "://" not in s:
        s = "http://" + s
    u = urlparse(s)
    host = u.hostname
    if not host:
        raise RuntimeError(f"CDP endpoint 无法解析主机名: {raw!r}")
    port = u.port if u.port is not None else 9222
    return host, port


def _ensure_cdp_endpoint() -> str:
    cdp_endpoint = _request_browser()
    if not cdp_endpoint:
        raise RuntimeError("浏览器启动失败：未拿到 CDP endpoint")
    return cdp_endpoint


# ── 后台线程 + 临时事件循环 ─────────────────────────────────────────────

def _run_async(coro_factory: Callable[[], Awaitable[Any]]) -> Any:
    """在专用线程中创建一次性 asyncio loop，运行 coroutine 并返回结果。

    与 browser.py 不同的是这里每次调用都建一个全新 loop，使用后立即关闭——
    pptx 工具是 one-shot 调用，不需要长生命周期。
    """
    result_box: dict[str, Any] = {"done": threading.Event()}

    def _worker() -> None:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_box["result"] = loop.run_until_complete(coro_factory())
        except Exception as exc:
            result_box["error"] = exc
        finally:
            try:
                pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
                for t in pending:
                    t.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            try:
                loop.close()
            except Exception:
                pass
            result_box["done"].set()

    threading.Thread(target=_worker, daemon=True).start()
    result_box["done"].wait()
    if "error" in result_box:
        raise result_box["error"]
    return result_box["result"]


# ── nodriver 通用辅助 ─────────────────────────────────────────────────

_PAGE_DCL_PROMISE_JS = (
    "(() => {"
    "  if (document.readyState === 'interactive' || document.readyState === 'complete') "
    "return Promise.resolve(null);"
    "  return new Promise((resolve) => {"
    "    document.addEventListener('DOMContentLoaded', () => resolve(null), { once: true });"
    "  });"
    "})()"
)

_PAGE_LOAD_PROMISE_JS = (
    "(() => {"
    "  if (document.readyState === 'complete') return Promise.resolve(null);"
    "  return new Promise((resolve) => {"
    "    window.addEventListener('load', () => resolve(null), { once: true });"
    "  });"
    "})()"
)


def _eval_error_payload(result: Any) -> str | None:
    if result is None:
        return None
    try:
        from nodriver.cdp.runtime import ExceptionDetails
    except ImportError:
        ExceptionDetails = ()  # type: ignore[misc, assignment]
    if ExceptionDetails and isinstance(result, ExceptionDetails):
        return str(result)
    return None


async def _tab_eval(tab: Any, expr: str, *, await_promise: bool = False) -> Any:
    r = await tab.evaluate(expr, await_promise=await_promise, return_by_value=True)
    err = _eval_error_payload(r)
    if err:
        raise RuntimeError(err)
    return r


async def _wait_dcl(tab: Any, timeout: float) -> None:
    async def _run() -> None:
        await _tab_eval(tab, _PAGE_DCL_PROMISE_JS, await_promise=True)
    await asyncio.wait_for(_run(), timeout=timeout)


async def _wait_load(tab: Any, timeout: float) -> None:
    async def _run() -> None:
        await _tab_eval(tab, _PAGE_LOAD_PROMISE_JS, await_promise=True)
    await asyncio.wait_for(_run(), timeout=timeout)


async def _connect_browser(cdp_endpoint: str):
    """连接到既有 CDP 浏览器（不会启动新进程）。"""
    import nodriver as uc  # 延迟导入，避免静态检测/未启用 skill 时的 import 开销

    host, port = _parse_cdp_endpoint(cdp_endpoint)
    # 同时传入 host + port → nodriver 仅连接已有 CDP；browser_executable_path 仅占位以避免误启动 Chromium
    browser = await uc.start(host=host, port=port, browser_executable_path=os.path.abspath(__file__))
    return browser


async def _open_new_tab(browser: Any, url: str = "about:blank") -> Any:
    """在 ``browser`` 内创建一个新 page tab 并返回 nodriver Tab 对象。

    必须绕开 nodriver ``Browser.get(url, new_tab=True)``：它内部强制传
    ``enable_begin_frame_control=True``，而该字段按 CDP 文档：
    *headless shell only, not supported on MacOS yet*。在 macOS + chromium headless
    组合下，chromium 端会直接以 ``-32000 Failed to open new tab - no browser is open``
    拒绝该 ``Target.createTarget`` 调用——与 BrowserContext 是否存在无关，纯粹是
    macOS headless 不识别这个字段。

    这里直接发 ``cdp.target.create_target(url)``（不带 enable_begin_frame_control），
    再轮询 ``update_targets`` 反查回 nodriver ``Tab`` 对象。
    """
    from nodriver import cdp

    conn = getattr(browser, "connection", None)
    if conn is None or conn.closed:
        raise RuntimeError("CDP 连接不可用，无法新建 tab")

    target_id = await conn.send(cdp.target.create_target(url))

    for _ in range(50):
        try:
            await browser.update_targets()
        except Exception:
            pass
        for t in browser.tabs:
            if getattr(t, "target_id", None) == target_id:
                t._browser = browser
                return t
        await asyncio.sleep(0.1)

    raise RuntimeError(
        f"已创建 target_id={target_id}，但 update_targets 未在 page tab 中发现它"
    )


async def _disconnect_browser(browser: Any) -> None:
    if browser is None:
        return
    try:
        import nodriver as uc
    except Exception:
        uc = None  # type: ignore[assignment]
    try:
        conn = getattr(browser, "connection", None)
        if conn is not None and not conn.closed:
            await conn.disconnect()
    except Exception:
        pass
    if uc is not None:
        try:
            uc.core.util.get_registered_instances().discard(browser)
        except Exception:
            pass


async def _close_tab(tab: Any) -> None:
    if tab is None:
        return
    try:
        from nodriver import cdp
        await tab.send(cdp.page.close())
    except Exception:
        pass
    try:
        await tab.disconnect()
    except Exception:
        pass


def _format_runtime_exception(evt: Any) -> str:
    try:
        ed = getattr(evt, "exception_details", None) or evt
        text = getattr(ed, "text", "") or ""
        exc_obj = getattr(ed, "exception", None)
        desc = ""
        if exc_obj is not None:
            desc = getattr(exc_obj, "description", "") or ""
            if not desc:
                val = getattr(exc_obj, "value", None)
                if val is not None:
                    desc = str(val)
        if text and desc:
            return f"{text}: {desc}"
        return desc or text or str(evt)
    except Exception:
        return str(evt)


# ── PPTX 导出：本地静态服务 + bridge ──────────────────────────────────────────


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _file_url_to_path(url: str) -> Path | None:
    """将 file: URL 转为本地 Path；无法解析时返回 None。"""
    u = url.strip()
    if not u.lower().startswith("file:"):
        return None
    parsed = urlparse(u)
    path = unquote(parsed.path or "")
    if sys.platform == "win32":
        # file:///C:/Users/... → /C:/Users/...
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
    return Path(path) if path else None


def _parse_img_src_to_local_path(src: str, base: Path) -> Path | None:
    """将 img 的 src 解析为本地文件路径（http(s)/data/blob/# 返回 None，保持原样由调用方跳过）。"""
    s = src.strip()
    if not s or s.startswith(("#", "data:", "blob:")):
        return None
    if s.startswith(("http://", "https://")):
        return None
    if s.startswith("//"):
        return None
    low = s.lower()
    if low.startswith("file:"):
        p = _file_url_to_path(s)
        return p
    pth = Path(s)
    if pth.is_absolute():
        return pth
    return base / s


def _loopback_http_url_to_local_path(url: str, base: Path) -> Path | None:
    """解析 ``http(s)://127.0.0.1:port/xxx/y.png``（localhost、任意端口）为本地文件。

    路径相对哪一层文档根不确定时，依次尝试 ``base``、``base.parent``、``base.parent.parent``。
    """
    s = url.strip()
    if not s.startswith(("http://", "https://")):
        return None
    try:
        u = urlparse(s)
    except Exception:
        return None
    if (u.hostname or "").lower() not in ("127.0.0.1", "localhost"):
        return None
    raw = unquote((u.path or "").lstrip("/"))
    if not raw:
        return None
    parts = [p for p in raw.split("/") if p and p != "."]
    if ".." in parts:
        return None
    if not parts:
        return None
    rel = Path(*parts)
    for root in (base, base.parent, base.parent.parent):
        try:
            cand = (root / rel).resolve()
        except OSError:
            continue
        try:
            if cand.is_file():
                return cand
        except OSError:
            continue
    return None


def _resolve_local_asset_path(src: str, base: Path) -> Path | None:
    """img/css 资源解析为本地 Path：先处理本机 loopback HTTP URL，再走相对/绝对/file。"""
    s = src.strip()
    if s.startswith(("http://", "https://")):
        return _loopback_http_url_to_local_path(s, base)
    return _parse_img_src_to_local_path(src, base)


def _scan_loopback_http_mount_roots(html_files: list[str], html_slides: list[str]) -> set[str]:
    """正文含 loopback URL 且带路径时，额外挂载 ``base.parent``、``base.parent.parent``。"""
    out: set[str] = set()
    for i, html in enumerate(html_slides):
        if not _RE_LOOPBACK_HTTP_IN_HTML.search(html):
            continue
        b = Path(html_files[i]).resolve().parent
        for root in (b.parent, b.parent.parent):
            try:
                out.add(str(root.resolve()))
            except OSError:
                continue
    return out


def _extra_dirs_to_resolved_mounts(extra_dirs: dict[str, str]) -> list[tuple[str, Path]]:
    """将 extra_dirs 转为已 resolve 的挂载列表，按根路径长度降序（优先最长前缀匹配）。"""
    out: list[tuple[str, Path]] = []
    for prefix, root in extra_dirs.items():
        try:
            out.append((prefix, Path(root).resolve()))
        except OSError:
            continue
    out.sort(key=lambda x: len(str(x[1])), reverse=True)
    return out


def _local_file_to_served_url(
    local_file: Path,
    port: int,
    extra_dirs: dict[str, str],
    *,
    _mounts: list[tuple[str, Path]] | None = None,
) -> str | None:
    """在 extra_dirs 挂载中查找包含该文件的最长根路径，返回可经本地 HTTP 访问的 URL。"""
    try:
        f = local_file.resolve()
    except OSError:
        return None
    mounts = _mounts if _mounts is not None else _extra_dirs_to_resolved_mounts(extra_dirs)
    best: tuple[int, str, str] | None = None
    for prefix, root_p in mounts:
        try:
            rel = f.relative_to(root_p)
        except (OSError, ValueError):
            continue
        rp = rel.as_posix()
        score = len(str(root_p))
        if best is None or score > best[0]:
            best = (score, prefix, rp)
    if best is None:
        return None
    _, prefix, rp = best
    quoted = "/".join(quote(part) for part in rp.split("/") if part != "")
    return f"http://127.0.0.1:{port}{prefix}/{quoted}"


def _plain_path_src_parent_for_mount(src: str) -> str | None:
    """从 img/css 的裸绝对磁盘路径（无 file:、非 http）解析出父目录，用于 extra_dirs 挂载。

    Windows：识别 ``C:/...``、``C:\\...``、UNC ``\\\\server\\...``；不把 ``/images/...`` 这类
    当作磁盘路径（避免与站点根路径混淆）。POSIX：仅当路径在磁盘上存在时才挂载，避免误挂 ``/img/x``。
    """
    s = src.strip()
    if not s or s[0] in "#'\"":
        return None
    low = s.lower()
    if low.startswith(("http://", "https://", "//", "data:", "blob:", "file:", "#")):
        return None
    if sys.platform == "win32":
        if len(s) >= 3 and s[1] == ":" and s[0].isalpha() and s[2] in "/\\":
            p = Path(s)
            try:
                return str(p.resolve().parent)
            except OSError:
                return str(p.parent)
        if s.startswith("\\\\"):
            p = Path(s)
            try:
                return str(p.resolve().parent)
            except OSError:
                return str(p.parent)
        return None
    p = Path(s)
    if not p.is_absolute() or s.startswith("//"):
        return None
    try:
        if p.exists():
            return str(p.resolve().parent)
    except OSError:
        pass
    return None


def _scan_img_plain_absolute_parent_dirs(html_slides: list[str]) -> set[str]:
    """扫描 img 中裸绝对路径（如 ``C:/Users/.../a.png``），收集父目录以加入 HTTP 挂载。"""
    out: set[str] = set()
    for html in html_slides:
        for m in _RE_IMG_SRC.finditer(html):
            src = (m.group(2) or m.group(3) or m.group(4) or "").strip()
            par = _plain_path_src_parent_for_mount(src)
            if par:
                out.add(par)
    return out


def _scan_img_file_url_parent_dirs(html_slides: list[str]) -> set[str]:
    """扫描 HTML 中 img file: 引用，收集需挂载的父目录（绝对路径字符串）。"""
    out: set[str] = set()
    for html in html_slides:
        for m in _RE_IMG_SRC.finditer(html):
            src = (m.group(2) or m.group(3) or m.group(4) or "").strip()
            if not src.lower().startswith("file:"):
                continue
            p = _file_url_to_path(src)
            if p is None:
                continue
            try:
                out.add(str(p.resolve().parent))
            except OSError:
                continue
    return out


def _rewrite_html_img_srcs_for_http(
    html: str,
    base: Path,
    port: int,
    extra_dirs: dict[str, str],
    *,
    _mounts: list[tuple[str, Path]] | None = None,
) -> str:
    """把 img 中的本地绝对/相对/file 路径改为当前 HTTP 服务可访问的 URL。"""
    mounts = _mounts if _mounts is not None else _extra_dirs_to_resolved_mounts(extra_dirs)

    def repl(m: re.Match) -> str:
        pre = m.group(1)
        if m.group(2) is not None:
            src, q = m.group(2), '"'
        elif m.group(3) is not None:
            src, q = m.group(3), "'"
        else:
            src, q = m.group(4), '"'
        local = _resolve_local_asset_path(src.strip(), base)
        if local is None:
            return m.group(0)
        url = _local_file_to_served_url(local, port, extra_dirs, _mounts=mounts)
        if url is None:
            return m.group(0)
        return f"{pre}{q}{url}{q}"

    return _RE_IMG_SRC.sub(repl, html)


def _scan_css_plain_absolute_parent_dirs(html_slides: list[str]) -> set[str]:
    """扫描 CSS url(...) 中的裸绝对路径，收集父目录。"""
    out: set[str] = set()
    for html in html_slides:
        for m in _RE_CSS_URL_QUOTED.finditer(html):
            inner = m.group(3).strip()
            par = _plain_path_src_parent_for_mount(inner)
            if par:
                out.add(par)
        for m in _RE_CSS_URL_UNQUOTED.finditer(html):
            inner = m.group(2).strip()
            if not inner or inner[0] in {'"', "'"}:
                continue
            par = _plain_path_src_parent_for_mount(inner)
            if par:
                out.add(par)
    return out


def _scan_css_file_url_parent_dirs(html_slides: list[str]) -> set[str]:
    """扫描 style 等中的 CSS url(...)，收集 file: 引用所在父目录。"""
    out: set[str] = set()
    for html in html_slides:
        for m in _RE_CSS_URL_QUOTED.finditer(html):
            inner = m.group(3).strip()
            if not inner.lower().startswith("file:"):
                continue
            p = _file_url_to_path(inner)
            if p is None:
                continue
            try:
                out.add(str(p.resolve().parent))
            except OSError:
                continue
        for m in _RE_CSS_URL_UNQUOTED.finditer(html):
            inner = m.group(2).strip()
            if not inner or inner[0] in {'"', "'"}:
                continue
            if not inner.lower().startswith("file:"):
                continue
            p = _file_url_to_path(inner)
            if p is None:
                continue
            try:
                out.add(str(p.resolve().parent))
            except OSError:
                continue
    return out


def _rewrite_css_urls_for_http(
    html: str,
    base: Path,
    port: int,
    extra_dirs: dict[str, str],
    *,
    _mounts: list[tuple[str, Path]] | None = None,
) -> str:
    """把 CSS url() 中的本地路径改为 http://127.0.0.1:{port}/...（与 img 相同解析规则）。"""
    mounts = _mounts if _mounts is not None else _extra_dirs_to_resolved_mounts(extra_dirs)

    def repl_quoted(m: re.Match) -> str:
        pre, q, inner = m.group(1), m.group(2), m.group(3)
        local = _resolve_local_asset_path(inner.strip(), base)
        if local is None:
            return m.group(0)
        url = _local_file_to_served_url(local, port, extra_dirs, _mounts=mounts)
        if url is None:
            return m.group(0)
        return f"{pre}{q}{url}{q})"

    html = _RE_CSS_URL_QUOTED.sub(repl_quoted, html)

    def repl_unquoted(m: re.Match) -> str:
        pre, raw, tail = m.group(1), m.group(2), m.group(3)
        inner = raw.strip()
        if not inner or inner[0] in {'"', "'"}:
            return m.group(0)
        local = _resolve_local_asset_path(inner, base)
        if local is None:
            return m.group(0)
        url = _local_file_to_served_url(local, port, extra_dirs, _mounts=mounts)
        if url is None:
            return m.group(0)
        return f'{pre}"{url}"{tail}'

    return _RE_CSS_URL_UNQUOTED.sub(repl_unquoted, html)


def _rewrite_html_local_assets_for_http(
    html: str,
    base: Path,
    port: int,
    extra_dirs: dict[str, str],
    *,
    _mounts: list[tuple[str, Path]] | None = None,
) -> str:
    """依次重写 <img src> 与 CSS url(...) 中的本地资源引用。

    同一批幻灯片应对 extra_dirs 只调用一次 _extra_dirs_to_resolved_mounts，经 _mounts 传入，
    避免每页重复排序与 resolve（页数多时会线性放大耗时）。
    """
    mounts = _mounts if _mounts is not None else _extra_dirs_to_resolved_mounts(extra_dirs)
    h = _rewrite_html_img_srcs_for_http(html, base, port, extra_dirs, _mounts=mounts)
    return _rewrite_css_urls_for_http(h, base, port, extra_dirs, _mounts=mounts)


def _start_file_server(directory: str, port: int, extra_dirs: dict | None = None) -> http.server.HTTPServer:
    """在后台线程中启动静态文件服务器，返回 server 对象（可调用 shutdown()）。

    Args:
        directory: 主服务目录（scripts 目录）
        port: 端口
        extra_dirs: 额外路径映射，如 {"/images": "/path/to/images"}、
                    {"/__pptx_src/0000": "/path/to/html_dir"}，
                    用于服务 slides 中引用的外部资源。匹配时**最长前缀优先**，避免前缀互相包含时误路由。
    """

    class _SilentHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args): pass

        def translate_path(self, path):
            # 先检查 extra_dirs 映射（最长前缀优先）
            if extra_dirs:
                from urllib.parse import unquote

                clean = unquote(path)
                for prefix, real_dir in sorted(
                    extra_dirs.items(), key=lambda kv: len(kv[0]), reverse=True
                ):
                    if clean.startswith(prefix + "/") or clean == prefix:
                        rest = clean[len(prefix):]
                        return os.path.join(real_dir, rest.lstrip("/"))
            # 回退到默认行为
            return super().translate_path(path)

    handler = functools.partial(_SilentHandler, directory=directory)
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _pptx_extra_dirs(html_files: list[str], html_slides: list[str]) -> dict[str, str]:
    """为 html_slide_to_pptx 构建 extra_dirs：各 HTML 所在目录、file: 与裸绝对路径引用所在目录等。"""
    # set 按路径字符串去重：多页 HTML 在同一目录时只会有一条挂载
    dirs: set[str] = {str(Path(f).resolve().parent) for f in html_files}
    dirs |= _scan_img_file_url_parent_dirs(html_slides)
    dirs |= _scan_css_file_url_parent_dirs(html_slides)
    dirs |= _scan_img_plain_absolute_parent_dirs(html_slides)
    dirs |= _scan_css_plain_absolute_parent_dirs(html_slides)
    dirs |= _scan_loopback_http_mount_roots(html_files, html_slides)

    parents_sorted = sorted(dirs, key=str)
    extra: dict[str, str] = {}
    for i, d in enumerate(parents_sorted):
        extra[f"/__pptx_src/{i:04d}"] = d

    return extra


def _to_js_template_literal(s: str) -> str:
    return "`" + s.replace("\\", "\\\\").replace("`", "\\`") + "`"


async def _async_html_to_pptx(
    cdp_endpoint: str,
    html_slides: list[str],
    port: int,
    rw: int,
    rh: int,
) -> str:
    browser = await _connect_browser(cdp_endpoint)
    tab = None
    try:
        url = f"http://127.0.0.1:{port}/pptx_bridge.html"
        tab = await _open_new_tab(browser, url)
        await _wait_dcl(tab, timeout=15.0)

        ready = False
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            r = await _tab_eval(tab, "window.__pptxReady__ === true")
            if r is True:
                ready = True
                break
            await asyncio.sleep(0.2)
        if not ready:
            raise RuntimeError("JS 库初始化超时（pptx bridge 未就绪）")

        js_array = "[" + ",".join(_to_js_template_literal(s) for s in html_slides) + "]"
        b64 = await _tab_eval(
            tab,
            f"""
(async () => {{
    const {{ htmlArrayToPptxBlob }} = window.__pptxLib__;
    const blob = await htmlArrayToPptxBlob({js_array}, {{
        width:       {rw},
        height:      {rh},
        slideWidth:  13.33,
        slideHeight: 7.5
    }});
    return new Promise((resolve, reject) => {{
        const reader = new FileReader();
        reader.onload  = () => resolve(reader.result.split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    }});
}})()
""",
            await_promise=True,
        )
        if not isinstance(b64, str):
            raise RuntimeError(f"htmlArrayToPptxBlob 返回值类型异常: {type(b64).__name__}")
        return b64
    finally:
        await _close_tab(tab)
        await _disconnect_browser(browser)


def html_slide_to_pptx(html_files: list[str], output_path: str) -> str:
    """
    将一组 HTML 幻灯片文件同步转换为 PPTX 文件。

    注入 bridge 前，会将每页 HTML 内 **``<img src>``** 与 **CSS ``url(...)``**（如
    ``background-image``）中的本地资源（相对路径、绝对磁盘路径、``file://``、可解析的本机
    loopback ``http`` 等）改写为当次转换在 ``127.0.0.1`` 静态服务下可访问的 ``http`` URL，
    避免在 ``pptx_bridge`` 的 iframe 中出现 404。

    **浏览器**：使用 **nodriver** 通过 CDP 连接沙箱提供的既有 Chromium（``_ensure_cdp_endpoint()``），
    不在此模块内启动 Playwright / 额外浏览器进程。

    **诊断**：设置 ``LX_PPTX_DIAG=1`` 时向 stderr 输出分段耗时。可用 ``LX_PPTX_VIEWPORT_SCALE``
    或 ``LX_PPTX_VIEWPORT_W`` / ``LX_PPTX_VIEWPORT_H`` 降低渲染像素以换速度。

    可在 Jupyter / asyncio 环境中安全调用，无需对当前协程 await。

    参数：
        html_files  - HTML 文件路径列表（每个文件对应一张幻灯片，顺序即幻灯片顺序）
        output_path - 输出 .pptx 文件路径（父目录不存在时自动创建）

    返回：
        转换结果文本，格式为：「pptx 已转换成功，保存路径为 <绝对路径>（X KB）」

    示例：
        from generate_pptx import html_slide_to_pptx
        print(html_slide_to_pptx(
            ["slide_01.html", "slide_02.html", "slide_03.html"],
            "output/presentation.pptx"
        ))
    """
    html_slides = [Path(f).read_text(encoding="utf-8") for f in html_files]
    extra = _pptx_extra_dirs(html_files, html_slides)
    port = _find_free_port()
    server = _start_file_server(str(_SERVE_DIR), port, extra_dirs=extra)

    rw, rh = _pptx_render_wh()
    _pptx_diag_line(f"render {rw}x{rh}  pages={len(html_slides)}")

    t0 = time.perf_counter()
    slide_bases = [Path(f).resolve().parent for f in html_files]
    resolved_mounts = _extra_dirs_to_resolved_mounts(extra)
    rewritten = [
        _rewrite_html_local_assets_for_http(
            html_slides[i],
            slide_bases[i],
            port,
            extra,
            _mounts=resolved_mounts,
        )
        for i in range(len(html_slides))
    ]
    _pptx_diag_line(f"rewrite_html+css: {time.perf_counter() - t0:.3f}s")

    cdp_endpoint = _ensure_cdp_endpoint()
    pptx_async_box: dict[str, Any] = {}
    pptx_done = threading.Event()

    def _pptx_browser_worker() -> None:
        try:
            t1 = time.perf_counter()
            pptx_async_box["b64"] = _run_async(
                lambda: _async_html_to_pptx(cdp_endpoint, rewritten, port, rw, rh)
            )
            _pptx_diag_line(
                f"cdp+htmlArrayToPptxBlob: {time.perf_counter() - t1:.3f}s"
            )
        except Exception as exc:
            pptx_async_box["error"] = exc
        finally:
            pptx_done.set()

    threading.Thread(target=_pptx_browser_worker, daemon=True).start()
    try:
        if not pptx_done.wait(timeout=_HTML_SLIDE_TO_PPTX_WAIT_S):
            raise RuntimeError(
                f"html_slide_to_pptx 总等待超时（{_HTML_SLIDE_TO_PPTX_WAIT_S}s，LX_PPTX_TOTAL_TIMEOUT_S 可调）："
                "耗时主要在浏览器内 htmlArrayToPptxBlob（多页/大图/慢 https）；可拆分页数或调大超时。"
            )
        if "error" in pptx_async_box:
            raise pptx_async_box["error"]
        pptx_bytes = base64.b64decode(pptx_async_box["b64"])
    finally:
        try:
            server.shutdown()
        except Exception:
            pass

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pptx_bytes)
    return f"pptx 已转换成功，保存路径为 {out.resolve()}（{len(pptx_bytes) / 1024:.1f} KB）"


# ── 风格预览：HTML 截图为 PNG ─────────────────────────────────────────────────


async def _async_screenshot_slides(cdp_endpoint: str, paths: list[Path]) -> list[str]:
    from nodriver import cdp

    browser = await _connect_browser(cdp_endpoint)
    tab = None
    try:
        tab = await _open_new_tab(browser, "about:blank")
        await tab.send(
            cdp.emulation.set_device_metrics_override(
                width=_EXPECTED_W,
                height=_EXPECTED_H,
                device_scale_factor=1,
                mobile=False,
            )
        )
        clip = cdp.page.Viewport(x=0, y=0, width=_EXPECTED_W, height=_EXPECTED_H, scale=1)
        output_paths: list[str] = []
        for html_path in paths:
            await tab.get(html_path.as_uri())
            try:
                await _wait_load(tab, timeout=15.0)
            except asyncio.TimeoutError:
                # 加载超时（缺少资源等）也尽量截一张，行为与 networkidle 超时一致
                pass
            png_path = html_path.with_suffix(".png")
            b64 = await tab.send(
                cdp.page.capture_screenshot(
                    format_="png",
                    clip=clip,
                    capture_beyond_viewport=False,
                )
            )
            png_path.write_bytes(base64.b64decode(b64))
            output_paths.append(str(png_path.resolve()))
        return output_paths
    finally:
        await _close_tab(tab)
        await _disconnect_browser(browser)


def screenshot_slides(html_files: list[str]) -> dict[str, Any]:
    """
    将一组 HTML 幻灯片截图为 PNG 图片。

    nodriver 在专用后台线程中以 CDP 模式连接既有浏览器，可在 Jupyter / asyncio 环境中安全调用。

    参数：
        html_files  - HTML 文件路径列表（相对路径基于 CWD 解析）

    返回：
        {
            "paths": PNG 文件绝对路径列表（与 html_files 同序，输出到 HTML 同目录）,
            "guide": 展示给用户的输出格式与下一步引导文案
        }
    """
    paths = [Path(f).resolve() for f in html_files]
    for p in paths:
        if not p.is_file():
            raise FileNotFoundError(str(p))
    if not paths:
        out_paths: list[str] = []
    else:
        cdp_endpoint = _ensure_cdp_endpoint()
        out_paths = _run_async(lambda: _async_screenshot_slides(cdp_endpoint, paths))

    skill_path = os.environ.get("SKILL_PATH", "")
    gen_ppt_path = (
        os.path.join(skill_path, "pptx", "gen_html_ppt.md")
        if skill_path
        else "skills/pptx/gen_ppt.md"
    )
    guide = f"""[下一步] 用户选定风格方案后，读取 {gen_ppt_path} 进入生成阶段。
截图已完成，请按以下格式总结各方案展示给用户，每个方案仅包含两项，不附加任何额外说明，不做任何多余操作：
1. 一行方案描述：`方案 N：中文设计描述`
2. 紧接使用 **`sharing_files`** 格式输出截图链接
"""

    return {"paths": out_paths, "guide": guide}



# ── 幻灯片检测（HTML 合法性 → 跑版）──────────────────────────────────────────

_EXPECTED_W = 1280
_EXPECTED_H = 720

# 跑版类 issue kind（汇总时单独统计）
_LAYOUT_ISSUE_KINDS = frozenset({"scroll_overflow", "element_overflow", "text_overlap", "text_line_overlap"})

# 修复建议：(匹配的 kind 集合, 提示文本)，汇总报告中按出现的 kind 去重输出
_DEFAULT_FONT_HINT = "标题 48px、正文 22px"


def _build_fix_tips(min_font_hint: str | None = _DEFAULT_FONT_HINT) -> list[tuple[frozenset[str], str]]:
    font_suffix = f"；字号不得低于最小值：{min_font_hint}" if min_font_hint else ""
    return [
        (
            frozenset({"html_encoding", "html_preamble", "html_structure", "js_error", "dom_error"}),
            "  · [HTML] 去掉文首/文中误入的非 HTML 正文，修正标签闭合与嵌套、内联脚本语法",
        ),
        (
            frozenset({"text_overlap"}),
            "  · [文本重叠] 调整 flex/grid 间距、换行、缩小字号或拆页，消除文字内容的实际重叠"
            f"（勿依赖 position 硬塞{font_suffix}）",
        ),
        (
            frozenset({"scroll_overflow", "element_overflow"}),
            "  · [跑版] 减少该页文字内容或拆为两页；缩小字号或收紧行距"
            + (f"（不得低于最小值：{min_font_hint}）" if min_font_hint else ""),
        ),
        (
            frozenset({"text_line_overlap"}),
            "  · [文字与装饰线重叠] 增大相邻区域之间的间距（调整 top/margin/padding），"
            "或缩小上方区域内容的字号/行距以腾出空间",
        ),
    ]


# ── 同目录检测次数限流（Kernel 持久化期间生效）──────────────────────────────
_MAX_CHECKS_PER_DIR = 2
_layout_check_counts: dict[str, int] = {}


def _resolve_check_dir(html_paths: list[str]) -> str:
    """从文件列表中提取公共父目录作为计数 key。"""
    parents = {str(Path(p).resolve().parent) for p in html_paths}
    if len(parents) == 1:
        return parents.pop()
    common = os.path.commonpath([str(Path(p).resolve()) for p in html_paths])
    return common


def reset_layout_check_count(directory: str | None = None) -> str:
    """重置跑版检测计数器。

    参数：
        directory - 指定目录则只重置该目录的计数；为 None 则清空全部计数。

    返回：
        操作结果说明。
    """
    if directory is None:
        _layout_check_counts.clear()
        return "已重置所有目录的跑版检测计数"
    key = str(Path(directory).resolve())
    removed = _layout_check_counts.pop(key, None)
    if removed is not None:
        return f"已重置目录 {key} 的检测计数（之前为 {removed}）"
    return f"目录 {key} 无计数记录，无需重置"


def _issue_category(issue: dict[str, Any]) -> str:
    """单条 issue：「html」或「layout」。"""
    return "layout" if issue.get("kind") in _LAYOUT_ISSUE_KINDS else "html"


def _page_fail_category(issues: list[dict[str, Any]]) -> str:
    """整页归类：含任一非跑版问题则归为 HTML，否则为跑版。"""
    if not issues:
        return "ok"
    if any(_issue_category(it) == "html" for it in issues):
        return "html"
    return "layout"


# html5lib 报告的标签/嵌套问题；下列代码视为幻灯片常见可接受情况，不判失败
_IGNORE_HTML5LIB_CODES = frozenset(
    {
        "expected-doctype-but-got-start-tag",
    }
)

# 文首「在 <html>/<!DOCTYPE> 之前」若出现类似 Markdown/Python 的行且整行无标签，视为混入非 HTML
_FOREIGN_LINE = re.compile(
    r"^(?:#{1,6}\s+\S|```\s*$|```\w+|def\s+\w+\s*\(|class\s+\w+\s*[:(]|import\s+\w|from\s+\w+\s+import\b)",
)


def _format_html5lib_error(err: tuple[Any, ...]) -> str:
    loc = err[0]
    code = err[1]
    data: Any = err[2] if len(err) > 2 else {}
    line = loc[0] if len(loc) > 0 else 0
    col = loc[1] if len(loc) > 1 else 0
    extra = ""
    if isinstance(data, dict) and data:
        extra = " " + json.dumps(data, ensure_ascii=False)
    return f"L{line}:{col} [{code}]{extra}"


def _html_mixed_non_markup_issues(text: str) -> list[dict[str, Any]]:
    """
    检测 .html 中误入的非 HTML 源码/正文（如文首纯文本、Markdown、Python、未包在标签内的代码围栏等）。
    与「标签是否闭合」的 html5lib 检测互补。
    """
    raw = text.lstrip("\ufeff")
    if not raw.strip():
        return []

    head = raw[:16384]
    # 合法 HTML 应在忽略 BOM/空白后以「<」起笔
    if not re.match(r"^\s*<", head):
        return [
            {
                "kind": "html_non_markup_start",
                "detail": "文首在忽略 BOM/空白后仍不以「<」起始，疑似混入纯文本、Markdown 或非 HTML 源码",
            }
        ]

    hl = head.lower()
    if "<html" not in hl and "<!doctype" not in hl:
        if "<head" not in hl[:4096] and "<body" not in hl[:4096]:
            return [
                {
                    "kind": "html_missing_root",
                    "detail": "文首约 16KB 内未出现 <!DOCTYPE、<html>、<head> 或 <body>，不像完整 HTML 页面",
                }
            ]

    # 首个 <html> 之前的片段（通常含 DOCTYPE）；任一行完全无「<」又酷似 Markdown/Python → 混入非 HTML
    m_html = re.search(r"<\s*html\b", head, re.I)
    before_html = head[: m_html.start()] if m_html else ""
    before_html = re.sub(r"<!--[\s\S]*?-->", "", before_html)
    for line in before_html.splitlines():
        t = line.strip()
        if not t:
            continue
        if "<" in t:
            continue
        if _FOREIGN_LINE.match(t):
            snippet = t[:120] + ("…" if len(t) > 120 else "")
            return [
                {
                    "kind": "html_foreign_line",
                    "detail": f"在首个 <html> 之前出现疑似非 HTML 行（整行无标签尖括号）：{snippet!r}",
                }
            ]
    return []


def _html_static_issues(text: str) -> list[dict[str, Any]]:
    """静态检测：混入非 HTML 内容 → html5lib 标签结构（过滤无害项）。"""
    stripped = text.strip()
    if not stripped:
        return [{"kind": "html_empty", "detail": "HTML 文件为空或仅空白"}]

    mixed = _html_mixed_non_markup_issues(text)
    if mixed:
        return mixed

    try:
        import html5lib
    except ImportError:
        return [
            {
                "kind": "html_dependency",
                "detail": "缺少依赖 html5lib，请执行：pip install html5lib",
            }
        ]

    parser = html5lib.HTMLParser()
    try:
        parser.parse(StringIO(stripped))
    except Exception as e:
        return [{"kind": "html_parse_error", "detail": f"HTML 解析异常：{e}"}]

    filtered = [e for e in parser.errors if e[1] not in _IGNORE_HTML5LIB_CODES]
    if not filtered:
        return []
    details = "; ".join(_format_html5lib_error(e) for e in filtered[:8])
    return [{"kind": "html_invalid", "detail": f"HTML 标签结构问题（html5lib）：{details}"}]


def _html_browser_validity_js() -> str:
    """加载完成后检查 DOM 是否可用。"""
    return """
(() => {
  const issues = [];
  const de = document.documentElement;
  if (!de) {
    issues.push({
      kind: 'html_dom',
      detail: '加载后 document.documentElement 为 null，无法形成有效页面'
    });
  }
  return JSON.stringify(issues);
})()
"""


# 注入到 </head> 前；若无 head 则插到 <html> 后
_SAFE_FIX_STYLE = (
    """<style id="ppt-builder-layout-fixer">
/* ppt-builder: 防滚动 + 固定画布（自动注入，可手工微调后删除本段） */
html, body {
  margin: 0 !important;
  padding: 0 !important;
  width: """
    + str(_EXPECTED_W)
    + """px !important;
  height: """
    + str(_EXPECTED_H)
    + """px !important;
  max-width: """
    + str(_EXPECTED_W)
    + """px !important;
  max-height: """
    + str(_EXPECTED_H)
    + """px !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
}
.slide-container {
  width: """
    + str(_EXPECTED_W)
    + """px !important;
  height: """
    + str(_EXPECTED_H)
    + """px !important;
  max-width: """
    + str(_EXPECTED_W)
    + """px !important;
  max-height: """
    + str(_EXPECTED_H)
    + """px !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
  position: relative !important;
}
</style>"""
)


@dataclass
class SlideLayoutReport:
    """单页检测结果。"""

    path: str
    ok: bool
    width: int
    height: int
    issues: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {"path": self.path, "ok": self.ok, "width": self.width, "height": self.height, "issues": self.issues},
            ensure_ascii=False,
            indent=2,
        )


def _layout_check_js() -> str:
    """
    跑版四类检测：
    1. 滚动区域是否超过 1280×720（针对无 overflow:hidden 的情况）
    2. 任意元素 getBoundingClientRect 是否超出 1280×720 边界
       （可捕获 overflow:hidden 裁剪的隐式溢出）
    3. 可见文字是否重叠：对每个文本节点用 Range.getClientRects() 取行/字框，两两比较字框（非整块元素盒）；
       带透明度：祖先链 opacity 乘积或 color 的 alpha<1 的块不参与比较，以免误判水印/背景字）
    4. 文字与跨容器装饰线重叠：文本节点矩形与来自不同容器的 border / 薄 div 线条重叠
       （同容器内的文字和 border 视为有意设计，不报告）
    """
    w, h = _EXPECTED_W, _EXPECTED_H
    return f"""
(() => {{
  const EW = {w}, EH = {h};
  const issues = [];
  const EPS = 2;
  const MIN_OVERLAP_AREA = 80;

  // 检测1：滚动区域
  const de = document.documentElement;
  const body = document.body;
  const scrollW = Math.max(de.scrollWidth, body ? body.scrollWidth : 0);
  const scrollH = Math.max(de.scrollHeight, body ? body.scrollHeight : 0);
  if (scrollW > EW + 2 || scrollH > EH + 2) {{
    issues.push({{
      kind: "scroll_overflow",
      detail: "页面可滚动区域超过 1280×720，内容超出布局",
      scrollWidth: scrollW,
      scrollHeight: scrollH,
      expected: [EW, EH],
    }});
  }}

  // 检测2：元素边界（覆盖 overflow:hidden 场景）
  let maxRight = 0, maxBottom = 0;
  for (const el of document.querySelectorAll('*')) {{
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (r.right  > maxRight)  maxRight  = r.right;
    if (r.bottom > maxBottom) maxBottom = r.bottom;
  }}
  if (maxRight > EW + 2 || maxBottom > EH + 2) {{
    issues.push({{
      kind: "element_overflow",
      detail: "存在元素超出 1280×720 边界（overflow:hidden 裁剪不算合格）",
      maxRight:  Math.round(maxRight),
      maxBottom: Math.round(maxBottom),
      expected:  [EW, EH],
    }});
  }}

  // 检测3：基于文本节点 + Range.getClientRects() 的行/字框重叠（避免整块元素盒过大导致误判）
  // 带透明度的文字（水印/背景字）可与正文重叠，不参与两两比较
  function cumulativeOpacity(el) {{
    let o = 1;
    let cur = el;
    while (cur && cur.nodeType === 1) {{
      const v = parseFloat(window.getComputedStyle(cur).opacity);
      if (!isNaN(v)) o *= v;
      cur = cur.parentElement;
    }}
    return o;
  }}
  function textFillAlpha(cssColor) {{
    if (!cssColor) return 1;
    const s = String(cssColor).trim().toLowerCase();
    if (s === 'transparent') return 0;
    let m = s.match(/rgba?\\s*\\(([^)]+)\\)/i);
    if (m) {{
      const p = m[1].split(',').map(function (x) {{ return x.trim(); }});
      if (p.length >= 4) {{
        const a = parseFloat(p[3]);
        return isNaN(a) ? 1 : Math.min(1, Math.max(0, a));
      }}
    }}
    m = s.match(/hsla?\\s*\\(([^)]+)\\)/i);
    if (m) {{
      const p = m[1].split(',').map(function (x) {{ return x.trim(); }});
      if (p.length >= 4) {{
        const a = parseFloat(p[p.length - 1]);
        return isNaN(a) ? 1 : Math.min(1, Math.max(0, a));
      }}
    }}
    return 1;
  }}
  function isTransparentTextBlock(el) {{
    if (cumulativeOpacity(el) < 0.999) return true;
    const st = window.getComputedStyle(el);
    if (textFillAlpha(st.color) < 0.999) return true;
    return false;
  }}
  function briefEl(el) {{
    if (!el || !el.tagName) return '?';
    const cls = (typeof el.className === 'string' && el.className)
      ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.')
      : '';
    return el.tagName.toLowerCase() + cls;
  }}
  function isHiddenByAncestors(el) {{
    let c = el;
    while (c) {{
      const s = window.getComputedStyle(c);
      if (s.display === 'none' || s.visibility === 'hidden') return true;
      if (parseFloat(s.opacity || '1') === 0) return true;
      c = c.parentElement;
    }}
    return false;
  }}
  function textSnippet(tn) {{
    var t = (tn.nodeValue || '').replace(/\\s+/g, ' ').trim();
    if (t.length > 18) return t.slice(0, 18) + '…';
    return t;
  }}
  function collectTextLineRects() {{
    const out = [];
    if (!body) return out;
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, null);
    let tn;
    while ((tn = walker.nextNode())) {{
      if (!tn.nodeValue || !/\\S/.test(tn.nodeValue)) continue;
      const parent = tn.parentElement;
      if (!parent) continue;
      if (parent.closest && parent.closest('script, style, noscript')) continue;
      if (parent.closest('[class*="echarts"]')) continue;
      if (isHiddenByAncestors(parent)) continue;
      if (isTransparentTextBlock(parent)) continue;
      const range = document.createRange();
      range.setStart(tn, 0);
      range.setEnd(tn, tn.length);
      const cr = range.getClientRects();
      const rects = [];
      for (let k = 0; k < cr.length; k++) {{
        const r = cr[k];
        if (r.width > 1 && r.height > 1) rects.push(r);
      }}
      if (rects.length === 0) continue;
      out.push({{ tn: tn, parent: parent, rects: rects, brief: briefEl(parent) }});
    }}
    return out;
  }}
  const blocks = collectTextLineRects();
  const pairs = [];
  var textOverlapParents = new Set();
  outer:
  for (let i = 0; i < blocks.length; i++) {{
    for (let j = i + 1; j < blocks.length; j++) {{
      const A = blocks[i];
      const B = blocks[j];
      let hit = null;
      loopRect:
      for (let ia = 0; ia < A.rects.length; ia++) {{
        const ra = A.rects[ia];
        for (let ib = 0; ib < B.rects.length; ib++) {{
          const rb = B.rects[ib];
          const interW = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
          const interH = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
          if (interW <= EPS || interH <= EPS) continue;
          const interArea = interW * interH;
          if (interArea < MIN_OVERLAP_AREA) continue;
          const areaA = Math.max(ra.width * ra.height, 1);
          const areaB = Math.max(rb.width * rb.height, 1);
          const minA = Math.min(areaA, areaB);
          if (interArea / minA < 0.06) continue;
          hit = {{ iw: Math.round(interW), ih: Math.round(interH), sa: textSnippet(A.tn), sb: textSnippet(B.tn) }};
          break loopRect;
        }}
      }}
      if (hit) {{
        textOverlapParents.add(A.parent);
        textOverlapParents.add(B.parent);
        pairs.push({{
          a: A.brief,
          b: B.brief,
          iw: hit.iw,
          ih: hit.ih,
          sa: hit.sa,
          sb: hit.sb,
        }});
        if (pairs.length >= 6) break outer;
      }}
    }}
  }}
  if (pairs.length > 0) {{
    const msg = pairs.map(function (p) {{
      return p.a + ' 与 ' + p.b + '（「' + p.sa + '」/「' + p.sb + '」）重叠约 ' + p.iw + '×' + p.ih + 'px';
    }}).join('；');
    issues.push({{
      kind: "text_overlap",
      detail: "可见文字内容重叠：" + msg,
      pairs: pairs,
    }});
  }}
  // 检测4：文字与跨容器装饰线（border / 薄 div）重叠
  // 已参与 text_overlap 的文本块跳过（此时会有装饰线重叠），其余独立文本块正常检测
  // 仅当文字不在线条所属元素内部时才报告，排除同容器内的有意设计
  function isDescendantOf(child, ancestor) {{
    var node = child;
    while (node) {{
      if (node === ancestor) return true;
      node = node.parentElement;
    }}
    return false;
  }}
  function collectLineRects() {{
    var lines = [];
    if (!body) return lines;
    var all = body.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {{
      var el = all[i];
      if (isHiddenByAncestors(el)) continue;
      var st = window.getComputedStyle(el);
      var rect = el.getBoundingClientRect();
      // 薄 div/hr 线条（高度 ≤ 5px 且宽度 > 20px，有可见背景色）
      if (rect.height > 0 && rect.height <= 5 && rect.width > 20) {{
        var bg = st.backgroundColor;
        if (bg && bg !== 'transparent' && bg !== 'rgba(0, 0, 0, 0)') {{
          lines.push({{ top: rect.top, bottom: rect.bottom, left: rect.left, right: rect.right, el: el, src: briefEl(el) }});
        }}
      }}
      // 元素 border-top / border-bottom（>= 2px 且有可见颜色）
      var sides = ['Top', 'Bottom'];
      for (var s = 0; s < sides.length; s++) {{
        var side = sides[s];
        var bw = parseFloat(st['border' + side + 'Width']) || 0;
        if (bw < 2) continue;
        var bc = st['border' + side + 'Color'];
        if (!bc || bc === 'transparent' || bc === 'rgba(0, 0, 0, 0)') continue;
        var lt, lb;
        if (side === 'Top') {{ lt = rect.top; lb = rect.top + bw; }}
        else {{ lt = rect.bottom - bw; lb = rect.bottom; }}
        lines.push({{ top: lt, bottom: lb, left: rect.left, right: rect.right, el: el, src: briefEl(el) + ' border-' + side.toLowerCase() }});
      }}
    }}
    return lines;
  }}
  var lineRects = collectLineRects();
  var tlPairs = [];
  for (var ti = 0; ti < blocks.length && tlPairs.length < 4; ti++) {{
    var tb = blocks[ti];
    if (textOverlapParents.has(tb.parent)) continue;
    for (var li = 0; li < lineRects.length && tlPairs.length < 4; li++) {{
      var ln = lineRects[li];
      if (isDescendantOf(tb.parent, ln.el)) continue;
      for (var ri = 0; ri < tb.rects.length; ri++) {{
        var tr = tb.rects[ri];
        var iw = Math.min(tr.right, ln.right) - Math.max(tr.left, ln.left);
        var ih = Math.min(tr.bottom, ln.bottom) - Math.max(tr.top, ln.top);
        if (iw > EPS && ih > 0.5) {{
          tlPairs.push({{
            text: briefEl(tb.parent),
            line: ln.src,
            snippet: textSnippet(tb.tn),
            iw: Math.round(iw),
            ih: Math.round(ih),
          }});
          break;
        }}
      }}
    }}
  }}
  if (tlPairs.length > 0) {{
    var tlMsg = tlPairs.map(function (p) {{
      return p.text + '「' + p.snippet + '」与 ' + p.line + ' 重叠约 ' + p.iw + '×' + p.ih + 'px';
    }}).join('；');
    issues.push({{
      kind: "text_line_overlap",
      detail: "文字与装饰线跨容器重叠：" + tlMsg,
      pairs: tlPairs,
    }});
  }}
  return JSON.stringify(issues);
}})()
"""


_GOTO_TIMEOUT_MS = 10_000


def _post_dom_wait_ms() -> int:
    try:
        return max(0, int(os.environ.get("PPT_LAYOUT_POST_MS", "0") or "0"))
    except ValueError:
        return 0


async def _async_layout_batch(cdp_endpoint: str, paths: list[Path]) -> list[list[dict[str, Any]]]:
    from nodriver import cdp

    browser = await _connect_browser(cdp_endpoint)
    tab = None
    try:
        tab = await _open_new_tab(browser, "about:blank")
        await tab.send(
            cdp.emulation.set_device_metrics_override(
                width=_EXPECTED_W,
                height=_EXPECTED_H,
                device_scale_factor=1,
                mobile=False,
            )
        )

        page_errors: list[str] = []

        def _on_exception(evt: Any) -> None:
            try:
                page_errors.append(_format_runtime_exception(evt))
            except Exception:
                pass

        try:
            await tab.send(cdp.runtime.enable())
        except Exception:
            pass
        try:
            tab.add_handler(cdp.runtime.ExceptionThrown, _on_exception)
        except Exception:
            pass

        layout_js = _layout_check_js()
        validity_js = _html_browser_validity_js()
        post_wait_ms = _post_dom_wait_ms()

        batch: list[list[dict[str, Any]]] = []
        for path in paths:
            uri = path.as_uri()
            page_errors.clear()
            await tab.get(uri)
            try:
                await _wait_dcl(tab, timeout=_GOTO_TIMEOUT_MS / 1000)
            except asyncio.TimeoutError:
                pass
            if post_wait_ms > 0:
                await asyncio.sleep(post_wait_ms / 1000.0)

            combined: list[dict[str, Any]] = []
            if page_errors:
                combined.append(
                    {
                        "kind": "page_js_error",
                        "detail": "页面脚本异常：" + "；".join(page_errors[:5]),
                    }
                )
            dom_raw = await _tab_eval(tab, validity_js)
            if isinstance(dom_raw, str):
                combined.extend(json.loads(dom_raw))
            if combined:
                batch.append(combined)
                continue

            raw = await _tab_eval(tab, layout_js)
            batch.append(json.loads(raw) if isinstance(raw, str) else [])
        return batch
    finally:
        await _close_tab(tab)
        await _disconnect_browser(browser)


def _run_browser_batch(html_paths: list[str]) -> list[list[dict[str, Any]]]:
    """只启动一次浏览器会话，顺序检测多页，返回与 html_paths 同序的 issues 列表。"""
    paths = [Path(p).resolve() for p in html_paths]
    for p in paths:
        if not p.is_file():
            raise FileNotFoundError(str(p))
    if not paths:
        return []
    cdp_endpoint = _ensure_cdp_endpoint()
    return _run_async(lambda: _async_layout_batch(cdp_endpoint, paths))


def check_slides_layout(html_paths: list[str], *, min_font_hint: str | None = _DEFAULT_FONT_HINT) -> str:
    """
    批量检测：先静态（UTF-8、是否混入非 HTML 正文、html5lib 结构），未通过则不进浏览器；
    通过的页面整批只启动一次浏览器，再测脚本/DOM，最后测跑版。

    同一目录最多检测 2 次（Kernel 持久化期间累计），超出后直接返回提示。
    可调用 reset_layout_check_count() 手动重置。

    参数：
        html_paths     - HTML 文件路径列表
        min_font_hint  - 修复建议中的字号下限提示，默认 "标题 48px、正文 22px"；
                         传 None 则不输出字号下限（适用于同款等字号由模板决定的场景）

    返回：
        人类可读报告。失败行带前缀 [HTML]（含编码、混入非 HTML、标签结构、脚本/DOM）或 [跑版]（画布越界）；
        末行汇总分别统计两类未通过页数。
    """
    paths = [Path(p).resolve() for p in html_paths]
    for p in paths:
        if not p.is_file():
            raise FileNotFoundError(str(p))

    if paths:
        check_dir = _resolve_check_dir(html_paths)
        current = _layout_check_counts.get(check_dir, 0)
        if current >= _MAX_CHECKS_PER_DIR:
            return (
                f"该目录已完成 {current} 次跑版检测，已达上限（{_MAX_CHECKS_PER_DIR} 次），跳过本次检测。\n"
            )

    if not paths:
        return "\n汇总：0 页全部通过"

    merged: list[list[dict[str, Any]] | None] = [None] * len(paths)
    for i, p in enumerate(paths):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            merged[i] = [{"kind": "html_encoding", "detail": f"UTF-8 解码失败：{e}"}]
            continue
        static = _html_static_issues(text)
        if static:
            merged[i] = static
        # else None → 待浏览器检测

    pending = [i for i in range(len(paths)) if merged[i] is None]
    if pending:
        sub_paths = [str(paths[i]) for i in pending]
        sub_results = _run_browser_batch(sub_paths)
        for j, orig_i in enumerate(pending):
            merged[orig_i] = sub_results[j]

    issues_list: list[list[dict[str, Any]]] = []
    for i in range(len(paths)):
        block = merged[i]
        assert block is not None
        issues_list.append(block)

    lines: list[str] = []
    fail_count = 0
    fail_html = 0
    fail_layout = 0
    seen_kinds: set[str] = set()
    for p, issues in zip(paths, issues_list, strict=True):
        abs_path = str(Path(p).resolve())
        name = Path(p).name
        if issues:
            fail_count += 1
            cat = _page_fail_category(issues)
            if cat == "html":
                fail_html += 1
                tag = "[HTML]"
            else:
                fail_layout += 1
                tag = "[跑版]"
            parts = []
            for it in issues:
                kind = it.get("kind", "")
                seen_kinds.add(kind)
                if kind == "element_overflow":
                    mr = it.get("maxRight", 0)
                    mb = it.get("maxBottom", 0)
                    over_r = max(0, mr - _EXPECTED_W)
                    over_b = max(0, mb - _EXPECTED_H)
                    parts.append(
                        f"元素越界：右侧超出 {over_r}px、底部超出 {over_b}px"
                        f"（最远元素坐标 right={mr}px bottom={mb}px，画布 {_EXPECTED_W}×{_EXPECTED_H}）"
                    )
                elif kind == "scroll_overflow":
                    sw = it.get("scrollWidth", 0)
                    sh = it.get("scrollHeight", 0)
                    over_w = max(0, sw - _EXPECTED_W)
                    over_h = max(0, sh - _EXPECTED_H)
                    parts.append(
                        f"滚动区越界：宽超出 {over_w}px、高超出 {over_h}px"
                        f"（滚动尺寸 {sw}×{sh}，画布 {_EXPECTED_W}×{_EXPECTED_H}）"
                    )
                elif kind == "text_overlap":
                    parts.append(it.get("detail", "可读文本块矩形重叠"))
                elif kind == "text_line_overlap":
                    parts.append(it.get("detail", "文字与装饰线跨容器重叠"))
                else:
                    parts.append(it.get("detail", kind))
            lines.append(f"✗ {name}  FAIL {tag}  {'；'.join(parts)}  [{abs_path}]")

    if paths:
        _layout_check_counts[check_dir] = current + 1
        remaining = _MAX_CHECKS_PER_DIR - (current + 1)

    total = len(paths)
    if fail_count == 0:
        lines.append(f"\n汇总：共 {total} 页，全部通过")
    else:
        lines.append(
            f"\n汇总：共 {total} 页，未通过 {fail_count} 页"
            f"（其中 HTML 相关问题 {fail_html} 页，跑版 {fail_layout} 页）"
        )
        lines.append("\n修复建议")
        for kind, tip in _build_fix_tips(min_font_hint):
            if kind & seen_kinds:
                lines.append(tip)
    return "\n".join(lines)


def check_slide_layout(html_path: str, *, min_font_hint: str | None = _DEFAULT_FONT_HINT) -> str:
    """检测单张是否超出布局（内部走批量接口）。"""
    return check_slides_layout([html_path], min_font_hint=min_font_hint)


def apply_safe_layout_css(html_path: str, output_path: str | None = None, backup: bool = True) -> Path:
    """
    在 HTML 的 <head> 内注入防滚动 + 固定画布 CSS（不改业务结构）。
    - output_path 为 None 时覆盖原文件；若 backup=True，先复制为 .bak。
    """
    p = Path(html_path)
    text = p.read_text(encoding="utf-8")

    injection = _SAFE_FIX_STYLE

    if "ppt-builder-layout-fixer" in text:
        out = Path(output_path) if output_path else p
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        return out.resolve()

    lower = text.lower()
    if "</head>" in lower:
        idx = lower.rindex("</head>")
        new_text = text[:idx] + injection + "\n" + text[idx:]
    elif re.search(r"<html[^>]*>", text, re.I):
        new_text = re.sub(
            r"(<html[^>]*>)",
            lambda m: m.group(1) + "\n<head>" + injection + "</head>\n",
            text,
            count=1,
            flags=re.I,
        )
    else:
        new_text = injection + "\n" + text

    out = Path(output_path) if output_path else p
    if backup and out.resolve() == p.resolve():
        shutil.copy2(p, p.with_suffix(p.suffix + ".bak"))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(new_text, encoding="utf-8")
    return out.resolve()


def print_report(report: SlideLayoutReport) -> None:
    """已废弃，保留仅供向后兼容；请直接使用 check_slides_layout() 的返回值。"""
    print(f"[layout] {report.path} — {'通过' if report.ok else '存在问题'} ({report.width}×{report.height})")
    for i, it in enumerate(report.issues, 1):
        kind = it.get("kind", "?")
        detail = it.get("detail", "")
        print(f"  {i}. [{kind}] {detail}")
        extra = {k: v for k, v in it.items() if k not in ("kind", "detail")}
        if extra:
            print(f"     {json.dumps(extra, ensure_ascii=False)}")
