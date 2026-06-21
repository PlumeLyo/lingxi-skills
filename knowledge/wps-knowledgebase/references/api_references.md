# WPS KnowledgeBase Skill MCP 工具参考

本文件包含 WPS KnowledgeBase Skill 所有 MCP 工具的参数、示例与返回值。Agent 通过 MCP 工具调用所有接口，无需手动拼接 URL 或传递鉴权 Header（MCP 网关已自动处理）。

---

## 调用约定

### MCP 工具调用

- 工具名称对应各接口文档中的 `mcp_id` 字段（可能包含 server 前缀，如 `user-kwiki-{mcp_id}` 或直接使用 `{mcp_id}`，请参考工具列表）。
- 请求参数以 JSON 格式传递给工具的 `arguments` 字段。
- CSRF Token 仍需根据接口要求通过参数传递。

> **⚠️ mcporter 参数传递格式（关键）**
>
> 通过 `mcporter call` 调用工具时，**必须使用 `--args` 传递 JSON 参数，严禁使用 `--json`**。
> `--json` 会导致 MCP 服务端无法正确解析参数字段，所有值回退为默认值（如知识库名称变成"默认名称"）。

### CSRF 防护

所有写操作（创建、修改、移动、删除、上传）必须携带 CSRF Token，否则后端返回 `{"code":100008,"message":"Required field (csrf)"}`。

| 项目         | 说明                                                                                                                                                                          |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **适用范围** | 所有写操作工具；查询类工具无需携带                                                                                                                                            |
| **生成方式** | 随机 32 位小写十六进制字符串（含 `0-9`, `a-f`）。**Agent 可直接依靠内部随机性自行生成**（如 `d41d8cd98f00b204e9800998ecf8427e`），**严禁调用任何外部 Shell 工具执行 openssl** |
| **传递方式** | Agent 在拼接 `arguments` JSON 时，**必须自行生成**该字符串并塞入 `csrfmiddlewaretoken` 字段一起传递给 MCP 工具                                                                |
| **复用策略** | 推荐会话级复用：一次会话开始时生成一个 token，后续所有写请求复用同一个                                                                                                        |

### 链接输出规范

接口返回的数据中，`url` 字段为**相对路径**（如 `/l/xxx?source=kmwiki` 或 `/wiki/l/xxx`），`kuid`字段为**知识库/文件夹/文件id**。**Agent 在拼接完整链接时，必须遵循以下规则，不猜测：**

1. **拼接规则**：`https://www.kdocs.cn` + `data.url 原值`。
2. **手动构造**：若接口未返回 `url` 但返回了 `kuid`，格式为 `https://www.kdocs.cn/wiki/l/${kuid}`。
3. **严禁使用其他字段构造链接**：不得使用 `file_id`、`link_id`、`drive_id`、`group_id` 等其他返回字段拼接或推测链接地址，只允许使用 `url` 或 `kuid`。

---

## 一、知识库管理接口

### 1. create_knowledge_view

#### 功能说明

创建知识库。请求体对应 `insight.CreateKnowledgeViewReq` 透传。

**触发场景**：用户说"帮我建一个知识库"、"新建 XX 知识库"、"创建一个主题为 XX 的知识库"等意图时调用。

#### 调用示例

```json
{
  "space_name": "前端技术周刊",
  "desc": "记录每周前端技术分享与学习笔记",
  "img": "https://zl.wpscdn.cn/2025/06/09/other/1.png",
  "source": "wiki",
  "status": 1,
  "role_id": "",
  "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### 参数说明

| 字段                  | 类型   | 必填   | 说明                    |
| --------------------- | ------ | ------ | ----------------------- |
| `space_name`          | string | **是** | 知识库名称              |
| `img`                 | string | 否     | 知识库封面图片 URL      |
| `desc`                | string | 否     | 知识库描述              |
| `status`              | int    | **是** | 状态，`1` 表示公开      |
| `source`              | string | 否     | 来源，固定为 `"wiki"`   |
| `role_id`             | string | 否     | 角色 ID                 |
| `csrfmiddlewaretoken` | string | 否     | CSRF 令牌（见调用约定） |

#### 响应 200

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "drive_id": "xxx",
    "group_id": "xxx",
    "kuid": "xxx"
  }
}
```

| 字段            | 类型    | 说明                        |
| --------------- | ------- | --------------------------- |
| `code`          | integer | 业务状态码，0 为正常        |
| `message`       | string  | 返回消息                    |
| `data.drive_id` | string  | 创建的知识库对应的驱动盘 ID |
| `data.group_id` | string  | 知识库组 ID                 |
| `data.kuid`     | string  | 知识库唯一标识              |

#### 调用规范

| 项目         | 说明                                                            |
| ------------ | --------------------------------------------------------------- |
| **必选参数** | 知识库名称（`space_name`）                                      |
| **可选参数** | 知识库简介（`desc`）                                            |
| **核心输出** | 告知创建成功，返回知识库名称、简介、直达入口                    |
| **异常兜底** | 名称重复 / 为空：引导用户修改；创建失败：明确告知原因并引导重试 |

---

### 2. list_knowledge_view

#### 功能说明

获取用户的知识库列表，支持名称模糊搜索。

**触发场景**：用户说"查一下我的知识库"、"我有哪些知识库"、"知识库列表"、"列出我所有的知识库"等意图时调用。

#### 调用示例

```json
{
  "keyword": "前端",
  "page_size": 20
}
```

#### 参数说明

