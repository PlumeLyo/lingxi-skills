---
name: dbsheet
description: "WPS 多维表（DbSheet）的操作与管理能力。涵盖获取 Schema、列举/检索/创建/更新/删除记录、数据表管理、视图管理、表单元数据等功能。"
---

# DbSheet SKILL

## 加载方式

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('skill_path'), 'dbsheet', 'script'))
import dbsheet
```

**通用参数说明**（以下各方法不再重复）

| 参数 | 类型 | 说明 |
|------|------|------|
| `file_id` | str | 多维表文件 ID，可从链接 `https://365.kdocs.cn/l/{file_id}` 提取 |
| `sheet_id` | int | 数据表 ID（整数），从 `get_schema()` 结果获取；新建 `.dbt` 多维表文件后第一张表的 ID 固定为 `1` |
| `record_id` | str | 记录 ID |
| `record_ids` | list[str] | 记录 ID 列表 |
| `view_id` | str | 视图 ID，从 `get_schema()` 结果的 views 列表获取 |
| `page_size` | int | 每页返回记录数，`None` 使用服务端默认值（最大 1000） |
| `page_token` | str | 翻页 token，传上一次返回的 `data.page_token`，`None` 或空串表示从第一页开始 |

**所有方法返回格式统一**

```python
# 成功
{"success": True, "data": {...}, "message": "操作成功描述"}
# 失败
{"success": False, "error": "错误描述"}
```

**`data` 字段结构说明**

| 方法 | `data` 内容 |
|------|------------|
| `get_schema` | `{"sheets": [{"id": 1, "name": "表名", "fields": [...], "views": [...], "records_count": 10}]}` |
| `list_records` / `search_records` / `create_records` / `update_records` / `delete_records` | `{"records": [...], "page_token": ""}` |
| `get_record` | `{"record": {"id": "rec_xxx", "fields": "{...}"}}` |
| `create_sheet` | `{"sheet": {"id": 2, "name": "表名", "fields": [...], "views": [...]}}` |
| `create_view` | `{"view": {"id": "V", "name": "视图名", "view_type": "Grid"}}` |
| `delete_empty_records` | `{"deleted_count": 18, "record_ids": [...]}` |
| `create_file` | `{"id": "file_id", "link_id": "...", "link_url": "...", "name": "文件名"}` |

> `fields` 已由客户端自动解析为 dict，可直接用 `rec["fields"]["字段名"]` 取值。

---

## 创建多维表文档

### `dbsheet.create_file(file_name)`

在云盘「我的文档」根目录新建文件，创建多维表文档（`.dbt`）时使用。

| 参数 | 说明 |
|------|------|
| `file_name` | 文件名，如 `"项目任务.dbt"`（多维表）|

**返回值**：`data.id`（file_id）、`data.link_id`（用于 im_send）、`data.link_url`、`data.name`、`data.primary_fields`（各数据表的主字段信息）

> **主字段说明**：创建后服务端预置了默认主字段（不可删除）。
> ⚠️ **必须复用主字段**：若业务中有字段需要新增，**必须先调用 `update_fields` 将主字段重命名为该字段名称**，再进行后续操作。禁止跳过主字段、另行新建字段替代。

# data.primary_fields 示例：
# [{"sheet_id": 1, "field_id": "B", "field_name": "名称", "field_type": "MultiLineText", "undeletable_reason": "主字段（primary field）是数据表的唯一标识列，不支持删除。若主字段在业务中有对应用途，必须先调用 update_fields 将其重命名为目标字段名称，再继续后续操作，禁止跳过或新建替代。"}]

```python
result = dbsheet.create_file("项目任务跟踪.dbt")
print(result)
```

---

## Schema（表结构）

### `dbsheet.get_schema(file_id)`

获取多维表所有数据表及字段结构（包括查询视图）。

**返回值**：`data.sheets` 列表，每项含 `id`（sheet_id）、`name`、`views`、`fields`、`records_count`

每个 `field` 含：`name`、`field_type`（也可用 `type`，两者等价）、`id`


```python
result = dbsheet.get_schema(file_id="abc123")
print(result)
sheet = result["data"]["sheets"][0]
sheet_id = sheet["id"]
# field['type'] 和 field['field_type'] 等价
second_col = sheet["fields"][1]  # 第2列
```

### `dbsheet.create_fields(file_id, sheet_id, fields)`

批量新建字段。`fields` 为字段描述数组，每项必须含 `name` 和 `type`。

