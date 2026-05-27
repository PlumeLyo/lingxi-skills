"""
ap.py

提供智能文档的创建、读取、写入、块查询、块插入、块删除、块更新等能力。

"""

import io
import json
import mimetypes
import os
import re
import struct
from typing import Any, Optional

import requests

import sys as _sys
import os as _os
_shared = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), "..", "..", "scripts"))
if _shared not in _sys.path:
    _sys.path.insert(0, _shared)
from wps_http import BaseClient
from kdocs import _encode_query_value, _append_link_params


# ──────────────────────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────────────────────


def _make_result(success: bool, data: Any = None, message: str = "", error: str = "") -> dict:
    r: dict = {"success": success}
    if data is not None:
        r["data"] = data
    if message:
        r["message"] = message
    if error:
        r["error"] = error
    return r


def _image_size(data: bytes) -> tuple:
    """
    从图片二进制数据解析原始宽高，支持 PNG / JPEG / GIF / WEBP。
    """
    try:
        f = io.BytesIO(data)
        head = f.read(24)
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            w, h = struct.unpack('>II', head[16:24])
            return w, h
        if head[:2] in (b'\xff\xd8',):
            f.seek(0)
            f.read(2)
            for _ in range(500):
                marker_data = f.read(2)
                if len(marker_data) < 2:
                    break
                marker, = struct.unpack('>H', marker_data)
                length_data = f.read(2)
                if len(length_data) < 2:
                    break
                length, = struct.unpack('>H', length_data)
                if marker in (0xFFC0, 0xFFC1, 0xFFC2):
                    f.read(1)
                    h, w = struct.unpack('>HH', f.read(4))
                    return w, h
                if length < 2:
                    break
                f.read(length - 2)
        if head[:6] in (b'GIF87a', b'GIF89a'):
            w, h = struct.unpack('<HH', head[6:10])
            return w, h
        if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
            f.seek(0)
            riff = f.read(12)
            chunk = f.read(4)
            if chunk == b'VP8 ':
                f.read(4)
                f.read(6)
                w, h = struct.unpack('<HH', f.read(4))
                return w & 0x3FFF, h & 0x3FFF
            if chunk == b'VP8L':
                f.read(4)
                f.read(1)
                bits = struct.unpack('<I', f.read(4))[0]
                w = (bits & 0x3FFF) + 1
                h = ((bits >> 14) & 0x3FFF) + 1
                return w, h
        return 0, 0
    except Exception:
        return 0, 0


def _render_size(width: int, height: int, max_size: int = 360) -> int:
    """
    等比缩放到 max_size 内，返回渲染宽度 renderWidth。
    """
    if width <= 0 or height <= 0:
        return max_size
    if width >= height:
        return min(width, max_size)
    return round(width * min(height, max_size) / height)


def _inject_index(blocks: list) -> None:
    """
    为 content 数组中每个子块注入 index 字段，方便 AI 直接用索引定位块位置。
    """
    for block in blocks:
        content = block.get("content")
        if isinstance(content, list):
            for i, child in enumerate(content):
                child["index"] = i
                _inject_index([child])


def _collect_source_keys(blocks: list) -> list:
    """递归收集块树中所有 picture 块的 sourceKey。"""
    keys = []
    for block in blocks:
        if block.get("type") == "picture":
            sk = (block.get("attrs") or {}).get("sourceKey", "")
            if sk:
                keys.append(sk)
        child = block.get("content")
        if isinstance(child, list):
            keys.extend(_collect_source_keys(child))
    return keys



# ──────────────────────────────────────────────────────────────────────────────
# OtlClient：智能文档操作客户端
# ──────────────────────────────────────────────────────────────────────────────