| 字段         | 类型   | 位置  | 必填 | 说明               |
| ------------ | ------ | ----- | ---- | ------------------ |
| `keyword`    | string | query | 否   | 名称模糊搜索关键字 |
| `page_size`  | int    | query | 否   | 每页数量，默认 20  |
| `page_token` | string | query | 否   | 翻页令牌           |

#### 响应 200

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "has_more": true,
    "list": [
      {
        "kuid": "xxx",
        "name": "我的知识库",
        "desc": "简介",
        "drive_id": "xxx",
        "group_id": "xxx",
        "file_total": 10,
        "member_total": 3,
        "cover_img": "https://...",
        "created_at": "2026-03-20T10:00:00Z"
      }
    ],
    "next_page_token": "xxx"
  }
}
```

#### 响应字段说明

| 字段                       | 类型    | 说明                         |
| -------------------------- | ------- | ---------------------------- |
| `code`                     | integer | 业务状态码，0 为正常         |
| `message`                  | string  | 返回消息                     |
| `data.has_more`            | boolean | 是否有下一页                 |
| `data.list`                | array   | 知识库列表                   |
| `data.list[].kuid`         | string  | 知识库唯一标识               |
| `data.list[].name`         | string  | 知识库名称                   |
| `data.list[].desc`         | string  | 知识库描述                   |
| `data.list[].drive_id`     | string  | 驱动盘 ID                    |
| `data.list[].group_id`     | string  | 组 ID                        |
| `data.list[].file_total`   | integer | 文档数                       |
| `data.list[].member_total` | integer | 成员数                       |
| `data.list[].cover_img`    | string  | 封面图片 URL                 |
| `data.list[].created_at`   | string  | 创建时间（ISO 8601 格式）    |
| `data.next_page_token`     | string  | 翻页令牌，空字符串代表到末尾 |

#### 调用规范

| 项目         | 说明                                                    |
| ------------ | ------------------------------------------------------- |
| **必选参数** | 无                                                      |
| **可选参数** | 名称模糊搜索关键词（`keyword`，服务端处理）             |
| **核心输出** | 返回知识库列表（名称、简介、创建时间），超 5 条折叠分页 |
| **异常兜底** | 无匹配知识库：引导用户创建；查询失败：告知原因          |

> **统计总数**：若需「共有多少个知识库」，需分页拉取直至 `has_more` 为 `false`，对 `data.list` 累加条数（响应中无单独 `total` 字段时以服务端为准）。

---

### 3. get_knowledge_view

#### 功能说明

获取指定知识库的详细信息，支持按 `drive_id` 或 `name` 查询（`name` 支持模糊匹配，服务端处理）。

**触发场景**：用户说"查一下 XX 知识库的详情"、"XX 知识库的信息"、"看看 XX 库的基本情况"等意图时调用。

#### 调用示例

按 ID 查询：

```json
{
  "drive_id": "3020487178"
}
```

按名称查询：

```json
{
  "name": "前端技术周刊"
}
```

#### 参数说明

| 字段       | 类型   | 位置  | 必填   | 说明               |
| ---------- | ------ | ----- | ------ | ------------------ |
| `drive_id` | string | query | 二选一 | 按 ID 查询         |
| `name`     | string | query | 二选一 | 按名称模糊匹配查询 |

> **参数互斥规则（强制）**：`drive_id` 和 `name` 二选一传入。**优先使用 `drive_id` 进行精确查询**；只有在不知道 `drive_id` 的情况下才使用 `name` 进行模糊匹配。**严禁在同一个请求中同时传入这两个参数。**

#### 响应 200

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "drive_id": "xxx",
    "group_id": "xxx",
    "kuid": "xxx",
    "name": "我的知识库",
    "desc": "简介",
    "cover_img": "https://...",
    "status": 1,
    "file_total": 10,
    "member_total": 3
  }
}
```

#### 响应字段说明

| 字段                | 类型    | 说明                 |
| ------------------- | ------- | -------------------- |
| `code`              | integer | 业务状态码，0 为正常 |
| `message`           | string  | 返回消息             |
| `data.drive_id`     | string  | 驱动盘 ID            |
| `data.group_id`     | string  | 组 ID                |
| `data.kuid`         | string  | 知识库唯一标识       |
| `data.name`         | string  | 知识库名称           |
| `data.desc`         | string  | 知识库描述           |
| `data.cover_img`    | string  | 封面图片 URL         |
| `data.status`       | integer | 状态                 |
| `data.file_total`   | integer | 文档数               |
| `data.member_total` | integer | 成员数               |

#### 调用规范

| 项目         | 说明                                               |
| ------------ | -------------------------------------------------- |
| **必选参数** | 知识库名称或 ID（`drive_id` 或 `name`，二选一）    |
| **可选参数** | 无                                                 |
| **核心输出** | 返回知识库名称、简介、创建时间、文件数量等核心详情 |
| **异常兜底** | 知识库不存在：引导用户核对名称；查询失败：告知原因 |

#### 按名称查询逻辑

当用户提供的是知识库名称时，Agent 按以下流程处理：

1. 调用 `get_knowledge_view(name=xxx)`，服务端进行模糊匹配
2. 若返回成功，展示知识库详情
3. 若用户反馈结果不是目标知识库，调用 `list_knowledge_view(keyword=xxx)` 获取候选列表，列出所有匹配项供用户选择
4. 若返回失败（不存在），引导用户核对名称是否正确

---

### 4. update_knowledge_view

#### 功能说明