**fields 每项字段说明**

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 字段名 |
| `type` | ✅ | 字段类型，见下方类型列表 |
| `items` | 选填 | `SingleSelect`/`MultipleSelect` 的选项数组，每项含 `value` |
| `max` | 选填 | `Rating` 的最大星级（默认 5） |

**常用 `type`**：`MultiLineText` / `SingleLineText` / `Number` / `Date` / `Checkbox` / `SingleSelect` / `MultipleSelect` / `Rating` / `Attachment` / `Member`

**返回值**：`data.fields`，含 `id`/`name`/`type`（选项字段含 `items`）

```python
result = dbsheet.create_fields(
    file_id="abc123", sheet_id=1,
    fields=[
        {"name": "备注", "type": "MultiLineText"},
        {"name": "状态", "type": "SingleSelect",
         "items": [{"value": "未开始"}, {"value": "进行中"}, {"value": "已完成"}]},
        {"name": "评分", "type": "Rating", "max": 5},
    ]
)
print(result)
```

### `dbsheet.delete_fields(file_id, sheet_id, field_ids)`

按字段 `id` 批量删除字段。`field_ids` 为字段 id 字符串列表（字段 id 可从 `get_schema`获取）。

**返回值**：`data.fields`，每项含 `id` 和 `deleted`（bool）

```python
result = dbsheet.delete_fields(file_id="abc123", sheet_id=1, field_ids=["J", "K"])
print(result)
```

### `dbsheet.update_fields(file_id, sheet_id, fields, omit_failure=False)`

批量更新字段属性。`fields` 每项必须含 `id`，其余属性选填，只修改提供的部分（同 `create_fields` 字段属性，均变为可选）。

**选项字段 `items` 更新规则**：
- 带 `id` → 修改已有选项
- 不带 `id` → 新增选项

**返回值**：`data.fields`，更新后的字段列表

```python
result = dbsheet.update_fields(
    file_id="abc123", sheet_id=1,
    fields=[
        {"id": "E", "name": "新字段名",
         "items": [{"id": "B", "value": "未开始"},   # 修改已有选项
                   {"value": "待定"},                  # 新增选项
                   {"id": "D", "value": "已完成"}]},   # 修改已有选项
        {"id": "C", "max": 4},
    ]
)
print(result)
```

---

## 记录操作

### `dbsheet.list_records(file_id, sheet_id, **可选参数)`

列举多维表记录（支持分页与条件筛选）

| 参数 | 类型 | 默认行为（None） | 说明 |
|------|------|----------|------|
| `filter_body` | dict | 返回所有记录 | 筛选条件，见下方格式说明 |
| `view_id` | str | 返回全表记录 | 指定视图 ID，仅返回该视图可见的记录 |
| `fields` | list[str] | 返回所有字段 | 指定返回的字段名或字段 id 列表，如 `["名称", "状态"]` |
| `page_size` | int | 服务端默认（最大 1000） | 每页返回记录数 |
| `page_token` | str | 从第一页开始 | 翻页 token，传上一次返回的 `data.page_token` |
| `max_records` | int | 不限制 | 服务端限制最多返回的记录总数 |
| `text_value` | str | 使用默认格式 | 字段值返回格式：`original`原始值 / `text`文本 / `compound`两者兼有 |

**filter_body 格式**

```python
{
    "mode": "AND",   # AND 或 OR
    "criteria": [
        {"field": "状态", "operator": "Equals",   "values": ["进行中"]},
        {"field": "名称", "operator": "Contains",  "values": ["测试"]},
        {"field": "截止", "operator": "Empty"},
    ]
}
# operator 可选：Equals / NotEqu / Contains / Empty / NotEmpty / Greater / Less 等
```

**返回值**：`data.records`（含 `id`、`fields`）、`data.page_token`（为空则无更多数据）

```python
result = dbsheet.list_records(file_id="abc123", sheet_id=1,
    filter_body={"mode": "AND", "criteria": [{"field": "状态", "operator": "Equals", "values": ["进行中"]}]})
print(result)
for rec in result["data"]["records"]:
    print(rec["id"], rec["fields"]["状态"])  # fields 已自动解析为 dict，直接取值
```

---

### `dbsheet.get_record(file_id, sheet_id, record_id)`

获取单条记录详情。**返回值**：`data.record`（含 `id`、`fields`）

```python
result = dbsheet.get_record(file_id="abc123", sheet_id=1, record_id="rec_xxx")
print(result)
```

---

### `dbsheet.search_records(file_id, sheet_id, record_ids)`

按 ID 列表批量检索记录（精确查询，非条件筛选）。**返回值**：`data.records`

```python
result = dbsheet.search_records(file_id="abc123", sheet_id=1, record_ids=["rec_1", "rec_2"])
print(result)
```

