"""
dbsheet.py — WPS 365 V7 多维表（DbSheet）API。

本模块作为库使用，由 AI 生成代码后 import 顶层函数即可（内部单例，无需也不应实例化类）：

    import sys, os
    sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'scripts'))
    import dbsheet

    result = dbsheet.get_schema("abc123")
    print(result)
"""

import json
import os
from typing import Any, List, Optional

import requests

import sys as _sys
import os as _os

_shared = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), "..", "..", "scripts")
)
if _shared not in _sys.path:
    _sys.path.insert(0, _shared)
from wps_http import BaseClient
from kdocs import _encode_query_value, _append_link_params


def _wrap(resp: Any) -> dict:
    return dict(resp) if isinstance(resp, dict) else {}


def _make_result(
    success: bool, data: Any = None, message: str = "", error: str = ""
) -> dict:
    r: dict = {"success": success}
    if data is not None:
        r["data"] = data
    if message:
        r["message"] = message
    if error:
        r["error"] = error
    return r


def _ok(resp: dict, message: str = "") -> dict:
    """响应 code==0 时提取 data 并包装为成功结果。"""
    if resp.get("code", -1) == 0:
        return _make_result(True, data=resp.get("data"), message=message)
    return _make_result(
        False, error=resp.get("msg") or resp.get("message") or "未知错误"
    )


def _parse_fields(rec: dict) -> dict:
    """将记录的 fields 字段从 JSON 字符串原地解析为 dict，返回修改后的记录副本。"""
    raw = rec.get("fields")
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            rec = dict(rec)
            rec["fields"] = parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, ValueError):
            rec = dict(rec)
            rec["fields"] = {}
    elif not isinstance(raw, dict):
        rec = dict(rec)
        rec["fields"] = {}
    return rec


def _parse_records(data: Optional[dict]) -> Optional[dict]:
    """将 data.records 或 data.record 中的 fields JSON 字符串统一解析为 dict。"""
    if not isinstance(data, dict):
        return data
    if "records" in data:
        data = dict(data)
        data["records"] = [_parse_fields(r) for r in (data["records"] or [])]
    if "record" in data:
        data = dict(data)
        data["record"] = _parse_fields(data["record"] or {})
    return data