修改知识库的名称、简介、封面、可见性等基础配置。请求体对应 `insight.UpdateKnowledgeViewReq` 透传。

**触发场景**：用户说"把 XX 知识库改名为 XX"、"修改 XX 知识库的简介"、"更新 XX 库的信息"等意图时调用。

#### 调用示例

```json
{
  "drive_id": "3020487178",
  "group_id": "2100635239",
  "name": "前端技术周刊（2026）",
  "desc": "2026 年度前端技术分享与学习笔记",
  "cover_img": "https://zl.wpscdn.cn/2025/06/09/other/1.png",
  "status": 1,
  "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### 参数说明

| 字段                  | 类型   | 必填   | 说明                                                          |
| --------------------- | ------ | ------ | ------------------------------------------------------------- |
| `drive_id`            | string | **是** | 目标知识库 ID                                                 |
| `group_id`            | string | **是** | 组 ID；未传时服务端可能默认与 `drive_id` 一致，以实际校验为准 |
| `status`              | int    | **是** | 状态                                                          |
| `cover_img`           | string | **是** | 新封面 URL                                                    |
| `name`                | string | **是** | 新名称                                                        |
| `desc`                | string | **是** | 新简介                                                        |
| `csrfmiddlewaretoken` | string | 否     | CSRF 令牌（见调用约定）                                       |

> **⚠️ 先读后写（强制）**
>
> 本接口要求传入**所有必填字段**，未传的字段会被覆盖为空值（而非保持不变）。
> Agent **必须**在修改前先调用 `get_knowledge_view(drive_id=xxx)` 读取当前完整配置，
> 将待修改字段替换后，**连同未修改字段一起整体提交**，避免误清空 name / desc / cover_img 等。

#### 响应 200

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| 字段      | 类型    | 说明                       |
| --------- | ------- | -------------------------- |
| `code`    | integer | 业务状态码，0 为正常       |
| `message` | string  | 返回消息                   |
| `data`    | object  | 返回数据（成功时为空对象） |

#### 调用规范

| 项目         | 说明                                                                               |
| ------------ | ---------------------------------------------------------------------------------- |
| **前置步骤** | **必须**先调用 `get_knowledge_view(drive_id)` 读取当前值，合并修改字段后整体提交   |
| **必选参数** | 目标知识库（`drive_id` / `group_id`）及待更新的名称、简介、封面、状态              |
| **可选参数** | 无（业务字段以服务端校验为准）                                                     |
| **核心输出** | 告知修改成功，返回修改前后的信息对比                                               |
| **异常兜底** | 知识库不存在：引导用户确认；新名称重复：引导用户调整；修改失败：告知原因并引导重试 |

---

### 5. close_knowledge_view

#### 功能说明

关闭并删除指定个人知识库，操作前务必确认目标正确。

#### 调用示例

关闭指定知识库：

```json
{
  "drive_id": "8001234567",
  "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### 参数说明

| 字段       | 类型   | 必填   | 说明                                                                                |
| ---------- | ------ | ------ | ----------------------------------------------------------------------------------- |
| `drive_id` | string | **是** | 要关闭的知识库驱动盘 ID，来自 `list_knowledge_views` 或 `get_knowledge_view` 返回值 |

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": ""
}
```

#### 操作约束

- **用户确认**：关闭知识库不可恢复，必须向用户确认目标知识库名称和 ID
- **前置检查**：`kwiki.get_knowledge_view` 确认目标知识库

---

## 二、文件管理接口

### 1. list_file

#### 功能说明

获取知识库内的子节点列表（文件和文件夹）。

**触发场景**：用户说"查一下 XX 库里的文件"、"XX 文件夹里有什么"、"列出 XX 库的所有文件"等意图时调用。

#### 参数说明

| 字段   | 类型   | 位置  | 必填   | 说明                      |
| ------ | ------ | ----- | ------ | ------------------------- |
| `kuid` | string | query | **是** | 知识库 kuid 或文件夹 kuid |

#### 响应 200

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "has_more": false,
    "next_page_token": "",
    "list": [
      {
        "title": "文件名",
        "doc_type": "w",
        "doc_origin_type": "",
        "kuid": "0s_xxx",
        "ctime": 1711234567,
        "page_token": "",
        "creator": { "id": 123, "name": "用户名", "avatar": "" },
        "size": 1024,
        "link_id": "xxx",
        "file_id": "xxx",
        "parent_id": "xxx",
        "parent_link_id": "xxx"
      }
    ]
  }
}
```

#### 响应字段说明

| 字段                          | 类型    | 说明                                                        |
| ----------------------------- | ------- | ----------------------------------------------------------- |
| `code`                        | integer | 业务状态码，0 为正常                                        |
| `msg`                         | string  | 返回消息                                                    |
| `data.has_more`               | boolean | 是否有下一页                                                |
| `data.next_page_token`        | string  | 翻页 token，空字符串代表到末尾                              |
| `data.list`                   | array   | 文件节点列表                                                |
| `data.list[].title`           | string  | 文档名称                                                    |
| `data.list[].doc_type`        | string  | 文档类型。`w`: wps、`p`: ppt、`s`: et、`o`: fp、`d`: 轻维表 |
| `data.list[].doc_origin_type` | string  | 源头文件类型                                                |
| `data.list[].kuid`            | string  | 节点唯一标识                                                |
| `data.list[].ctime`           | integer | 创建时间（Unix 时间戳）                                     |
| `data.list[].page_token`      | string  | 分页 token                                                  |
| `data.list[].creator.id`      | integer | 创建者 ID                                                   |
| `data.list[].creator.name`    | string  | 创建者名称                                                  |
| `data.list[].creator.avatar`  | string  | 创建者头像                                                  |
| `data.list[].size`            | integer | 文档大小                                                    |
| `data.list[].link_id`         | string  | 链接 ID                                                     |
| `data.list[].file_id`         | string  | 文件 ID                                                     |
| `data.list[].parent_id`       | string  | 父节点 ID                                                   |
| `data.list[].parent_link_id`  | string  | 父节点链接 ID                                               |