---

### `dbsheet.create_records(file_id, sheet_id, records)`

批量创建记录。`records` 直接传字段对象列表，如 `[{"名称": "任务A", "状态": "进行中"}]`，自动转换为接口格式。
**返回值**：`data.records`（含 `id`）


```python
result = dbsheet.create_records(file_id="abc123", sheet_id=1,
    records=[{"名称": "需求评审", "优先级": "高", "状态": "待开始"}])
print(result)
```

---

### `dbsheet.update_records(file_id, sheet_id, records)`

批量更新记录。`records` 格式：`[{"id": "记录ID", "fields_value": {"字段名": 新值}}]`
**返回值**：`data.records`

```python
result = dbsheet.update_records(file_id="abc123", sheet_id=1,
    records=[{"id": "rec_xxx", "fields_value": {"状态": "已完成"}}])
print(result)
```

---

### `dbsheet.delete_records(file_id, sheet_id, record_ids)`

批量删除记录。**返回值**：`data.records`（含 `deleted` 状态）

```python
result = dbsheet.delete_records(file_id="abc123", sheet_id=1, record_ids=["rec_1", "rec_2"])
print(result)
```

---

### `dbsheet.delete_empty_records(file_id, sheet_id)`

删除表中所有空记录（`fields` 为空或 `{}`）。翻页遍历、分批删除（每批 50 条）。

**返回值**：`data.deleted_count`、`data.record_ids`

```python
result = dbsheet.delete_empty_records(file_id="abc123", sheet_id=1)
print(result)
```

---

## 数据表管理

### `dbsheet.create_sheet(file_id, name="", fields=[], views=[], position={})`

创建数据表。

| 参数 | 默认行为（None） | 说明 |
|------|----------|------|
| `name` | 服务端自动命名 | 数据表名称 |
| `fields` | 使用服务端默认字段 | 字段列表，每项格式 `{"name": "字段名", "field_type": "类型"}`，`field_type` 可选：`MultiLineText` / `Number` / `Date` / `SingleSelect` / `MultipleSelect` / `Checkbox` / `Url` |
| `views` | 自动补一个默认表格视图 | 视图列表（API 强制至少一个视图，不传时自动处理） |
| `position` | 追加到末尾 | 插入位置：`{"before_sheet_id": id}` 或 `{"after_sheet_id": id}` |

**返回值**：`data.sheet`（含 `id`、`name`）

```python
result = dbsheet.create_sheet(file_id="abc123", name="任务清单",
    fields=[{"name": "名称", "field_type": "MultiLineText"}, {"name": "状态", "field_type": "SingleSelect"}])
print(result)
sheet_id = result["data"]["sheet"]["id"]
```

---

### `dbsheet.update_sheet(file_id, sheet_id, name)`

重命名数据表。

```python
result = dbsheet.update_sheet(file_id="abc123", sheet_id=1, name="新表名")
print(result)
```

---

### `dbsheet.delete_sheet(file_id, sheet_id)`

删除数据表。

```python
result = dbsheet.delete_sheet(file_id="abc123", sheet_id=2)
print(result)
```

---

## 视图

### `dbsheet.create_view(file_id, sheet_id, name="视图名", view_type="Grid")`

创建视图。`view_type`：`Grid`表格视图 / `Kanban`看板视图 / `Gallery`画册视图 / `Form`表单视图 / `Gantt`甘特视图 / `Query`查询视图 / `Calendar`日历视图
**返回值**：`data.view`（含 `id`、`name`、`view_type`）

```python
result = dbsheet.create_view(file_id="abc123", sheet_id=1, name="看板视图", view_type="Kanban")
print(result)
```

> **创建甘特图视图需要两步**：`create_view` 仅完成视图创建，**必须紧接着调用 `update_view` 设置 `begin_field` 和 `end_field`**，否则甘特图无法正常显示时间轴。
> ⚠️ `begin_field` 和 `end_field`两个字段名须从 `get_schema` 返回的字段中按语义选取（field_type 的类型为 `Date`），不可照抄示例。
>
> ```python
> # 第一步：创建甘特图视图
> result = dbsheet.create_view(file_id="abc123", sheet_id=1, name="甘特图", view_type="Gantt")
> print(result)
> # 第二步：配置起始和结束日期字段（必须执行）
> if result.get("success"):
>     view_id = result["data"]["view"]["id"]
>     update_view_result = dbsheet.update_view(
>         file_id="abc123", sheet_id=1, view_id=view_id,
>         begin_field="<起始日期字段名>",  # 从 get_schema 结果中选取
>         end_field="<结束日期字段名>",    # 从 get_schema 结果中选取
>     )
>     print(update_view_result)
> ```

