---
name: wps_docs
description: "WPS灵犀封装了WPS云文档能力，包含四大模块：\n- 云文档基础能力：文件信息查询、上传、下载\n- ET：在云端创建和编辑在线表格（.xlsx）与智能表格（.ksheet），两者共用同一套 API\n- DbSheet（多维表）：包括查询Schema、读写记录、管理字段与各种视图\n- AP(智能文档)：创建和修改智能文档\n若用户指定 *.kdocs.cn/l/xxxx 这类云文档链接，相关操作均通过本技能处理。"
---

# WPS 云文档 SKILL

### 常见链接格式

https://365.kdocs.cn/l/{file_id}?lingxi_file_name={file_name}

## 场景路由

收到云文档链接或 file_id 后，先用 `kdocs.get_file_info(file_id)` 获取文件信息，根据文件类型分发：

| 文件类型 | 文件后缀        | 使用模块                         |
| -------- | --------------- | -------------------------------- |
| 智能文档 | .otl | AP（导出 Markdown / 块操作） |
| 表格     | .xlsx           | ET                               |
| 智能表格 | .ksheet         | ET（同 .xlsx）                   |
| 多维表   | .dbt            | DbSheet                          |
| 其他     | .docx / .pdf 等 | 云文档基础能力（下载到本地处理） |

**规则**：除非用户明确要求下载到本地，对云文档的操作都在云端进行。禁止将云文档下载到本地后用 openpyxl / pandas 等python库处理再上传——这会丢失云端格式、公式、图表和协作状态。必须使用对应模块（ET / DbSheet）的云端 API 直接操作。

---

## 一、云文档基础能力

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'scripts'))
import kdocs
```

### kdocs.get_file_info(file_id)

获取云文档文件信息。

| 参数    | 说明   |
|---------|--------|
| file_id | 文件ID |

**返回值**

```python
{
    "success": True/False,
    "data": {
        "file_id": "文件ID",
        "name": "文件名（含后缀）",
        "link_url": "云文档访问链接",
        "size": "1.23 MB",
        "ctime": "创建时间(ISO 8601)",
        "created_by": {"id": "创建者ID", "name": "创建者名称"}
    },
    "message": "成功获取文件信息: xxx.ksheet"
}
```

**调用示例**

```python
result = kdocs.get_file_info(file_id="xxx")
print(result)
```

### kdocs.download_file(file_id, save_dir=None)

下载云文档文件到本地。

| 参数     | 说明         |
|----------|--------------|
| file_id  | 文件ID       |
| save_dir | 本地保存目录 |

**返回值**

```python
{
    "success": True/False,
    "data": {
        "file_id": "文件ID",
        "name": "云端文件名",
        "link_url": "云文档访问链接",
        "size": "1.23 MB",
        "ctime": "创建时间(ISO 8601)",
        "created_by": {"id": "创建者ID", "name": "创建者名称"}
    },
    "message": "下载成功，保存路径为: /path/to/file.xlsx"
}
```

**调用示例**

```python
result = kdocs.download_file(file_id="xxx", save_dir="workspace/output")
print(result)
```

### kdocs.upload_file(file_path, folder_id=None)

上传本地文件到云文档。

**注意**： 直接上传，无需提前检查是否存在同名文件。

| 参数      | 说明 |
| file_path | 本地文件路径。|
| folder_id | 目标文件夹的 `file_id`；不传则上传到根目录。 |

**返回值**

```python
{
    "success": True/False,
    "data": {
        "file_id": "文件ID",
        "name": "文件名",
        "link_url": "云文档访问链接",
        "size": "1.23 MB",
        "ctime": "创建时间(ISO 8601)",
        "created_by": {"id": "创建者ID", "name": "创建者名称"}
    },
    "message": "上传成功，云文档文件名为: xxx.docx，链接为: https://..."
}
```

**调用示例**

```python
# 上传到根目录
result = kdocs.upload_file("/tmp/report.docx")
print(result)
```

### kdocs.list_latest_items(page_size=20, page_token=None)

获取最近访问/编辑的文件列表。

| 参数       | 说明                          |
|------------|-------------------------------|
| page_size  | 每页条数，最大 500，默认 20   |
| page_token | 翻页 token，首次不传          |

**返回值**

```python
{
    "success": True/False,
    "data": {
        "files": [
            {"file_id": "文件ID", "line": "文件名（大小，创建时间） 云文档链接"}
        ],
        "next_page_token": "翻页token（无更多数据时为空）"
    },
    "message": "获取到 20 条最近记录"
}
```

**调用示例**

```python
result = kdocs.list_latest_items()
print(result)
```

### kdocs.list_folder_files(folder_id, page_token=None, filter_type=None)

获取文件夹下的子文件列表。
**注意**：文件夹本质上也是特殊的 file，拥有 `file_id`，可通过本接口列举其中所有文件。

| 参数 | 说明 |
|------|------|
| folder_id | 文件夹的 `file_id`（**必填**） |
| page_token | 翻页 token，首次不传，后续传上一次返回的 `next_page_token` |
| filter_type | 只返回指定类型：`'file'` / `'folder'` / `'shortcut'` |

**返回值**

```python
{
    "success": True/False,
    "data": {
        "items": [
            {
                "file_id": "文件ID（type=folder 时可再次传入本函数递归遍历）",
                "name": "文件名",
                "type": "file/folder/shortcut",
                "parent_id": "父目录ID",
                "link_url": "云文档访问链接",
                "ctime": "创建时间(ISO 8601)",
                "mtime": "修改时间(ISO 8601)"
            }
        ],
        "next_page_token": "翻页token（无更多数据时为空）"
    },
    "message": "获取到 N 个文件"
}
```

**注意**：返回的 `file_id` 若对应 `type=folder` 的子文件夹，可再次传入本函数实现递归遍历

**调用示例**

```python
result = kdocs.list_folder_files(folder_id="xxx")
print(result)
```

### kdocs.create_folder(folder_name, parent_id="0")

在云端创建文件夹。仅支持「我的云文档」。

| 参数        | 说明                                                       |
|-------------|----------------------------------------------------------|
| folder_name | 文件夹名称                                                |
| parent_id   | 父文件夹 ID，默认 `"0"` 表示根目录                         |

**返回值**

返回 `dict`：`{"success": True, "data": "<folder_id>", ...}` 或 `{"success": False, "error": "...", ...}`。

**调用示例**

```python
result = kdocs.create_folder("项目A")
if result["success"]:
    folder_id = result["data"]