#### 调用规范

| 项目         | 说明                                                          |
| ------------ | ------------------------------------------------------------- |
| **必选参数** | 目标知识库 kuid 或文件夹 kuid                                 |
| **可选参数** | 无                                                            |
| **核心输出** | 返回文件 / 文件夹列表（名称、类型、创建时间、大小）           |
| **异常兜底** | 知识库 / 文件夹不存在：引导核对；无匹配文件：引导调整筛选条件 |

---

### 2. import_file

#### 功能说明

将已有的云文档导入到知识库中，支持两种模式：**副本导入**（`copy`）和**快捷方式导入**（`shortcut`）。

**触发场景**：用户说"把云文档导入到知识库"、"把 XX 文档复制到知识库里"、"在知识库里创建 XX 文档的快捷方式"等意图时调用。

#### 调用示例

```json
{
  "action": "copy",
  "file_infos": [
    {
      "file_ids": [100236796634],
      "group_id": 2100635239
    }
  ],
  "kuid": "0s_4002368554",
  "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### 参数说明

| 字段                    | 类型          | 必填   | 说明                                              |
| ----------------------- | ------------- | ------ | ------------------------------------------------- |
| `action`                | string        | **是** | 导入模式：`copy`（副本）或 `shortcut`（快捷方式） |
| `file_infos`            | array         | **是** | 待导入的云文档信息列表                            |
| `file_infos[].file_ids` | array[number] | **是** | 云文档的 file_id 列表                             |
| `file_infos[].group_id` | number        | **是** | 导入的文档所在的 group_id                         |
| `kuid`                  | string        | **是** | 目标知识库的 kuid                                 |

#### 响应 200

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "url": "/wiki/l/0s_4002368554"
  }
}
```

#### 响应字段说明

| 字段       | 类型    | 说明                   |
| ---------- | ------- | ---------------------- |
| `code`     | integer | 业务状态码，0 为正常   |
| `msg`      | string  | 返回消息               |
| `data.url` | string  | 导入后知识库的访问路径 |

#### 调用规范

| 项目         | 说明                                                                                        |
| ------------ | ------------------------------------------------------------------------------------------- |
| **必选参数** | 导入模式（`action`）、云文档信息（`file_infos`）、目标知识库 kuid                           |
| **可选参数** | 无                                                                                          |
| **核心输出** | 告知导入成功，返回知识库访问链接（格式：`https://www.kdocs.cn/wiki/l/${kuid}`）             |
| **异常兜底** | 云文档不存在：引导核对 file_id 和 group_id；知识库不存在：引导核对 kuid；导入失败：告知原因 |

#### 导入模式说明

| 模式         | `action` 值 | 说明                                             |
| ------------ | ----------- | ------------------------------------------------ |
| **副本**     | `copy`      | 在知识库中创建云文档的独立副本，后续编辑互不影响 |
| **快捷方式** | `shortcut`  | 在知识库中创建指向原文档的引用，编辑同步到源文档 |

> 用户未明确指定模式时，默认使用 `copy`（副本）。

---

### 3. upload_file

#### 功能说明

通过 HTTP POST 直传本地文件到知识库（`multipart/form-data`），支持批量上传多个文件。

**接口路径**：`POST /kwiki/api/v1/skills_hub/skill/file/upload`

**触发场景**：用户说"上传文件到 XX 库"、"把本地文件传到知识库"、"上传 XX 文件到 XX 目录下"等意图时调用。

> **⚠️ 文件格式说明**
>
> 所有本地文件（包括 `.md`、`.docx`、`.pdf`、`.png` 等）均通过本接口直接上传。

#### 参数说明

| 字段                  | 类型   | 必填   | 说明                                                                                                           |
| --------------------- | ------ | ------ | -------------------------------------------------------------------------------------------------------------- |
| `drive_id`            | string | **是** | 目标知识库 drive_id                                                                                            |
| `parent_link_id`      | string | **是** | 父目录的 `link_id`（对应 `list_file` 返回的 `link_id` 字段，**严禁传成 `file_id`**）；上传到库根目录时填 `"0"` |
| `files`               | []file | **是** | 实体文件列表（multipart file 字段）                                                                            |
| `csrfmiddlewaretoken` | string | **是** | CSRF 令牌（见调用约定），作为 multipart 表单字段传入                                                           |

#### 调用示例

**curl（macOS / Linux）：**

```bash
curl -X POST "https://zhishi.wps.cn/kwiki/api/v1/skills_hub/skill/file/upload" \
  -H "X-Kwiki-Auth: $X_KWIKI_AUTH" \
  -F "drive_id=<目标库 drive_id>" \
  -F "parent_link_id=0" \
  -F "csrfmiddlewaretoken=d41d8cd98f00b204e9800998ecf8427e" \
  -F "files=@/path/to/file1.docx" \
  -F "files=@/path/to/file2.pdf"
```

**curl（Windows PowerShell）：**