class OtlClient(BaseClient):
    _KDOCS_BASE = "https://365.kdocs.cn"

    def __init__(self):
        super().__init__(csrf=False)

    def _get_link_id(self, file_id: str) -> str:
        """
        从 file_id 解析出 core/execute 所需的 link_id。
        - 非纯数字 ID：本身就是 link_id（来自 URL 365.kdocs.cn/l/{link_id}），直接可用
        - 纯数字 ID（v5）：通过 v5 元数据接口获取 link_id
        """
        try:
            int(file_id)
        except (TypeError, ValueError):
            return file_id
        resp = self._s.get(f"{self._V5_BASE}/api/v5/files/{file_id}/metadata", params={"with_link": "true"})
        if resp.get("result") != "ok":
            raise ValueError(f"v5 获取元数据失败: {resp.get('msg', '未知错误')}")
        link_id = (resp.get("fileinfo") or {}).get("link_id", "")
        if not link_id:
            raise ValueError(f"v5 文件 {file_id} 未找到 link_id")
        return link_id

    def _get_private_drive_id(self) -> str:
        """获取私人云盘 ID，优先返回「我的企业文档」，否则返回第一个。"""
        resp = self._s.get(f"{self._v7}/v7/drives", params={"allotee_type": "user", "page_size": 10})
        if resp.get("code") != 0:
            raise ValueError(resp.get("msg") or "获取云盘列表失败")
        items = (resp.get("data") or {}).get("items") or []
        for item in items:
            if item.get("name") == "我的企业文档":
                return item["id"]
        if items:
            return items[0]["id"]
        raise ValueError("未找到可用云盘")

    @staticmethod
    def _check_resp(resp: dict) -> dict:
        """
        统一校验 core/execute 响应。
        core/execute 有两种错误格式:
          - 新版: {"code": -1, "msg": "..."}
          - 旧版: {"errno": 10000, "result": "clinkUserNotLogin", "msg": "..."}
        成功时返回 data / detail / 整个 resp。
        """
        errno = resp.get("errno")
        if errno is not None and errno != 0:
            raise RuntimeError(resp.get("msg") or resp.get("result") or f"errno={errno}")
        r, c = resp.get("result"), resp.get("code")
        if r not in (None, "ok"):
            raise RuntimeError(resp.get("msg") or r or "未知错误")
        if c is not None and c != 0:
            raise RuntimeError(resp.get("msg") or f"code={c}")
        return resp.get("data") or resp.get("detail") or resp

    def _exec(self, link_id: str, subtype: str, params: Any) -> dict:
        """
        调用 http.otl.exec 接口（写操作：insertContent / block.insert / block.update / block.delete）。
        成功返回响应的 data 或 detail 字段，失败抛出 RuntimeError。
        """
        resp = self._s.post(
            f"{self._KDOCS_BASE}/api/v3/office/file/{link_id}/core/execute",
            {"command": "http.otl.exec", "param": {"subType": subtype, "params": params}},
        )
        return self._check_resp(resp)

    def _query(self, link_id: str, name: str, params: Any) -> dict:
        """
        调用 http.otl.query 接口（读操作：block.query / convert）。
        core/execute 对 query 操作会返回 {name, params, result} 包装层，
        本方法自动解包，直接返回 result 中的实际数据。
        """
        resp = self._s.post(
            f"{self._KDOCS_BASE}/api/v3/office/file/{link_id}/core/execute",
            {"command": "http.otl.query", "param": {"name": name, "params": params}},
        )
        wrapper = self._check_resp(resp)
        if isinstance(wrapper, dict) and "name" in wrapper and "result" in wrapper:
            return wrapper["result"]
        return wrapper

    # ── 公开 API ──────────────────────────────────────────────────────────────

    def create_doc(
        self,
        name: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        parent_id: str = "0",
        drive_id: Optional[str] = None,
    ) -> dict:
        """
        新建智能文档（.otl），可选设置文档标题和 Markdown 正文内容。

        写入流程：
          1. 创建文档（文件名为 name）
          2. block.update update_content 对 doc 块替换整个内容为仅含 title 的数组，
             一步完成标题设置并消除默认空段落
          3. 若有 content，insertContent 写入 Markdown 正文
          4. 若正文含图片，逐张上传并通过 block.update 更新对应 picture 块的 sourceKey

        Args:
            name:      文件名（.otl 后缀可省略）
            title:     文档大标题文字；为 None 时默认取 name（去掉后缀）
            content:   可选，Markdown 正文内容；为 None 时仅创建标题文档
            parent_id: 父文件夹 ID，默认 "0"（根目录）
            drive_id:  云盘 ID，默认自动获取

        Returns:
            {
                "success": True,
                "data": {
                    "link_id": "link_id",
                    "name": "文件名.otl",
                    "link_url": "云文档链接"
                },
                "message": "成功创建智能文档: xxx.otl，链接: https://..."
            }
        """
        try:
            if not name.endswith(".otl"):
                name += ".otl"
            doc_title = title if title else name

            if not drive_id:
                drive_id = self._get_private_drive_id()
            resp = self._s.post(
                f"{self._v7}/v7/drives/{drive_id}/files/{parent_id}/create",
                {"name": name, "file_type": "file"},
            )
            if resp.get("code") != 0:
                return _make_result(False, error=f"创建智能文档失败: {resp.get('msg', '未知错误')}")
            raw = resp.get("data") or {}
            link_id = raw.get("link_id", "")
            link_url = raw.get("link_url", "")
            if not link_id and link_url:
                parts = link_url.rstrip("/").split("/")
                if len(parts) >= 2 and parts[-2] == "l":
                    link_id = parts[-1]

            # 查询初始块结构（新建文档默认含 title + 空 paragraph）
            doc_data = self._query(link_id, "block.query", {"blockIds": ["doc"]})
            initial_content = ((doc_data.get("blocks") or [{}])[0]).get("content", [])

            # 更新 title 块内容
            title_block = next((b for b in initial_content if b.get("type") == "title"), None)
            if title_block:
                self._exec(link_id, "block.update", [{
                    "blockId": title_block["id"],
                    "operation": "update_content",
                    "content": [{"type": "text", "content": doc_title}],
                }])

            if content:
                image_urls = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", content)
                self._exec(link_id, "insertContent", {"content": content, "pos": "end"})

                # insertContent 之后文档结构为 [title, para(空), ...正文块...]
                # 此时 doc 不止 title 一个块，删除空段落是安全的
                for i, blk in enumerate(initial_content):
                    if blk.get("type") == "paragraph":
                        try:
                            self._exec(link_id, "block.delete", {
                                "blockId": "doc",
                                "startIndex": i,
                                "endIndex": i + 1,
                            })
                        except RuntimeError:
                            pass  # 删除失败不影响整体流程

                if image_urls:
                    uploads = [self._upload_attachment(link_id, u) for u in image_urls]

                    # 查询结构，找到所有 picture 占位块
                    doc_data = self._query(link_id, "block.query", {"blockIds": ["doc"]})
                    picture_blocks = [
                        item
                        for item in ((doc_data.get("blocks") or [{}])[0]).get("content", [])
                        if item.get("type") == "picture"
                    ]

                    for idx, up in enumerate(uploads):
                        if up and idx < len(picture_blocks):
                            pic = picture_blocks[idx]
                            attrs = dict(pic.get("attrs", {}))
                            attrs["sourceKey"] = up["attachment_id"]
                            attrs["width"] = up["width"]
                            attrs["height"] = up["height"]
                            attrs["renderWidth"] = up["renderWidth"]
                            self._exec(link_id, "block.update", [
                                {"blockId": pic["id"], "operation": "update_attrs", "attrs": attrs}
                            ])
            

            link_url = _append_link_params(link_url, name)
            message = f"成功创建智能文档: {name}，链接: {link_url}"

            return _make_result(
                True,
                data={
                    "link_id": link_id,
                    "name": name,
                    "link_url": link_url,
                },
                message=message,
            )
        except Exception as e:
            return _make_result(False, error=f"创建智能文档失败: {str(e)}")

    def block_query(self, file_id: str) -> dict:
        """
        查询智能文档结构详情，返回完整的块结构树。

        Args:
            file_id: 智能文档文件 ID

        Returns:
            {
                "success": True,
                "data": {
                    "blocks": [
                        {
                            "id": "doc",
                            "type": "doc",
                            "content": [
                                {"id": "...", "type": "title", "attrs": {...}},
                                {"id": "...", "type": "paragraph", "content": [...], "attrs": {...}},
                                ...
                            ]
                        }
                    ]
                },
                "message": "查询文档内容成功"
            }
        """
        try:
            link_id = self._get_link_id(file_id)
            data = self._query(link_id, "block.query", {"blockIds": ["doc"]})
            if isinstance(data, dict) and "blocks" in data:
                _inject_index(data["blocks"])
            return _make_result(True, data=data, message="查询文档内容成功")
        except Exception as e:
            return _make_result(False, error=f"查询文档内容失败: {e}")

    def _resolve_images_in_content(self, link_id: str, content: list) -> list:
        """
        递归扫描块数组，将 picture 块中的 image_url 自动上传并替换为
        sourceKey / width / height / renderWidth。
        其他类型的块会递归处理其子块（content 字段）。
        """
        resolved = []
        for blk in content:
            blk = dict(blk)
            if blk.get("type") == "picture":
                attrs = dict(blk.get("attrs") or {})
                image_url = attrs.pop("image_url", None)
                if image_url:
                    up = self._upload_attachment(link_id, image_url)
                    if up:
                        attrs["sourceKey"] = up["attachment_id"]
                        attrs["width"] = up["width"]
                        attrs["height"] = up["height"]
                        attrs["renderWidth"] = up["renderWidth"]
                blk["attrs"] = attrs
            elif isinstance(blk.get("content"), list):
                blk["content"] = self._resolve_images_in_content(link_id, blk["content"])
            resolved.append(blk)
        return resolved

    def block_insert(
        self,
        file_id: str,
        index: int,
        content: list,
        block_id: str = "doc"
    ) -> dict:
        """
        在智能文档指定父块下按索引插入块内容。

        调用前须先通过 block_query 获取文档结构，确定正确的 block_id 和 index。

        支持在 content 中插入图片块：将 picture 块的 attrs.image_url 设为图片地址
        （URL 或本地路径），方法会自动上传并填充 sourceKey / width / height / renderWidth。

        Args:
            file_id:   智能文档文件 ID
            block_id:  目标父块 ID，"doc" 表示在文档级插入
            index:     插入位置索引（block_id 为 "doc" 时需 ≥ 1，index=0 是标题）
            content:   块节点数组，picture 块可用 attrs.image_url 代替 sourceKey

        Returns:
            {"success": True, "data": {...}, "message": "插入块成功"}
        """
        try:
            link_id = self._get_link_id(file_id)
            content = self._resolve_images_in_content(link_id, content)
            data = self._exec(link_id, "block.insert", {"blockId": block_id, "index": index, "content": content})
            return _make_result(True, data=data, message="插入块成功")
        except Exception as e:
            return _make_result(False, error=f"插入块失败: {e}")

    def block_delete(
        self,
        file_id: str,
        start_index: int,
        end_index: int,
        block_id: str = "doc"
    ) -> dict:
        """
        删除智能文档中指定父块下 [startIndex, endIndex) 区间的子块（左闭右开）。

        Args:
            file_id: 智能文档文件 ID
            block_id: 目标父块 ID
            start_index: 删除起始索引（包含）
            end_index: 删除末尾索引（不包含），需大于 start_index

        Returns:
            {"success": True, "data": {...}, "message": "删除块成功"}
        """
        try:
            link_id = self._get_link_id(file_id)
            data = self._exec(
                link_id,
                "block.delete",
                {"blockId": block_id, "startIndex": start_index, "endIndex": end_index},
            )
            return _make_result(True, data=data, message="删除块成功")
        except Exception as e:
            return _make_result(False, error=f"删除块失败: {e}")

    def block_update(self, file_id: str, params: list) -> dict:
        """
        更新智能文档指定块的内容或属性，支持多种操作类型。

        Args:
            file_id: 智能文档文件 ID
            params: 操作数组，每项含以下字段：
                - operation (str, 必填): 操作类型，见下方说明
                - blockId (str, 必填): 目标块 ID

        支持的 operation 类型：
            update_content       - 更新块内容（需传 content 数组）
            update_attrs         - 更新块属性（需传 attrs 对象，覆盖操作）
            insert_table_rows    - 插入表格行（需传 content 和可选 start）
            insert_table_columns - 插入表格列
            delete_table_rows    - 删除表格行（需传 count 和可选 start）
            delete_table_columns - 删除表格列
            merge_table_cells    - 合并单元格（需传 rowSpan, colSpan）
            split_table_cell     - 拆分单元格

        Returns:
            {"success": True, "data": {...}, "message": "更新块成功"}
        """
        try:
            link_id = self._get_link_id(file_id)
            data = self._exec(link_id, "block.update", params)
            return _make_result(True, data=data, message="更新块成功")
        except Exception as e:
            return _make_result(False, error=f"更新块失败: {e}")

    def _resolve_image_urls(self, link_id: str, source_keys: list) -> dict:
        """
        批量将 sourceKey 解析为可访问的临时图片 URL。
        通过 attachment/shapes 接口，传入 attachment_id 列表，返回 {sourceKey: url} 映射。
        """
        if not source_keys:
            return {}
        objects = [{"attachment_id": sk} for sk in source_keys]
        resp = self._s.post(
            f"{self._KDOCS_BASE}/api/v3/office/file/{link_id}/attachment/shapes",
            {"objects": objects},
        )
        data = resp.get("data") or {}
        return {sk: info["url"] for sk in source_keys if (info := data.get(sk)) and info.get("url")}

    def download_otl(
        self,
        file_id: str,
        save_dir: Optional[str] = None,
        include_images: bool = False,
    ) -> dict:
        """
        将智能文档导出为 Markdown 文件。

        通过 exportToMarkDown 接口获取文档的 Markdown 正文。
        当 include_images=True 时，自动查询文档中的图片块，
        将 sourceKey 解析为可访问的临时 URL 并嵌入 Markdown。

        Args:
            file_id:        智能文档文件 ID
            save_dir:       保存目录，默认当前工作目录
            include_images: 是否获取图片并嵌入到 Markdown 中

        Returns:
            {
                "success": True,
                "data": {
                    "file_path": "/path/to/file.md",
                    "name": "xxx.md",
                    "size": 1234
                },
                "message": "导出成功，保存路径为: /path/to/file.md"
            }
        """
        try:
            link_id = self._get_link_id(file_id)
            save_dir = save_dir or os.getcwd()
            os.makedirs(save_dir, exist_ok=True)

            result = self._query(link_id, "exportToMarkDown", {})
            if isinstance(result, dict):
                md_content = result.get("markdown") or result.get("content") or result.get("text") or ""
            elif isinstance(result, str):
                md_content = result
            else:
                md_content = str(result) if result else ""

            if not md_content:
                return _make_result(False, error="导出的 Markdown 内容为空")

            if include_images:
                doc_data = self._query(link_id, "block.query", {"blockIds": ["doc"]})
                blocks = ((doc_data.get("blocks") or [{}])[0]).get("content", [])
                source_keys = _collect_source_keys(blocks)
                if source_keys:
                    url_map = self._resolve_image_urls(link_id, source_keys)
                    for sk, url in url_map.items():
                        md_content = md_content.replace(sk, url)

            md_name = f"{file_id}.md"
            save_path = os.path.join(save_dir, md_name)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            return _make_result(
                True,
                data={"file_path": save_path, "name": md_name, "size": len(md_content.encode("utf-8"))},
                message=f"导出成功，保存路径为: {save_path}",
            )
        except Exception as e:
            err_msg = str(e)
            if "无权限" in err_msg or "403" in err_msg:
                return _make_result(False, error="下载失败: 无权限。请停止当前操作，并提示用户向文件所有者申请访问权限后重试。")
            return _make_result(False, error=f"导出 Markdown 失败: {err_msg}")

    def _upload_attachment(
        self,
        link_id: str,
        image_source: str,
        file_name: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[dict]:
        """
        内部图片上传方法（3 步：申请地址 → 直传 → 回调）。


        成功返回:
            {
                "attachment_id": "xxx",
                "width": 1920, "height": 1080,
                "renderWidth": 360
            }
        """
        try:
            if image_source.startswith(("http://", "https://")):
                dl_resp = requests.get(image_source, timeout=30)
                dl_resp.raise_for_status()
                file_data = dl_resp.content
                if not file_name:
                    file_name = image_source.split("/")[-1].split("?")[0] or "image.png"
                if not content_type:
                    content_type = (
                        dl_resp.headers.get("Content-Type", "").split(";")[0].strip()
                        or mimetypes.guess_type(file_name)[0]
                        or "image/png"
                    )
            else:
                with open(image_source, "rb") as f:
                    file_data = f.read()
                if not file_name:
                    file_name = os.path.basename(image_source)
                if not content_type:
                    content_type = mimetypes.guess_type(file_name)[0] or "image/png"

            file_size = len(file_data)
            text_hdr = {
                "Content-Type": "text/plain;charset=UTF-8",
                "Referer": f"{self._KDOCS_BASE}/l/{link_id}",
            }

            #  申请上传地址
            addr_url = f"{self._KDOCS_BASE}/api/v3/office/file/{link_id}/attachment/upload/address"
            addr_body = json.dumps(
                {"name": file_name, "size": file_size, "content_type": content_type},
                ensure_ascii=False,
            ).encode("utf-8")
            addr_resp = self._s._http.post(addr_url, data=addr_body, headers=text_hdr, timeout=30)
            addr_resp.raise_for_status()
            addr_data = addr_resp.json()
            upload_url = addr_data["request"]["url"]
            upload_headers = addr_data["request"].get("headers", {})
            upload_id = addr_data["upload_id"]
            send_back_params = addr_data.get("send_back_params", {})

            #  传文件到云存储
            put_headers = dict(upload_headers)
            put_headers["Content-Type"] = content_type
            put_resp = requests.put(upload_url, data=file_data, headers=put_headers, timeout=60)
            put_resp.raise_for_status()

            params_for_complete: dict = {}
            for param_name, source in send_back_params.items():
                if source.startswith("header."):
                    header_name = source[len("header."):]
                    params_for_complete[param_name] = put_resp.headers.get(header_name, "")

            missing = [k for k, v in params_for_complete.items() if not v]
            if missing:
                raise ValueError(f"Step 2 响应头缺少参数: {missing}")

            #  上传完成回调
            complete_url = f"{self._KDOCS_BASE}/api/v3/office/file/{link_id}/attachment/upload/complete"
            complete_body = json.dumps(
                {"upload_id": upload_id, "params": params_for_complete},
                ensure_ascii=False,
            ).encode("utf-8")
            complete_resp = self._s._http.post(complete_url, data=complete_body, headers=text_hdr, timeout=30)
            complete_resp.raise_for_status()
            complete_data = complete_resp.json()

            attachment_id = complete_data.get("attachment_id")
            if not attachment_id:
                return None
            img_w, img_h = _image_size(file_data)
            render_w = _render_size(img_w, img_h)
            return {
                "attachment_id": attachment_id,
                "width": img_w,
                "height": img_h,
                "renderWidth": render_w,
            }
        except Exception:
            return None



def _get() -> OtlClient:
    return OtlClient()


def create_doc(*args, **kwargs):      return _get().create_doc(*args, **kwargs)
def block_query(*args, **kwargs):     return _get().block_query(*args, **kwargs)
def block_insert(*args, **kwargs):    return _get().block_insert(*args, **kwargs)
def block_delete(*args, **kwargs):    return _get().block_delete(*args, **kwargs)
def block_update(*args, **kwargs):    return _get().block_update(*args, **kwargs)
def download_otl(*args, **kwargs): return _get().download_otl(*args, **kwargs)