# 在已有文件夹下创建子文件夹
result = kdocs.create_folder("子目录", parent_id=folder_id)
```

### kdocs.find_folder_by_path(folder_path)

按名称或路径查找文件夹。
**注意**：需要在指定文件夹下创建/上传文件时，先调用本函数获取 `file_id`，再传给对应接口的 `folder_id` / `parent_id` 参数。

**错误处理**：若输出"未找到文件夹"，告知用户该文件夹未找到，请用户确认文件夹名称是否正确或者是否需要创建文件夹。

| 参数        | 说明                                                                               |
|-------------|------------------------------------------------------------------------------------|
| folder_path | 文件夹名称或多层路径（`/` 分隔，如 `"工作/项目A"`）         |


**返回值**

返回文件夹的 `file_id` 字符串；路径不存在时抛出 `ValueError`。

**调用示例**

```python

# 多层路径
folder_id = kdocs.find_folder_by_path("工作/项目A")
print(folder_id)
```

### 错误处理

| 错误               | 原因                 | 解决方案              |
| ------------------ | -------------------- | --------------------- |
| 获取下载地址失败 | 文件无权下载或不存在 | 检查 file_id 是否合法 |

---

## 二、ET（在线表格 / 智能表格）

使用前必须先读取完整文档：

```
{skill_path}/wps_docs/et/et_guide.md
```
读取示例：
```python
import sys, os
print(open(os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'et', 'et_guide.md'), encoding="utf-8").read())
```

涵盖能力：创建和编辑在线表格（.xlsx）或智能表格（.ksheet），两种文件类型共用同一套 API。包括数据读写、公式、格式美化、图表、条件格式、数据透视表、图片插入等功能。

---

## 三、DbSheet（多维表）

DbSheet 功能作为本技能的子模块，使用前必须先读取完整文档，完整文档请读取：

```
{skill_path}/wps_docs/dbsheet/dbsheet_guide.md
```

加载模块：

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'dbsheet','scripts'))
import dbsheet
```

涵盖能力：查询 Schema、列举/检索/创建/更新/删除记录、管理字段与各种视图。使用前请先读取上方文档。

---

## 四、AP（智能文档）

AP 功能作为本技能的子模块，使用前必须先读取完整文档：

```
{skill_path}/wps_docs/ap/ap_guide.md
```

加载模块：

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'ap','scripts'))
import ap
```

涵盖能力：导出智能文档为 Markdown、创建智能文档、查询文档块结构、插入/删除/更新块内容。使用前请先读取上方文档。

---

## 云文档交付规范

凡是通过本技能创建或上传云文档后，向用户交付结果时，**必须**使用以下格式：

```
[`文件名`](link_url)
```

- `link_url` 取 API 返回值中的 `link_url` 字段，该字段已包含 `lingxi_file_name` 参数，**直接使用，禁止截断或替换为裸链接**
- 文件名原样写在反引号内

**示例：**

```
[`明月.otl`](https://www.kdocs.cn/l/ckR5jy8fj2Hw?lingxi_file_name=明月.otl)
[`5月开支详情.dbt`](https://www.kdocs.cn/l/cpc5ijZVRqX0?lingxi_file_name=5月开支详情.dbt)
[`你好.pptx`](https://www.kdocs.cn/l/ciyDvJZIdLfB?lingxi_file_name=你好.pptx)
```