```powershell
curl.exe -X POST "https://zhishi.wps.cn/kwiki/api/v1/skills_hub/skill/file/upload" `
  -H "X-Kwiki-Auth: $X_KWIKI_AUTH" `
  -F "drive_id=<目标库 drive_id>" `
  -F "parent_link_id=0" `
  -F "csrfmiddlewaretoken=d41d8cd98f00b204e9800998ecf8427e" `
  -F "files=@C:\path\to\file1.docx" `
  -F "files=@C:\path\to\file2.pdf"
```

**Python（推荐，跨平台通用，尤其 Windows 中文文件名场景）：**

```python
import requests

url = "https://zhishi.wps.cn/kwiki/api/v1/skills_hub/skill/file/upload"
headers = {"X-Kwiki-Auth": token}  # token 从 .env 的 X_KWIKI_AUTH 读取

files_list = [
    ("files", ("报告.docx", open("/path/to/报告.docx", "rb"), "application/octet-stream")),
    ("files", ("数据.pdf", open("/path/to/数据.pdf", "rb"), "application/octet-stream")),
]
data = {
    "drive_id": "<目标库 drive_id>",
    "parent_link_id": "0",
    "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e",
}

resp = requests.post(url, headers=headers, data=data, files=files_list)
print(resp.json())
```

#### Agent 调用行为规范

上传通过 HTTP `multipart/form-data` 直传文件。

Agent 流程：

1. 确认目标知识库和目标文件夹存在（`get_knowledge_view` + `list_file`）
2. 构造 `multipart/form-data` 请求，`files` 字段传入实体文件
3. 发送 HTTP POST 请求，`X-Kwiki-Auth` 头携带认证 Token

> 中文文件名在 `multipart/form-data` 中由 HTTP 客户端自动处理编码，无需额外处理。

#### 响应 200

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "file_name": "报告.docx",
      "file_id": "EkSXLQ5TtxMJijiRVrZfxxjiDC9DQdEVZ",
      "file_size": 279,
      "url": "/wiki/l/0lcfdsw6VyCgwQ"
    },
    {
      "file_name": "数据.pdf",
      "file_id": "dSgK1a37UxMpus4PQJVN1xUX3T6yMfLLZ",
      "file_size": 125541,
      "url": "/wiki/l/0lcgHkGIydFaJo"
    }
  ]
}
```

#### 响应字段说明

| 字段               | 类型    | 说明                 |
| ------------------ | ------- | -------------------- |
| `code`             | integer | 业务状态码，0 为正常 |
| `msg`              | string  | 返回消息             |
| `data`             | array   | 上传成功的文件列表   |
| `data[].file_name` | string  | 文件名               |
| `data[].file_id`   | string  | 文件 ID              |
| `data[].file_size` | integer | 文件大小（字节）     |
| `data[].url`       | string  | 文件的访问路径       |

#### 调用规范

| 项目         | 说明                                                                                            |
| ------------ | ----------------------------------------------------------------------------------------------- |
| **必选参数** | 目标知识库 drive_id、文件列表（multipart file）、父目录 link_id                                 |
| **可选参数** | 无                                                                                              |
| **核心输出** | 告知上传成功，返回每个文件的名称、大小和访问链接（格式：`https://www.kdocs.cn/wiki/l/${kuid}`） |
| **异常兜底** | 知识库不存在：引导核对 drive_id；上传失败：告知错误原因并引导重试                               |

---

### 4. create_file

#### 功能说明

在知识库中新建**空的** WebOffice 在线文档节点或文件夹。

> ⚠️ **「创建文件」≠「写入内容」**
>
> 本接口仅在知识库目录树中创建一个空的文档节点（由 WebOffice 管理），**不支持写入文档正文内容**。
> 如果用户要求"创建文档并写入内容"，Agent 应：
>
> 1. 调用本接口创建空文档
> 2. 返回文档的在线访问链接（格式：`https://www.kdocs.cn/wiki/l/${kuid}`）
> 3. **明确告知用户**：文档已创建，需通过链接在 WebOffice 编辑器中手动编辑内容

**触发场景**：用户说"在 XX 库里新建一个文件夹"、"在 XX 文件夹里建一个 XX 文档"、"创建 XX 文件夹"等意图时调用。

#### 调用示例

```json
{
  "doc_type": "o",
  "kuid": "0s_4002368554",
  "parent_file_id": "0",
  "title": "2026 Q2 技术方案",
  "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### 参数说明

| 字段             | 类型   | 必填   | 说明                                                                                                                                                         |
| ---------------- | ------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `doc_type`       | string | **是** | 文档类型。`w`: wps（文字文档）、`p`: ppt（演示文稿）、`s`: et（表格）、`o`: fp（智能文档）、`d`: 轻维表、`folder`: 文件夹。枚举值：`[w, p, s, o, d, folder]` |
| `kuid`           | string | **是** | 知识库的 kuid                                                                                                                                                |
| `parent_file_id` | string | **否** | 父文件夹的 `file_id`（对应 `list_file` 返回的 `file_id` 字段，**严禁传成 `link_id`**）；`"0"` 表示根目录                                                     |
| `title`          | string | **是** | 文件 / 文件夹名称                                                                                                                                            |

#### 响应 200

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "kuid": "0lcrH7FwnLujDp",
    "title": "name of new file or folder",
    "url": "url of new file or folder"
  }
}
```