class _DbSheetClient(BaseClient):
    """WPS 365 V7 多维表 API 客户端。认证读取环境变量 wps_sid / WPS_SID / TMP_LX_UUID。"""

    _DBSHEET_REFERER = "https://365.kdocs.cn/woa/im/messages"

    def __init__(self, base_url: Optional[str] = None):
        base = base_url or os.environ.get("WPS_API_BASE") or "https://api.wps.cn"
        super().__init__(
            session_base=base,
            extra_headers={"Referer": self._DBSHEET_REFERER},
        )

    # ── 创建多维表文档 ─────────────────────────────────────────────────────────

    def _get_private_drive_id(self) -> str:
        resp = _wrap(
            self._s.get("/v7/drives", params={"allotee_type": "user", "page_size": 10})
        )
        if resp.get("code", -1) != 0:
            raise ValueError(resp.get("msg") or "获取云盘列表失败")
        items = (resp.get("data") or {}).get("items") or []
        for item in items:
            if item.get("name") == "我的企业文档":
                return item["id"]
        if items:
            return items[0]["id"]
        raise ValueError("未找到可用云盘")

    def create_file(self, file_name: str, folder_id: Optional[str] = None) -> dict:
        """POST /v7/drives/{drive_id}/files/{parent_id}/create
        在指定文件夹（默认根目录）创建多维表文档，云盘自动选取私有盘。
        folder_id: 目标文件夹的 file_id；不传则创建在根目录。
                   如需按名称查找文件夹 ID，请先调用 kdocs.find_folder_by_path()。
        返回 data.id（file_id）、data.link_id、data.link_url、data.name。
        创建成功后自动：① 删除服务端预置的默认字段（主字段保留，不可删）；
                        ② 删除预置的空白行；
                        ③ 在 data.primary_fields 中返回各数据表主字段信息及不可删原因。
        """
        try:
            did = self._get_private_drive_id()
            pid = folder_id if folder_id else "0"
            body = {
                "file_type": "file",
                "name": file_name,
                "on_name_conflict": "rename",
            }
            resp = _wrap(self._s.post(f"/v7/drives/{did}/files/{pid}/create", body=body))
            if resp.get("code", -1) == 0:
                d = resp.get("data") or {}
                fid = d.get("id", "")
                primary_fields_info: list = []
                # 删除服务端预置的默认字段（主字段不可删）和空白行
                try:
                    schema = self.get_schema(fid)
                    if schema.get("success"):
                        for sheet in (schema.get("data") or {}).get("sheets") or []:
                            sid = sheet["id"]
                            primary = sheet.get("primary_field_id", "")
                            # 删除非主字段
                            ids_to_del = [
                                f["id"]
                                for f in sheet.get("fields") or []
                                if f.get("id") and f["id"] != primary
                            ]
                            if ids_to_del:
                                self.delete_fields(fid, sid, ids_to_del)
                            # 删除预置空白行
                            self.delete_empty_records(fid, sid)
                            # 记录主字段信息
                            for f in sheet.get("fields") or []:
                                if f.get("id") == primary:
                                    primary_fields_info.append(
                                        {
                                            "sheet_id": sid,
                                            "sheet_name": sheet.get("name", ""),
                                            "field_id": f["id"],
                                            "field_name": f.get("name", ""),
                                            "field_type": f.get("field_type", ""),
                                            "undeletable_reason": "主字段（primary field）是数据表的唯一标识列，不支持删除。若主字段在业务中有对应用途，必须先调用 update_fields 将其重命名为目标字段名称，再继续后续操作，禁止跳过或新建替代。",
                                        }
                                    )
                except Exception:
                    pass
                d["primary_fields"] = primary_fields_info
                if d.get("link_url"):
                    d["link_url"] = _append_link_params(d["link_url"], d.get("name", file_name))
                return _make_result(
                    True,
                    data=d,
                    message=f"已创建：{d.get('name', file_name)}，file_id={fid}",
                )
            return _make_result(False, error=resp.get("msg", "未知错误"))
        except Exception as e:
            return _make_result(False, error=str(e))

    # ── Schema ────────────────────────────────────────────────────────────────

    def get_schema(self, file_id: str) -> dict:
        """GET /v7/dbsheet/{file_id}/schema
        返回 data.sheets（含 id/name/views/fields/records_count）。
        每个 field 注入 type（field_type 的别名，两者均可用）。
        """
        try:
            result = _ok(
                _wrap(self._s.get(f"/v7/dbsheet/{file_id}/schema")), "获取 Schema 成功"
            )
            if result["success"]:
                for sheet in (result.get("data") or {}).get("sheets") or []:
                    for field in sheet.get("fields") or []:
                        field.setdefault("type", field.get("field_type", ""))
            return result
        except Exception as e:
            return _make_result(False, error=str(e))

    def _kdocs_execute(self, file_id: str, command: str, param: dict) -> dict:
        """调用 kdocs core/execute 接口，返回解析后的 body 或错误结果。"""
        url = f"https://www.kdocs.cn/api/v3/office/file/{file_id}/core/execute"
        resp = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Origin": "http://www.kdocs.cn",
            },
            cookies={
                "wps_sid": self._sid,
                "weboffice_branch": "kdocs-amd-func-dbsheet-openapi-err",
            },
            json={"command": command, "param": param},
            timeout=30,
        )
        body = resp.json() if resp.content else {}
        if resp.status_code != 200 or body.get("result") != "ok":
            msg = body.get("msg") or body.get("message") or f"HTTP {resp.status_code}"
            detail = []
            if body.get("result"):
                detail.append(f"result={body.get('result')}")
            if body.get("errno") is not None:
                detail.append(f"errno={body.get('errno')}")
            if detail:
                msg = f"{msg} ({', '.join(detail)})"
            return _make_result(False, error=msg)
        return _make_result(True, data=body.get("detail") or {})

    def create_fields(self, file_id: str, sheet_id: int, fields: List[dict]) -> dict:
        """POST kdocs core/execute，command: http.db.createFields
        批量新建字段。每个字段至少含 name 和 type，选项字段可附带 items。

        常用 type：MultiLineText / SingleLineText / Number / Date / Checkbox /
                   SingleSelect / MultiSelect / Rating / Attachment / Member
        选项字段示例：{"name": "状态", "type": "SingleSelect",
                      "items": [{"value": "未开始"}, {"value": "进行中"}]}
        返回 data.fields：已创建字段列表（含 id/name/type）。
        """
        try:
            result = self._kdocs_execute(
                file_id,
                "http.db.createFields",
                {"sheetId": sheet_id, "fields": fields},
            )
            if not result["success"]:
                return result
            created = (result.get("data") or {}).get("fields") or []
            return _make_result(
                True, data={"fields": created}, message=f"已创建 {len(created)} 个字段"
            )
        except Exception as e:
            return _make_result(False, error=str(e))

    def delete_fields(self, file_id: str, sheet_id: int, field_ids: List[str]) -> dict:
        """POST kdocs core/execute，command: http.db.deleteFields
        按字段 id 批量删除字段。
        返回 data.fields：每项含 id 和 deleted（bool）。
        """
        try:
            result = self._kdocs_execute(
                file_id,
                "http.db.deleteFields",
                {"sheetId": sheet_id, "fields": [{"id": fid} for fid in field_ids]},
            )
            if not result["success"]:
                return result
            deleted = (result.get("data") or {}).get("fields") or []
            return _make_result(
                True, data={"fields": deleted}, message=f"已删除 {len(deleted)} 个字段"
            )
        except Exception as e:
            return _make_result(False, error=str(e))

    def update_fields(
        self,
        file_id: str,
        sheet_id: int,
        fields: List[dict],
        omit_failure: bool = False,
    ) -> dict:
        """POST kdocs core/execute，command: http.db.updateFields
        批量更新字段属性。每项必须含 id，其余属性（name/items/max 等）选填，只修改提供的部分。

        修改选项示例：
          {"id": "E", "items": [{"id": "B", "value": "未开始"},  # 修改已有选项
                                 {"value": "待定"}]}             # 新增选项
        返回 data.fields：更新后的字段列表。
        """
        try:
            result = self._kdocs_execute(
                file_id,
                "http.db.updateFields",
                {"sheetId": sheet_id, "fields": fields, "omitFailure": omit_failure},
            )
            if not result["success"]:
                return result
            updated = (result.get("data") or {}).get("fields") or []
            return _make_result(
                True, data={"fields": updated}, message=f"已更新 {len(updated)} 个字段"
            )
        except Exception as e:
            return _make_result(False, error=str(e))

    # ── 记录操作 ──────────────────────────────────────────────────────────────

    def list_records(
        self,
        file_id: str,
        sheet_id: int,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None,
        filter_body: Optional[dict] = None,
        view_id: Optional[str] = None,
        fields: Optional[List[str]] = None,
        max_records: Optional[int] = None,
        text_value: Optional[str] = None,
    ) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/{sheet_id}/records
        filter_body 格式：{"mode":"AND","criteria":[{"field":"字段名","operator":"Equals","values":["值"]}]}
        operator：Equals/NotEqu/Contains/Empty/NotEmpty/Greater/Less 等。
        API 筛选不生效时自动做客户端本地二次过滤兜底。
        """
        try:
            body: dict = {}
            if page_size is not None:
                body["page_size"] = min(1000, max(1, page_size))
            if page_token:
                body["page_token"] = page_token
            if filter_body is not None:
                body["filter"] = filter_body
            if view_id:
                body["view_id"] = view_id
            if fields is not None:
                body["fields"] = fields
            if max_records is not None:
                body["max_records"] = max_records
            if text_value:
                body["text_value"] = text_value
            resp = _wrap(
                self._s.post(
                    f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/records", body=body
                )
            )
            if resp.get("code", -1) == 0:
                return _make_result(
                    True, data=_parse_records(resp.get("data")), message="获取记录成功"
                )
            return _make_result(False, error=resp.get("msg", "未知错误"))
        except Exception as e:
            return _make_result(False, error=str(e))

    def get_record(self, file_id: str, sheet_id: int, record_id: str) -> dict:
        """GET /v7/dbsheet/{file_id}/sheets/{sheet_id}/records/{record_id}"""
        try:
            resp = _wrap(
                self._s.get(
                    f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/records/{record_id}"
                )
            )
            if resp.get("code", -1) == 0:
                return _make_result(
                    True, data=_parse_records(resp.get("data")), message="获取记录成功"
                )
            return _make_result(False, error=resp.get("msg") or "未知错误")
        except Exception as e:
            return _make_result(False, error=str(e))

    def search_records(
        self, file_id: str, sheet_id: int, record_ids: List[str]
    ) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/{sheet_id}/records/search（按 ID 精确查询）"""
        try:
            resp = _wrap(
                self._s.post(
                    f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/records/search",
                    body={"records": list(record_ids)},
                )
            )
            if resp.get("code", -1) == 0:
                return _make_result(
                    True, data=_parse_records(resp.get("data")), message="检索记录成功"
                )
            return _make_result(False, error=resp.get("msg") or "未知错误")
        except Exception as e:
            return _make_result(False, error=str(e))

    def create_records(self, file_id: str, sheet_id: int, records: List[dict]) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/{sheet_id}/records/batch_create
        records 支持直接传字段对象（{"名称":"任务A"}）或 {"fields_value":"..."} 格式，自动转换。
        """
        try:
            items = []
            for r in records:
                if isinstance(r, dict) and "fields_value" in r:
                    items.append(r)
                elif isinstance(r, dict):
                    items.append({"fields_value": json.dumps(r, ensure_ascii=False)})
                else:
                    items.append({"fields_value": str(r)})
            resp = _wrap(
                self._s.post(
                    f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/records/batch_create",
                    body={"records": items},
                )
            )
            if resp.get("code", -1) == 0:
                n = len((resp.get("data") or {}).get("records", []))
                return _make_result(
                    True,
                    data=_parse_records(resp.get("data")),
                    message=f"已创建 {n} 条记录",
                )
            return _make_result(False, error=resp.get("msg", "未知错误"))
        except Exception as e:
            return _make_result(False, error=str(e))

    def update_records(self, file_id: str, sheet_id: int, records: List[dict]) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/{sheet_id}/records/batch_update
        records 格式：[{"id":"记录ID","fields_value":{"字段名":新值}}]
        fields_value 传 dict 或 JSON 字符串均可，自动转换为接口所需的 JSON 字符串格式。
        """
        try:
            items = []
            for r in records:
                if (
                    isinstance(r, dict)
                    and "fields_value" in r
                    and isinstance(r["fields_value"], dict)
                ):
                    r = dict(r)
                    r["fields_value"] = json.dumps(
                        r["fields_value"], ensure_ascii=False
                    )
                items.append(r)
            resp = _wrap(
                self._s.post(
                    f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/records/batch_update",
                    body={"records": items},
                )
            )
            if resp.get("code", -1) == 0:
                n = len((resp.get("data") or {}).get("records", []))
                return _make_result(
                    True,
                    data=_parse_records(resp.get("data")),
                    message=f"已更新 {n} 条记录",
                )
            return _make_result(False, error=resp.get("msg", "未知错误"))
        except Exception as e:
            return _make_result(False, error=str(e))

    def delete_records(
        self, file_id: str, sheet_id: int, record_ids: List[str]
    ) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/{sheet_id}/records/batch_delete"""
        try:
            resp = _wrap(
                self._s.post(
                    f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/records/batch_delete",
                    body={"records": list(record_ids)},
                )
            )
            if resp.get("code", -1) == 0:
                return _make_result(
                    True,
                    data=_parse_records(resp.get("data")),
                    message=f"已删除 {len(record_ids)} 条记录",
                )
            return _make_result(False, error=resp.get("msg", "未知错误"))
        except Exception as e:
            return _make_result(False, error=str(e))

    def delete_empty_records(self, file_id: str, sheet_id: int) -> dict:
        """删除表中所有空记录（fields 为空或 {}），翻页遍历、每批 50 条删除。
        新建 .dbt 服务端预置约 18 行空记录，建议新建后立即调用。
        """
        try:
            empty_ids: List[str] = []
            page_token: Optional[str] = None
            while True:
                body: dict = {"page_size": 100}
                if page_token:
                    body["page_token"] = page_token
                resp = _wrap(
                    self._s.post(
                        f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/records", body=body
                    )
                )
                if resp.get("code", -1) != 0:
                    return _make_result(False, error=resp.get("msg", "获取记录失败"))
                data = resp.get("data") or {}
                for rec in data.get("records", []):
                    fs = rec.get("fields")
                    if isinstance(fs, str):
                        try:
                            empty = not json.loads(
                                fs
                            )  # 解析失败视为非空（跳过），避免误删
                        except (json.JSONDecodeError, ValueError):
                            empty = False
                    else:
                        empty = not _parse_fields(rec).get("fields")
                    if empty:
                        rid = rec.get("id")
                        if rid:
                            empty_ids.append(rid)
                page_token = data.get("page_token") or ""
                if not page_token:
                    break
            if not empty_ids:
                return _make_result(
                    True,
                    data={"deleted_count": 0, "record_ids": []},
                    message="未发现空记录",
                )
            deleted = 0
            for i in range(0, len(empty_ids), 50):
                chunk = empty_ids[i : i + 50]
                r = _wrap(
                    self._s.post(
                        f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/records/batch_delete",
                        body={"records": chunk},
                    )
                )
                if r.get("code", -1) != 0:
                    return _make_result(False, error=r.get("msg", "删除失败"))
                deleted += len(chunk)
            return _make_result(
                True,
                data={"deleted_count": deleted, "record_ids": empty_ids},
                message=f"已删除 {deleted} 条空记录",
            )
        except Exception as e:
            return _make_result(False, error=str(e))

    # ── 数据表管理 ────────────────────────────────────────────────────────────

    def create_sheet(
        self,
        file_id: str,
        name: Optional[str] = None,
        fields: Optional[List[dict]] = None,
        views: Optional[List[dict]] = None,
        position: Optional[dict] = None,
    ) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/create
        fields 每项：{"name":"字段名","field_type":"MultiLineText/Number/Date/SingleSelect/..."}
        返回 data.sheet（含 id、name）。
        """
        try:
            body: dict = {}
            if name is not None:
                body["name"] = name
            if fields is not None:
                body["fields"] = fields
            # API 强制要求至少传一个视图，否则返回 CoreExecutionFailed
            body["views"] = (
                views
                if views is not None
                else [{"name": "表格视图", "view_type": "Grid"}]
            )
            if position is not None:
                body["position"] = position
            resp = _wrap(
                self._s.post(f"/v7/dbsheet/{file_id}/sheets/create", body=body)
            )
            if resp.get("code", -1) == 0:
                sheet = (resp.get("data") or {}).get("sheet", {})
                return _make_result(
                    True,
                    data=resp.get("data"),
                    message=f"已创建数据表：{sheet.get('name', '')}",
                )
            return _make_result(False, error=resp.get("msg", "未知错误"))
        except Exception as e:
            return _make_result(False, error=str(e))

    def update_sheet(self, file_id: str, sheet_id: int, name: str) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/{sheet_id}/update"""
        try:
            return _ok(
                _wrap(
                    self._s.post(
                        f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/update",
                        body={"name": name},
                    )
                ),
                f"数据表名已更新为：{name}",
            )
        except Exception as e:
            return _make_result(False, error=str(e))

    def delete_sheet(self, file_id: str, sheet_id: int) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/{sheet_id}/delete"""
        try:
            resp = _wrap(
                self._s.post(f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/delete")
            )
            if resp.get("code", -1) == 0:
                return _make_result(True, message=f"数据表 {sheet_id} 已删除")
            return _make_result(False, error=resp.get("msg", "未知错误"))
        except Exception as e:
            return _make_result(False, error=str(e))

    # ── 视图管理 ──────────────────────────────────────────────────────────────

    def create_view(
        self,
        file_id: str,
        sheet_id: int,
        name: Optional[str] = None,
        view_type: str = "Grid",
    ) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/{sheet_id}/views
        view_type：Grid/Kanban/Gallery/Form/Gantt/Query/Calendar。
        返回 data.view（含 id/name/view_type）。
        """
        try:
            body: dict = {"view_type": view_type}
            if name is not None:
                body["name"] = name
            return _ok(
                _wrap(
                    self._s.post(
                        f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/views", body=body
                    )
                ),
                "视图创建成功",
            )
        except Exception as e:
            return _make_result(False, error=str(e))

    def delete_view(self, file_id: str, sheet_id: int, view_id: str) -> dict:
        """POST kdocs core/execute，command: http.db.deleteView
        删除指定视图。
        返回 data.view（通常含被删除视图 id）。
        """
        try:
            result = self._kdocs_execute(
                file_id,
                "http.db.deleteView",
                {"sheetId": sheet_id, "id": view_id},
            )
            if not result["success"]:
                return result
            return _make_result(
                True,
                data={
                    "view": (result.get("data") or {}).get("view") or {"id": view_id}
                },
                message=f"视图 {view_id} 已删除",
            )
        except Exception as e:
            return _make_result(False, error=str(e))

    def update_view(
        self,
        file_id: str,
        sheet_id: int,
        view_id: str,
        name: Optional[str] = None,
        prefer_id: bool = False,
        order_fields: Optional[List[str]] = None,
        fields_attribute: Optional[List[dict]] = None,
        height: Optional[int] = None,
        widths: Optional[List[dict]] = None,
        cover_field: Optional[str] = None,
        begin_field: Optional[str] = None,
        end_field: Optional[str] = None,
    ) -> dict:
        """POST kdocs core/execute，command: http.db.updateView
        更新视图属性（重命名、字段顺序、隐藏、宽高等）。

        参数说明：
          order_fields     : 字段名列表（非字段ID），需与表中所有字段一一对应
          fields_attribute : [{"field": "字段名", "hidden": True}] 控制显隐
          height           : Grid 视图记录行高
          widths           : [{"field": "字段名", "width": 1600}] Grid 字段列宽
          cover_field      : Kanban/Gallery 封面字段名
          begin_field      : Gantt 起始字段名
          end_field        : Gantt 结束字段名
          prefer_id        : True 时用字段 id 标识字段与选项，默认 False 用字段名

        返回 data.view（含 id/name/type）。
        """
        try:
            param: dict = {"sheetId": sheet_id, "id": view_id}
            if prefer_id:
                param["preferId"] = True
            if name is not None:
                param["name"] = name
            if order_fields is not None:
                param["orderFields"] = order_fields
            if fields_attribute is not None:
                param["fieldsAttribute"] = fields_attribute
            if height is not None:
                param["height"] = height
            if widths is not None:
                param["widths"] = widths
            if cover_field is not None:
                param["coverField"] = cover_field
            if begin_field is not None:
                param["beginField"] = begin_field
            if end_field is not None:
                param["endField"] = end_field
            result = self._kdocs_execute(file_id, "http.db.updateView", param)
            if not result["success"]:
                return result
            return _make_result(
                True,
                data={
                    "view": (result.get("data") or {}).get("view") or {"id": view_id}
                },
                message=f"视图 {view_id} 已更新",
            )
        except Exception as e:
            return _make_result(False, error=str(e))

    def get_form_meta(self, file_id: str, sheet_id: int, view_id: str) -> dict:
        """GET /v7/dbsheet/{file_id}/sheets/{sheet_id}/forms/{view_id}/meta"""
        try:
            return _ok(
                _wrap(
                    self._s.get(
                        f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/forms/{view_id}/meta"
                    )
                ),
                "获取表单元数据成功",
            )
        except Exception as e:
            return _make_result(False, error=str(e))

    def update_form_meta(
        self,
        file_id: str,
        sheet_id: int,
        view_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """POST /v7/dbsheet/{file_id}/sheets/{sheet_id}/forms/{view_id}/meta"""
        try:
            body: dict = {}
            if name is not None:
                body["name"] = name
            if description is not None:
                body["description"] = description
            if not body:
                return _make_result(False, error="请至少提供 name 或 description")
            return _ok(
                _wrap(
                    self._s.post(
                        f"/v7/dbsheet/{file_id}/sheets/{sheet_id}/forms/{view_id}/meta",
                        body=body,
                    )
                ),
                "表单元数据已更新",
            )
        except Exception as e:
            return _make_result(False, error=str(e))


# ── 模块级 API（对外仅暴露函数，内部单例）─────────────────────────

_client: Optional[_DbSheetClient] = None


def _get_client() -> _DbSheetClient:
    global _client
    if _client is None:
        _client = _DbSheetClient()
    return _client


def create_file(file_name: str, folder_id: Optional[str] = None) -> dict:
    return _get_client().create_file(file_name, folder_id=folder_id)


def get_schema(file_id: str) -> dict:
    return _get_client().get_schema(file_id)


def create_fields(file_id: str, sheet_id: int, fields: List[dict]) -> dict:
    return _get_client().create_fields(file_id, sheet_id, fields)


def delete_fields(file_id: str, sheet_id: int, field_ids: List[str]) -> dict:
    return _get_client().delete_fields(file_id, sheet_id, field_ids)


def update_fields(
    file_id: str,
    sheet_id: int,
    fields: List[dict],
    omit_failure: bool = False,
) -> dict:
    return _get_client().update_fields(
        file_id, sheet_id, fields, omit_failure=omit_failure
    )


def list_records(
    file_id: str,
    sheet_id: int,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None,
    filter_body: Optional[dict] = None,
    view_id: Optional[str] = None,
    fields: Optional[List[str]] = None,
    max_records: Optional[int] = None,
    text_value: Optional[str] = None,
) -> dict:
    return _get_client().list_records(
        file_id,
        sheet_id,
        page_size=page_size,
        page_token=page_token,
        filter_body=filter_body,
        view_id=view_id,
        fields=fields,
        max_records=max_records,
        text_value=text_value,
    )


def get_record(file_id: str, sheet_id: int, record_id: str) -> dict:
    return _get_client().get_record(file_id, sheet_id, record_id)


def search_records(file_id: str, sheet_id: int, record_ids: List[str]) -> dict:
    return _get_client().search_records(file_id, sheet_id, record_ids)


def create_records(file_id: str, sheet_id: int, records: List[dict]) -> dict:
    return _get_client().create_records(file_id, sheet_id, records)


def update_records(file_id: str, sheet_id: int, records: List[dict]) -> dict:
    return _get_client().update_records(file_id, sheet_id, records)


def delete_records(file_id: str, sheet_id: int, record_ids: List[str]) -> dict:
    return _get_client().delete_records(file_id, sheet_id, record_ids)


def delete_empty_records(file_id: str, sheet_id: int) -> dict:
    return _get_client().delete_empty_records(file_id, sheet_id)


def create_sheet(
    file_id: str,
    name: Optional[str] = None,
    fields: Optional[List[dict]] = None,
    views: Optional[List[dict]] = None,
    position: Optional[dict] = None,
) -> dict:
    return _get_client().create_sheet(
        file_id, name=name, fields=fields, views=views, position=position
    )


def update_sheet(file_id: str, sheet_id: int, name: str) -> dict:
    return _get_client().update_sheet(file_id, sheet_id, name)


def delete_sheet(file_id: str, sheet_id: int) -> dict:
    return _get_client().delete_sheet(file_id, sheet_id)


def create_view(
    file_id: str,
    sheet_id: int,
    name: Optional[str] = None,
    view_type: str = "Grid",
) -> dict:
    return _get_client().create_view(file_id, sheet_id, name=name, view_type=view_type)


def delete_view(file_id: str, sheet_id: int, view_id: str) -> dict:
    return _get_client().delete_view(file_id, sheet_id, view_id)


def update_view(
    file_id: str,
    sheet_id: int,
    view_id: str,
    name: Optional[str] = None,
    prefer_id: bool = False,
    order_fields: Optional[List[str]] = None,
    fields_attribute: Optional[List[dict]] = None,
    height: Optional[int] = None,
    widths: Optional[List[dict]] = None,
    cover_field: Optional[str] = None,
    begin_field: Optional[str] = None,
    end_field: Optional[str] = None,
) -> dict:
    return _get_client().update_view(
        file_id,
        sheet_id,
        view_id,
        name=name,
        prefer_id=prefer_id,
        order_fields=order_fields,
        fields_attribute=fields_attribute,
        height=height,
        widths=widths,
        cover_field=cover_field,
        begin_field=begin_field,
        end_field=end_field,
    )


def get_form_meta(file_id: str, sheet_id: int, view_id: str) -> dict:
    return _get_client().get_form_meta(file_id, sheet_id, view_id)


def update_form_meta(
    file_id: str,
    sheet_id: int,
    view_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    return _get_client().update_form_meta(
        file_id, sheet_id, view_id, name=name, description=description
    )


__all__ = [
    "create_file",
    "get_schema",
    "create_fields",
    "delete_fields",
    "update_fields",
    "list_records",
    "get_record",
    "search_records",
    "create_records",
    "update_records",
    "delete_records",
    "delete_empty_records",
    "create_sheet",
    "update_sheet",
    "delete_sheet",
    "create_view",
    "delete_view",
    "update_view",
    "get_form_meta",
    "update_form_meta",
]