---

### `dbsheet.delete_view(file_id, sheet_id, view_id)`

**返回值**：`data.view`（通常含 `id`）

```python
result = dbsheet.delete_view(file_id="abc123", sheet_id=1, view_id="I")
print(result)
```

---

### `dbsheet.update_view(file_id, sheet_id, view_id, **可选参数)`

| 可选参数 | 适用视图 | 说明 |
|------|------|------|
| `name` | 全部 | 视图重命名，传入新名称字符串 |
| `prefer_id` | 全部 | 控制下列参数中字段的标识方式：`False`（默认）用字段名，`True` 用字段 id。字段名含特殊字符或存在重名时建议开启，开启后其余参数里的字段标识须同步改为 id |
| `order_fields` | 全部 | 调整视图列顺序。传入字段**名**列表，**必须包含该表的全部字段**，不可只传部分，列表顺序即最终列顺序。示例：`["名称", "状态", "截止日期", "负责人"]` |
| `fields_attribute` | 全部 | 控制字段在视图中的显示/隐藏。每项格式 `{"field": "字段名", "hidden": True/False}`，只需传要修改的字段，其余字段保持原状。示例：`[{"field": "备注", "hidden": True}]` |
| `begin_field` | Gantt | 甘特图时间轴**起始日期**对应的字段名，必须是 `Date` 类型字段，不设置则时间轴无法显示 |
| `end_field` | Gantt | 甘特图时间轴**结束日期**对应的字段名，必须是 `Date` 类型字段，不设置则时间轴无法显示 |

**返回值**：`data.view`（含 `id`/`name`/`type`）

```python
# 重命名 + 调整字段顺序 + 隐藏某列
result = dbsheet.update_view(
    file_id="abc123", sheet_id=1, view_id="I",
    name="新视图名",
    order_fields=["B", "D", "F", "E", "C"],
    fields_attribute=[{"field": "D", "hidden": True}],
    widths=[{"field": "B", "width": 1600}],
)
print(result)
```

---

### `dbsheet.get_form_meta(file_id, sheet_id, view_id)`

获取表单视图元数据。`view_id` 从 `get_schema()` 的 views 中筛选 `type == "Form"` 的项获取。

```python
result = dbsheet.get_form_meta(file_id="abc123", sheet_id=1, view_id="view_xxx")
print(result)
```

---

### `dbsheet.update_form_meta(file_id, sheet_id, view_id, name=None, description=None)`

更新表单视图名称/描述，name 和 description至少提供一个。

```python
result = dbsheet.update_form_meta(file_id="abc123", sheet_id=1, view_id="view_xxx",
    name="需求收集表", description="请填写你的需求")
print(result)
```

---

## 类型参考

**字段类型（Field Type）**

普通类型：`MultiLineText`多行文本 · `Date`日期 · `Time`时间 · `Number`数值 · `Currency`货币 · `Percentage`百分比 · `ID`身份证 · `Phone`电话 · `Email`电子邮箱 · `Url`超链接 · `Checkbox`复选框 · `SingleSelect`单选项 · `MultipleSelect`多选项（旧文档也写作`MultiSelect`）· `Rating`等级 · `Complete`进度条 · `Contact`联系人 · `Attachment`附件 · `Link`关联 · `Note`富文本 · `Address`地址 · `Cascade`级联 · `Department`部门

自动类型（只读/系统生成）：`AutoNumber`编号 · `CreatedBy`创建者 · `CreatedTime`创建时间 · `LastModifiedBy`最后修改者 · `LastModifiedTime`最后修改时间 · `Formula`公式 · `Lookup`引用 · `BarCode`条码 · `SearchLookup`查找引用 · `Button`按钮 · `OneWayLink`单向关联

**视图类型（View Type）**

`Grid`表格视图 · `Kanban`看板视图 · `Gallery`画册视图 · `Form`表单视图 · `Gantt`甘特视图 · `Query`查询视图 · `Calendar`日历视图

---

## 错误处理

| 常见错误 | 原因 | 解决方案 |
|----------|------|----------|
| 字段未找到 | 字段名不匹配 | 先用 `get_schema()` 确认字段名，区分大小写 |
| 数据类型错误 | 值类型不符 | 数字传 int/float，日期传字符串如 `"2026-03-14"` |
| 权限不足 | 无读写权限 | 确认 `file_id` 正确且账号有访问权限 |
| SingleSelect 保存为空 | 选项值不在预定义列表 | 先 `get_schema()` 确认选项，值须完全匹配 |