| 字段         | 类型    | 说明                       |
| ------------ | ------- | -------------------------- |
| `code`       | integer | 业务状态码，0 为正常       |
| `msg`        | string  | 返回消息                   |
| `data.kuid`  | string  | 新建文件或文件夹的 kuid    |
| `data.title` | string  | 新建文件或文件夹的名称     |
| `data.url`   | string  | 新建文件或文件夹的访问链接 |

#### 调用规范

| 项目         | 说明                                                                                      |
| ------------ | ----------------------------------------------------------------------------------------- |
| **必选参数** | 目标知识库 kuid、创建类型（`doc_type`）、名称（`title`）、父文件夹 ID                     |
| **可选参数** | 无                                                                                        |
| **核心输出** | 告知创建成功，返回创建的完整路径和访问链接（格式：`https://www.kdocs.cn/wiki/l/${kuid}`） |
| **异常兜底** | 名称重复 / 为空：引导修改；父路径不存在：引导核对；创建失败：告知原因                     |

#### 支持新建的文档类型

| 类型         | `doc_type` | 别名 | 文件后缀 | 推荐度         | 说明                               |
| ------------ | ---------- | ---- | -------- | -------------- | ---------------------------------- |
| **智能文档** | `o`        | ap   | .otl     | [===] **首选** | 排版美观，支持丰富组件             |
| 表格         | `s`        | et   | .xlsx    | [===]          | 数据表格专用                       |
| ppt文档      | `p`        | ppt  | .pptx    | [===]          | PPT 文档专用                       |
| 文字文档     | `w`        | wps  | .docx    | [===]          | 传统格式                           |
| 轻维表       | `d`        | db   | .dbt     | [===]          | 数据库化表格，支持多视图、字段管理 |

> **别名识别**：用户提到 `ap文件` = 智能文档(.otl)、`et文件` = 表格(.xlsx)、`wps文件` = 文字文档(.docx)、`ppt文件` = ppt文档(.pptx)、`db文件` = 轻维表(.dbt)。遇到这些别名时，自动映射到对应的文档类型进行操作。

#### 文档类型选择

```
用户需要创建文档
├── 需要丰富排版/图文混排？ → otl（智能文档）首选
├── 需要表格/数据处理？→ 简单表格数据 → xlsx
│   需要数据表/字段管理/多视图 → dbt（轻维表）
├── 需要生成 ppt？ → pptx
├── 需要兼容 Word？ → docx
└── 不确定 → otl（智能文档）默认推荐
```

---

### 5. move_file

#### 功能说明

移动一个或多个文档 / 文件夹到目标位置（支持批量，通过 `file_kuids` 数组传入多个）。

**触发场景**：用户说"把 XX 文件移到 XX 文件夹里"、"把 XX 文件夹挪到 XX 库里"、"移动 XX 文件到 XX 路径"、"把这几个文件都移到 XX 文件夹里"等意图时调用。

#### 调用示例

```json
{
  "group_id": "2100635239",
  "drive_id": "3020487178",
  "dest_drive_id": "3020487200",
  "dest_parent_id": "3020487210",
  "file_kuids": ["0lcrH7FwnLujDp", "0lcgHkGIydFaJo"],
  "space_kuid": "0s_4002368554",
  "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### 参数说明

| 字段             | 类型          | 必填   | 说明                                                                                                                     |
| ---------------- | ------------- | ------ | ------------------------------------------------------------------------------------------------------------------------ |
| `group_id`       | string        | **是** | 源知识库 group_id                                                                                                        |
| `drive_id`       | string        | **是** | 源知识库 drive_id                                                                                                        |
| `dest_drive_id`  | string        | **是** | 目标知识库 drive_id                                                                                                      |
| `dest_parent_id` | string        | **是** | 目标文件夹 file_id；移动到根目录时传 `"0"`                                                                               |
| `file_kuids`     | array[string] | **是** | 待移动文件的 kuid 列表。**警告：即使只移动 1 个文件，也必须使用数组格式包裹（如 `["单文件kuid"]`），严禁直接传入字符串** |
| `space_kuid`     | string        | **是** | 源知识库 kuid                                                                                                            |

#### 响应 200

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "url": "/wiki/l/0l0lctuE1b8w4gho"
  }
}
```

| 字段       | 类型    | 说明                       |
| ---------- | ------- | -------------------------- |
| `code`     | integer | 业务状态码，0 为正常       |
| `msg`      | string  | 返回消息                   |
| `data.url` | string  | 移动后第一个文件的访问路径 |

#### 调用规范

| 项目         | 说明                                                    |
| ------------ | ------------------------------------------------------- |
| **必选参数** | 待移动文件 kuid 列表、源知识库信息、目标知识库 drive_id |
| **可选参数** | 无                                                      |
| **核心输出** | 告知移动成功，返回新的存放路径                          |
| **异常兜底** | 见下方「移动前置检查」                                  |

#### 参数收集流程

> ⚠️ 本接口需要 6 个参数，分散在多个前置查询的返回值中。Agent **必须**按以下流程逐步收集，禁止猜测或硬编码。

```
步骤 1: get_knowledge_view(name="源库名") 或 list_knowledge_view(keyword="源库名")
        → 获取 drive_id, group_id, kuid (即 space_kuid)

步骤 2: list_file(kuid=源库kuid)
        → 定位待移动文件 → 获取文件的 kuid (即 file_kuids 数组元素)

步骤 3 (同库移动): list_file(kuid=源库kuid)
        → 定位目标文件夹 → 获取文件夹的 file_id (即 dest_parent_id)
        → dest_drive_id = drive_id（同一个库）

步骤 3 (跨库移动): get_knowledge_view(name="目标库名")
        → 获取目标库 drive_id (即 dest_drive_id)
        → list_file(kuid=目标库kuid) 定位目标文件夹 → 获取 file_id (即 dest_parent_id)
```

