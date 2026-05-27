---
name: ap
description: "智能文档相关能力。当需要对智能文档（.otl）进行创建、写入、查询/插入/删除/更新块等操作时，使用本技能。"
---

# AP SKILL

## 快速开始

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'ap','scripts'))
import ap
```


## 块类型（Block Type）说明

智能文档内容由块（block）树组成。以下是常见块类型。

| type | 含义 | 备注 |
|------|------|------|
| doc | 文档根节点 | 顶层容器，id 固定为 "doc"，其 content 即文档所有顶层块 |
| title | 文档大标题 | 每篇文档唯一，位于 doc.content[0] |
| heading | 标题块 | attrs.level 表示层级（1~6） |
| paragraph | 段落 | 最常用的文本块；列表（无序/有序/任务）也是 paragraph，通过 attrs.listAttrs 区分 |
| picture | 图片块 | attrs.sourceKey 为附件 ID |
| table | 表格 | content 为 tableRow 数组 |
| tableRow | 表格行 | content 为 tableCell 数组 |
| tableCell | 表格单元格 | content 为段落等块数组 |
| bulletList | 无序列表 | content 为 listItem 数组 |
| orderedList | 有序列表 | content 为 listItem 数组 |
| listItem | 列表项 | |
| codeBlock | 代码块 | attrs.language 为语言名 |
| blockQuote | 引用块 | 子节点为行内节点（text 等） |
| highLightBlock | 高亮块（彩色背景容器） | 可嵌套块节点 |
| hr | 分割线 | 叶子节点，无子节点 |
| text | 行内文本节点 | 块的 content 数组中的叶子节点，content 字段为文本字符串；attrs 可含 bold、italic、color 等样式 |


## 智能文档 API

### ap.download_otl(file_id, save_dir=None, include_images=False)

下载智能文档为 Markdown 文件。

| 参数 | 类型 | 说明 |
|------|------|------|
| file_id | str | 智能文档文件 ID |
| save_dir | str | 可选，保存目录，默认当前工作目录 |
| include_images | bool | 可选，是否获取图片|

**返回值**

```python
{
    "success": True/False,
    "data": {
        "file_id": "文件ID",
        "name": "文件名.md",
        "local_path": "/path/to/file.md",
        "size": "12.34 KB"
    },
    "message": "下载成功，保存路径为: /path/to/file.md"
}
```

通过该接口获取到的文档块结构与 `ap.block_query` 返回的文档块结构一致

**调用示例**

```python
result = ap.download_otl(file_id="xxx", include_images=True)
print(result)
```

### ap.create_doc(name, title=None, content=None, parent_id="0")

新建智能文档。

| 参数 | 类型 | 说明 |
|------|------|------|
| name | str | 文件名（云文档列表中显示的名称，可省略 .otl 后缀） |
| title | str | 可选，文档大标题 |
| content | str | 可选，Markdown 正文内容 |
| parent_id | str | 可选，目标文件夹的 `file_id`，默认 `"0"`（根目录）；可通过 `kdocs.find_folder_by_path("文件夹名")` 获取 |

**返回值**

```python
{
    "success": True/False,
    "data": {
        "link_id": "link_id（即 file_id，可用于后续操作）",
        "name": "文件名.otl",
        "link_url": "https://365.kdocs.cn/l/xxx"
    },
    "message": "成功创建智能文档: xxx.otl，链接: https://..."
}
```

**调用示例**

```python
result = ap.create_doc(
    name="产品说明",
    title="产品说明",
    content="## 截图\n\n![示例](https://example.com/img.png)\n\n说明文字"
)
print(result)
```


### ap.block_query(file_id)

查询智能文档结构详情

**调用 block_insert / block_delete / block_update 前，必须先调用此接口获取块 ID 和结构。**

| 参数 | 类型 | 说明 |
|------|------|------|
| file_id | str | 智能文档文件 ID |

**返回值**

```python
{
    "success": True/False,
    "data": {
        "blocks": [
            {
                "id": "doc",
                "type": "doc",
                "content": [
                    {"id": "...", "type": "title", "attrs": {...}},
                    {"id": "...", "type": "paragraph", "content": [...], "attrs": {...}}
                ]
            }
        ]
    },
    "message": "查询文档内容成功"
}
```

**调用示例**

```python
result = ap.block_query(file_id="xxx")
print(result)
```


### ap.block_insert(file_id, index, content)

插入块内容。


| 参数 | 类型 | 说明 |
|------|------|------|
| file_id | str | 智能文档文件 ID |
| index | int | 插入位置索引（block_id="doc" 时 ≥1，0 是标题） |
| content | list | 块节点数组，结构见下方说明 |

**content 块结构说明**

| 场景 | 结构示例 |
|------|---------|
| 普通段落 | {"type": "paragraph", "content": [{"type": "text", "content": "文字"}]} |
| 图片 | {"type": "picture", "attrs": {"image_url": "https://..."}} |


**返回值**

```python
{"success": True/False, "message": "插入成功"}
```

**调用示例**

```python
result = ap.block_insert(
    file_id="xxx",
    index=1,
    content=[{
        "type": "paragraph",
        "content": [{"type": "text", "content": "新增段落文本"}]
    }]
)
print(result)
```


### ap.block_delete(file_id, start_index, end_index)

删除智能文档中指定内容。

| 参数 | 类型 | 说明 |
|------|------|------|
| file_id | str | 智能文档文件 ID |
| start_index | int | 删除起始索引（包含） |
| end_index | int | 删除末尾索引（不包含） |

**返回值**

```python
{"success": True/False, "message": "删除成功"}
```

**调用示例**

```python
result = ap.block_delete(file_id="xxx", start_index=1, end_index=2)
print(result)
```

---

### ap.block_update(file_id, params)

更新指定块的内容或属性。

| 参数 | 类型 | 说明 |
|------|------|------|
| file_id | str | 智能文档文件 ID |
| params | list | 操作数组，每项含 operation（操作类型）和 blockId（目标块 ID） |

**operation 类型**

| operation | 功能 | 附加必填参数 |
|-----------|------|-------------|
| update_content | 更新块内容 | content（子节点数组） |
| update_attrs | 更新块属性（**覆盖**操作，不改的字段需原样传入） | attrs（属性对象） |

**返回值**

```python
{"success": True/False, "message": "更新成功"}
```

**调用示例**

```python
# 更新图片
result = ap.block_update(
    file_id="xxx",
    params=[{
        "operation": "update_attrs",
        "blockId": block["id"],
        "attrs": attrs
    }]
)
print(result)
```