| 参数             | 来源                                                        |
| ---------------- | ----------------------------------------------------------- |
| `group_id`       | 源库 `get_knowledge_view` 返回                              |
| `drive_id`       | 源库 `get_knowledge_view` 返回                              |
| `space_kuid`     | 源库 `get_knowledge_view` 返回的 `kuid`                     |
| `file_kuids`     | `list_file` 返回的文件 `kuid` 数组                          |
| `dest_drive_id`  | 目标库 `get_knowledge_view` 返回                            |
| `dest_parent_id` | 目标文件夹 `list_file` 返回的 `file_id`；移到根目录传 `"0"` |

#### 移动前置检查

> ⚠️ **Agent 在执行移动操作前，必须先通过文件列表接口确认源文件和目标路径均存在。禁止自动创建目标文件夹。**

Agent 调用移动接口前，必须按以下规则处理异常情况：

| 异常场景                 | Agent 行为                                                                                                             |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| **源文件不存在**         | 告知用户未找到该文件，列出相似名称的文件供用户确认                                                                     |
| **目标文件夹不存在**     | 告知用户目标路径不存在，**询问用户**：1) 是否路径名称有误，需要核对；2) 是否需要先创建该文件夹。等用户明确确认后再操作 |
| **目标路径存在同名文件** | 告知用户目标路径下已有同名文件，询问用户如何处理                                                                       |
| **移动失败**             | 告知具体错误原因，引导用户重试                                                                                         |

**禁止行为**：不得在用户未确认的情况下自动创建目标文件夹、自动重命名或自动覆盖同名文件。

---

### 6. delete_file

#### 功能说明

删除单个文档（移入回收站，非永久删除），支持删除文件夹（包括非空文件夹，会连带删除内部所有内容）。

> ⚠️ **本接口每次仅支持删除单个文件**。若用户需要删除多个文件，Agent 应对每个文件分别调用本接口，可**并行调用**以提高效率。

**触发场景**：用户说"删除 XX 库里的 XX 文件"、"把 XX 文件删掉"、"移除 XX 文件夹里的 XX 文件"、"把这几个文件都删掉"等意图时调用。

> **Agent 必须在删除成功后明确告知用户**：文件已移入回收站，7 天内可恢复，并附上回收站链接。

#### 调用示例

```json
{
  "kuid": "0lPqRs8WxYzAbC",
  "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### 参数说明

| 字段   | 类型   | 必填   | 说明              |
| ------ | ------ | ------ | ----------------- |
| `kuid` | string | **是** | 知识库文件的 kuid |

#### 响应 200

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "message": "文件已移至回收站，7天内可恢复",
    "trash_url": "https://www.kdocs.cn/enttrash/0"
  }
}
```

| 字段             | 类型    | 说明                               |
| ---------------- | ------- | ---------------------------------- |
| `code`           | integer | 业务状态码，0 为正常               |
| `msg`            | string  | 返回消息                           |
| `data.message`   | string  | 友好提示（回收站 + 恢复有效期）    |
| `data.trash_url` | string  | 回收站地址，可引导用户访问恢复文件 |

#### 调用规范

| 项目                     | 说明                                                                                                                                                                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **高危前置检查（强制）** | 当目标对象是一个**文件夹**（`doc_type == "folder"`）时，Agent 必须先调用 `list_file` 检查其内部是否为空。如果不为空，必须向用户发出二次警告："该文件夹内包含 N 个文件，删除将连带全部移入回收站，是否继续？"。**严禁未经检查直接删除非空文件夹** |
| **必选参数**             | 待删除文件/文件夹的 kuid                                                                                                                                                                                                                         |
| **可选参数**             | 无                                                                                                                                                                                                                                               |
| **核心输出**             | 告知删除成功，展示回收站链接（`https://www.kdocs.cn/enttrash/0`）和恢复有效期                                                                                                                                                                    |
| **异常兜底**             | 文件 / 知识库不存在：引导核对；删除失败：告知原因                                                                                                                                                                                                |

#### 批量删除策略

本接口不支持一次删除多个文件。当用户要求删除多个文件时，Agent 应：

1. 通过 `list_file` 查询文件/文件夹列表，确认所有待删除文件的 kuid
2. 对每个 kuid **并行调用** `delete_file`（不必串行等待）
3. 汇总所有调用结果，统一向用户报告：成功 N 个、失败 M 个（若有失败，列出具体文件和错误原因）
4. 告知用户所有已删除文件均在回收站中，7 天内可恢复

---

### 7. rename_file

#### 功能说明

重命名知识库中的文件。

**触发场景**：用户说"把 XX 文件改名为 XX"、"重命名 XX 文件"等意图时调用。

#### 调用示例

```json
{
  "kuid": "0lcrH7FwnLujDp",
  "title": "2026 Q2 技术方案（终稿）",
  "operate_kdocs": true,
  "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### 参数说明

| 字段            | 类型   | 必填   | 默认值 | 说明               |
| --------------- | ------ | ------ | ------ | ------------------ |
| `kuid`          | string | **是** | -      | 文件唯一标识       |
| `title`         | string | **是** | -      | 新文件名           |
| `operate_kdocs` | bool   | 否     | `true` | 是否同步操作云文档 |

#### 响应 200

```json
{
  "code": 0,
  "data": {}
}
```

| 字段   | 类型    | 说明                       |
| ------ | ------- | -------------------------- |
| `code` | integer | 业务状态码，0 为正常       |
| `data` | object  | 返回数据（成功时为空对象） |

#### 调用规范

| 项目         | 说明                                                                 |
| ------------ | -------------------------------------------------------------------- |
| **必选参数** | 文件 kuid、新文件名（`title`）                                       |
| **可选参数** | `operate_kdocs`（默认 `true`，同步重命名云文档）                     |
| **核心输出** | 告知重命名成功，返回新文件名                                         |
| **异常兜底** | 文件不存在：引导核对 kuid；新名称为空/重复：引导修改；失败：告知原因 |

---

### 8. download_file

#### 功能说明

下载知识库文件，支持三种响应格式。

**接口路径**：`POST /kwiki/api/v1/skills_hub/skill/file/download`

**触发场景**：用户说"下载 XX 文件"、"获取 XX 文件的下载链接"等意图时调用。

#### 响应格式

| `response_type`         | 说明                       |
| ----------------------- | -------------------------- |
| `download_link`（默认） | 返回下载链接               |
| `file_stream`           | 直接返回文件二进制流       |
| `file_base64`           | 返回 Base64 编码的文件内容 |

#### 调用示例

```json
{
  "kuid": "0lcrH7FwnLujDp",
  "response_type": "download_link"
}
```

#### 参数说明

| 字段            | 类型   | 必填   | 默认值          | 说明                                                      |
| --------------- | ------ | ------ | --------------- | --------------------------------------------------------- |
| `kuid`          | string | **是** | -               | 文件唯一标识                                              |
| `response_type` | string | 否     | `download_link` | 响应格式：`download_link` / `file_stream` / `file_base64` |

#### 响应 - download_link

```json
{
  "code": 0,
  "data": {
    "download_url": "https://..."
  }
}
```

| 字段                | 类型    | 说明                                                 |
| ------------------- | ------- | ---------------------------------------------------- |
| `code`              | integer | 业务状态码，0 为正常                                 |
| `data.download_url` | string  | 文件下载链接（带签名，可直接 `curl.exe -L -o` 下载） |

> **注意**：`download_url` 带签名，可直接下载，无需登录态。
> 使用 `curl.exe -L -o "文件名" "download_url"` 即可保存到本地。

#### 响应 - file_stream

直接返回文件二进制流，响应头包含 `Content-Disposition: attachment; filename="xxx"`。

#### 响应 - file_base64

```json
{
  "code": 0,
  "data": {
    "file_name": "example.docx",
    "file_base64": "base64编码内容..."
  }
}
```

| 字段               | 类型    | 说明                     |
| ------------------ | ------- | ------------------------ |
| `code`             | integer | 业务状态码，0 为正常     |
| `data.file_name`   | string  | 文件名                   |
| `data.file_base64` | string  | 文件内容的 Base64 编码串 |

#### 调用规范

| 项目         | 说明                                                     |
| ------------ | -------------------------------------------------------- |
| **必选参数** | 文件 kuid                                                |
| **可选参数** | `response_type`（默认 `download_link`）                  |
| **核心输出** | 根据 `response_type` 返回下载链接 / 文件流 / Base64 内容 |
| **异常兜底** | 文件不存在：引导核对 kuid；获取失败：告知原因并引导重试  |

---

### 9. convert_file

#### 功能说明

将指定格式的内容转换为目标格式的文件。目前仅支持 **md → otl**（Markdown 转智能文档）。

**触发场景**：用户说"把 Markdown 转成智能文档"、"将这段md内容转为在线文档"、"Markdown 转 otl"等意图时调用。

#### 调用示例

```json
{
  "kuid": "0s_xxxxxxxxxxxx",
  "title": "技术方案",
  "content": "# 标题\n\n## 概述\n\n这是一段 Markdown 内容...",
  "from": "md",
  "to": "otl",
  "csrfmiddlewaretoken": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### 参数说明

| 字段      | 类型   | 必填   | 默认值 | 说明                                                          |
| --------- | ------ | ------ | ------ | ------------------------------------------------------------- |
| `kuid`    | string | **是** | -      | 目标知识库的 kuid（`0s_` 开头），转换后的文件创建在此知识库下 |
| `title`   | string | **是** | -      | 文件标题（无需 `.otl` 后缀）                                  |
| `content` | string | **是** | -      | 源内容（Markdown 文本）                                       |
| `from`    | string | 否     | `md`   | 源格式                                                        |
| `to`      | string | 否     | `otl`  | 目标格式                                                      |

#### 响应 200

```json
{
  "code": 0,
  "data": {
    "file_id": "abc123def456"
  }
}
```

| 字段           | 类型    | 说明                 |
| -------------- | ------- | -------------------- |
| `code`         | integer | 业务状态码，0 为正常 |
| `data.file_id` | string  | 转换后生成的文件 ID  |

#### 调用规范

| 项目         | 说明                                                                                   |
| ------------ | -------------------------------------------------------------------------------------- |
| **必选参数** | 目标知识库 kuid（`kuid`，`0s_` 开头）、文件标题（`title`）、Markdown 内容（`content`） |
| **可选参数** | 源格式（`from`，默认 `md`）、目标格式（`to`，默认 `otl`）                              |
| **核心输出** | 告知转换成功，返回生成的文件 ID                                                        |
| **异常兜底** | 知识库不存在：引导核对 kuid；内容为空：引导提供内容；转换失败：告知原因                |

---
