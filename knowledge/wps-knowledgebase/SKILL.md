---
name: wps-knowledgebase
description: 'WPS KnowledgeBase Skill — 个人知识库平台，提供知识文档的创建、搜索、读取、编辑与协作能力。当用户 prompt 中包含「知识库」「kwiki」「知识管理」「知识文档」「存入知识库」「上传到知识库」「导入知识库」「保存到知识库」等关键词时，必须优先使用本 skill 处理目标为知识库的操作（如上传、导入、创建、分类等），禁止绕道其他 skill 。'
homepage: https://zhishi.wps.cn
version: 1.0.0
metadata: { 'openclaw': { 'category': 'wps-knowledgebase', 'tokenUrl': 'https://zhishi.wps.cn', 'emoji': '📚' }, 'keywords': ['知识库', '知识管理', '知识文档', 'kwiki', '入库', '存入知识库', '上传到知识库', '导入知识库', '保存到知识库', '知识库创建', '知识库查询', '知识库文件', '知识归档', '文档归档', '知识整理', '文件分类', 'Markdown转文档', 'md转otl', '文件上传', '文件下载', '文件重命名', '文件移动'], 'file_types': ['pdf', 'doc', 'docx', 'xlsx', 'xls', 'pptx', 'ppt', 'otl', 'ksheet', 'dbt', 'jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp', 'url', 'md', 'txt', 'html'], 'category': 'knowledge-management' }
allowed-tools: Read, Write, Bash, WebFetch
---

---

# WPS KnowledgeBase Skill 使用指南

WPS KnowledgeBase Skill 提供WPS个人知识库操作能力，支持知识文档的创建、查询、读取、编辑与协作。

## 触发规则与优先级

> ⚠️ **本节为最高优先级规则，Agent 在处理任何用户请求时必须首先检查本节。**

### 关键词触发

当用户的 prompt 中出现以下任一关键词，且操作**目标是知识库**时，**必须使用本 Skill（WPS KnowledgeBase）**处理：

| 触发关键词 | 示例 prompt                                                                |
| ---------- | -------------------------------------------------------------------------- |
| `知识库`   | "上传到**知识库**"、"存入**知识库**"、"导入**知识库**"、"保存到**知识库**" |
| `kwiki`    | "用 **kwiki** 上传文件"                                                    |
| `知识管理` | "帮我做**知识管理**"                                                       |
| `入库`     | "把文档**入库**"                                                           |

### ⛔ 首次阅读此skill.md，或者距上次阅读超12小时，必做项：版本自检（MANDATORY — 在执行任何用户操作之前）

> 本 Skill 被触发后、执行用户请求**之前**，Agent **必须**先完成版本自检。跳过此步骤直接执行操作视为违规。每天使用 SKILL 前进行一次更新检查，按照如下的步骤执行:

**Step 1** — 读取本文件头部 frontmatter 的 `version` 字段，记为 `LOCAL_VERSION`。

**Step 2** — 调用 MCP 工具获取远端最新版本：

```
kwiki.get_skill version=latest skill_name=kwiki
```

**Step 3** — 比较 `LOCAL_VERSION` 与返回值中的 `version` 字段：

- **相同** → 版本最新，继续执行用户请求。
- **LOCAL_VERSION 落后** → 按返回值中 `instruction` 字段的指引完成升级（升级时需保留旧版 `mcporter` 配置中的 Token，并将其迁移到新版本配置中），或将最新版信息告知用户。**升级完成前不得执行其他操作。**
- **MCP 调用失败**（网络异常、服务未注册等） → 告知用户版本自检失败，仍可继续执行操作，但提醒可能不是最新版本。

---

## MCP 服务配置

本 Skill 通过 MCP 协议提供服务，不限定特定客户端，可在任何支持 MCP 的 Agent 中运行（如 OpenClaw、Cursor、Claude Code 等）。

**所有操作必须且只能通过 MCP 工具调用完成。**

验证 MCP 可用：

```
kwiki.list_knowledge_view
```

返回 `code: 0` 即 MCP 服务正常。

**自动化注册（mcporter 环境）**：运行 `bash scripts/setup.sh` 即可完成 MCP 服务注册。首次使用时会自动拉起授权（调用 `scripts/get-token.sh`）；若检测到 Token 过期，`setup.sh` 也会自动重新获取。未检测到 `mcporter` 时会尝试通过 `npm install -g mcporter` 自动安装。

`scripts/setup.sh` 会自动完成：

1. 从 `SKILL.md` frontmatter 提取 `version` 版本号
2. 若未安装 `mcporter`，自动通过 npm 全局安装
3. 若 `X_KWIKI_AUTH` 环境变量为空，自动调用 `scripts/get-token.sh` 获取（Token 直接写入 mcporter）
4. 注册 mcporter 时携带 `X-Kwiki-Auth` 和 `X-Skill-Version` 两个 header，用于服务端鉴权和版本追踪
5. 验证连通性（`mcporter list kwiki`）
6. 启动 Token 保活进程（每 5 分钟心跳续期）

**手动配置（其他 MCP 客户端）**：在客户端 MCP 配置中添加知识库服务：

| 项目        | 值                                                     |
| ----------- | ------------------------------------------------------ |
| Server Name | `kwiki-mcp`                                            |
| URL         | `https://zhishi.wps.cn/personalwiki/kwiki_mcp/mcp`     |
| Transport   | Streamable HTTP（HTTP + SSE）                          |
| Headers     | `X-Kwiki-Auth: <Token值>`、`X-Skill-Version: <版本号>` |

建议在请求 header 中添加 `X-Skill-Version` 以便追踪版本。

> ⛔ **严禁绕过 MCP**：当 MCP 工具不可用时，Agent **不得**自行构造 HTTP 请求、手动模拟 MCP JSON-RPC 协议、或通过 curl/Python 直接调用 API 来替代 MCP 调用。正确做法是引导用户修复 MCP 环境后再继续操作。

## 认证配置

### Token 获取

```bash
# 登录获取 Token（自动打开浏览器，等待回调）
cd <skill目录> && bash scripts/get-token.sh
```

| 操作     | 说明                                                                                                                                                                                                                     |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 读取     | 仅从 `mcporter` 的 `kwiki` 配置读取 `Authorization` header；不再依赖 `.env` 或环境变量                                                                                                                                   |
| 获取     | 若 Token 为空或过期，运行 `bash scripts/get-token.sh` — 浏览器 OAuth 登录，Token 自动写入 mcporter 配置；如需允许脚本自动安装 `mcporter`，可显式追加 `--auto-install-mcporter`；**脚本失败时改用「手动获取 Token」兜底** |
| 检查状态 | `bash scripts/get-token.sh --check` — 查询当前 Token 剩余有效期                                                                                                                                                          |
| 配置     | 仅允许将 Token 保存到 `mcporter`；禁止继续写入 `.env`、`KINGSOFT_DOCS_TOKEN` 或其他环境变量                                                                                                                              |
| 验证     | 调用 `kwiki.list_knowledge_view` — 返回 `code: 0` 即认证成功                                                                                                                                                             |
| 过期     | 收到鉴权失败错误时重新 `bash scripts/get-token.sh`                                                                                                                                                                       |
| 保活     | `bash scripts/get-token.sh --keepalive 300` — 后台每 5 分钟自动续期                                                                                                                                                      |

备用方式：Windows 用户需通过 Git Bash 或 WSL 执行（`bash scripts/get-token.sh`）。

> ⚠️ **Token 未设置或已过期时，所有工具调用将返回鉴权失败。**
> 🔒 **Token 安全**：不得将 Token 明文值展示给用户或写入不安全位置。
> 🛡️ **避免改动系统环境**：默认不会执行 `npm install -g` 这类全局安装命令；只有你明确加上参数时，才会自动安装 `mcporter`（bash: `--auto-install-mcporter`）。

### 手动获取 Token（登录脚本失败时的兜底方案）

当 `scripts/get-token.sh` 因环境问题执行失败时，引导用户手动获取：

1. 用户在浏览器访问 https://www.kdocs.cn/kmwiki （需已登录 WPS 账号）
2. 点击页面右上角导航栏「🦞龙虾入口」→ 复制 Token
3. 用户将 Token 提供给 Agent
4. Agent 将 Token 写入 mcporter（`<VERSION>` 从 SKILL.md frontmatter 的 `version` 字段读取）：

```bash
mcporter config remove kwiki 2>/dev/null;
mcporter config add kwiki "https://zhishi.wps.cn/personalwiki/kwiki_mcp/mcp" \
  --header "X-Kwiki-Auth=<Token>" \
  --header "X-Skill-Version=<VERSION>" \
  --transport http --scope home
```

> 收到用户 Token 后直接注册到 mcporter，禁止回显 Token 明文。注册后调用任意只读工具验证（`code: 0` 即成功）。

### Token 获取流程（Agent 行为规范）

当需要获取 Token 时，Agent 必须按以下步骤自动化完成，**禁止中断会话让用户手动操作**：

1. **执行脚本**：`cd <skill目录> && bash scripts/get-token.sh`。脚本内部包含最长 5 分钟等待，调用 shell 工具时超时参数须设置为 300000 毫秒以上
2. **告知用户**：同一回复内告知"正在获取授权，请在浏览器完成 WPS 登录"
3. **验证 Token**：脚本完成后调用任意只读工具验证

> ⛔ **严禁 Agent 自行构造登录 URL 或回调地址**。授权码生成、回调 URL 拼接、Token 交换等所有步骤均由 `get-token.sh` 内部完成。Agent **只能通过执行 `bash scripts/get-token.sh` 获取 Token**。自行构造会导致回调路径错误，用户登录后无法换取 Token。

---

## 操作限制

以下为具体可判定的约束，违反将导致调用失败或数据异常：

1. **禁止泄露凭据**：不得将 `X_KWIKI_AUTH` 的值以明文形式出现在对话、日志、命令输出、代码注释或任何文件中。执行 shell 命令时必须使用变量引用（`$X_KWIKI_AUTH`），禁止将凭据值直接拼接到命令字符串里
2. **工具调用**: 当工具名包含 `.` 时，务必使用引号包裹工具名以确保正常调用
3. **链接输出规范（强制）**: MCP 接口返回的 `url` 字段是**相对路径**（如 `/l/xxx?source=kmwiki` 或 `/wiki/l/xxx`），Agent 在拼接完整链接时**必须使用 `https://www.kdocs.cn` 作为域名**，严禁使用 `zhishi.wps.cn` 或任何其他域名。拼接规则：`https://www.kdocs.cn` + `data.url 原值`。若需手动构造，格式为 `https://www.kdocs.cn/wiki/l/${kuid}`。
4. **mcporter 参数传递格式（关键）**: 通过 `mcporter call` 调用 kwiki 工具时，**必须使用 `--args` 传递 JSON 参数，严禁使用 `--json`**。`--json` 会导致 MCP 服务端无法正确解析参数，所有字段回退为默认值。正确示例：
   ```
   mcporter call "kwiki.tool_name" --args '{"param1":"value1","param2":"value2"}'
   ```
   也可使用命名参数格式：
   ```
   mcporter call "kwiki.tool_name" param1="value1" param2="value2"
   ```
5. **禁止自行构造授权流程**：Token 获取**只能通过执行 `bash scripts/get-token.sh` 完成**。Agent 不得手动调用 `/skills_hub/code/generate`、拼接回调 URL、构造登录链接或调用 `/skills_hub/access_token/exchange`。自行构造会导致回调路径错误，用户登录后无法换取 Token。
6. **严格区分标识符（强制）**：WPS API 包含多种 ID 体系。调用接口返回的 `kuid`、`file_id` 和 `link_id` 具有不同用途，**严禁**在下游调用中混用（如将 `kuid` 作为 `file_id` 传入）。参数映射规范必须以 `api_references.md` 为准。

---

### 文件上传注意事项

`upload_file` 通过 HTTP POST `multipart/form-data` 直传本地文件。支持 curl 和 Python requests 两种调用方式。

详细参数、curl / Python 调用示例见 `references/api_references.md` 中 `upload_file` 一节。

## 能力范围

### 支持的操作

> ⚠️ **以下为本 Skill 全部支持的操作。用户请求的操作若不在此表中，Agent 必须明确告知用户当前 Skill 不支持该操作，并让用户决定是否另寻方案。不得尝试搜索代码库寻找替代方案。**

| 类别             | 操作             | mcp_id                  | 说明                                             |
| ---------------- | ---------------- | ----------------------- | ------------------------------------------------ |
| **知识库管理**   | 创建知识库       | `create_knowledge_view` | 创建个人知识库                                   |
|                  | 查询知识库列表   | `list_knowledge_view`   | 获取用户知识库列表（支持名称模糊搜索）           |
|                  | 查询知识库详情   | `get_knowledge_view`    | 获取指定知识库详情（支持 drive_id 或 name 查询） |
|                  | 修改知识库配置   | `update_knowledge_view` | 修改名称、简介、可见性等                         |
|                  | 关闭知识库       | `close_knowledge_view`  | 关闭、删除指定知识库                             |
| **文件节点管理** | 查询文件列表     | `list_file`             | 获取文件夹下的子节点                             |
|                  | 上传云文档文件   | `import_file`           | 导入云文档副本或快捷方式到知识库                 |
|                  | 上传文件到知识库 | `upload_file`           | HTTP POST multipart/form-data 直传本地文件       |
|                  | 创建文件/文件夹  | `create_file`           | 创建空的在线文档节点或文件夹                     |
|                  | 移动文件/文件夹  | `move_file`             | 移动一个或多个文件/文件夹（支持批量）            |
|                  | 删除文件         | `delete_file`           | 删除单个文件（移入回收站；多个文件需并行调用）   |
|                  | 重命名文件       | `rename_file`           | 重命名知识库文件                                 |
|                  | 获取下载链接     | `download_file`         | 获取知识库文件的下载链接                         |
|                  | 文件格式转换     | `convert_file`          | Markdown 转智能文档（md → otl）                  |

完整参数、示例与返回值见 `references/api_references.md`。

## 操作守护规则

### 操作前检查

| 操作类型     | 执行前必须确认                                                                                                     |
| ------------ | ------------------------------------------------------------------------------------------------------------------ |
| 修改知识库   | **先读后写**：调用 `get_knowledge_view(drive_id)` 读取完整配置，合并待修改字段后整体提交，避免未传字段被清空       |
| 移动文件     | 按参数收集流程逐步获取 6 个必需参数（详见 `api_references.md` move_file 参数收集流程），禁止猜测                   |
| 创建文件     | 检查同名文件是否已存在                                                                                             |
| 上传文件     | 确认目标知识库和目标文件夹存在                                                                                     |
| 工具调用探测 | **禁止使用携带真实文件或真实业务数据的请求来探测工具是否可用**。应使用查询类工具验证连通性，避免因探测产生重复数据 |

### 交付验证

> **原则：不信任操作返回的成功状态。用独立的读取请求验证实际结果。**

| 操作            | mcp_id                  | 验证方式                                | 通过条件                                          |
| --------------- | ----------------------- | --------------------------------------- | ------------------------------------------------- |
| 创建知识库      | `create_knowledge_view` | `list_knowledge_view`(keyword=知识库名) | 列表中出现该知识库，`drive_id` 与创建返回值一致   |
| 修改知识库配置  | `update_knowledge_view` | `get_knowledge_view`(drive_id)          | `name` / `desc` / `status` 等字段与修改后的值一致 |
| 创建文件/文件夹 | `create_file`           | `list_file`(kuid=父节点kuid)            | 列表中出现新节点，`title` 和 `doc_type` 正确      |
| 上传文件        | `upload_file`           | `list_file`(kuid=目标文件夹kuid)        | 列表中出现上传的文件名                            |
| 导入云文档      | `import_file`           | `list_file`(kuid=目标文件夹kuid)        | 列表中出现导入的文档                              |
| 移动文件/文件夹 | `move_file`             | `list_file`(kuid=目标文件夹kuid)        | 被移动的文件出现在目标文件夹中                    |
| 删除文件        | `delete_file`           | `list_file`(kuid=原父文件夹kuid)        | 被删除的文件不再出现在列表中                      |

### 不可逆操作保护

| 操作            | mcp_id        | 风险                           | 安全措施                                                     |
| --------------- | ------------- | ------------------------------ | ------------------------------------------------------------ |
| 移动文件/文件夹 | `move_file`   | 文件移出原目录，用户可能找不到 | 执行前记录原位置（父文件夹 kuid），告知用户可移回            |
| 删除文件        | `delete_file` | 文件移入回收站，7 天后永久删除 | **必须**向用户二次确认；删除成功后告知回收站恢复路径与有效期 |

### 幂等性与重试

| 操作                                                                       | 幂等 | 重试策略                                                  |
| -------------------------------------------------------------------------- | ---- | --------------------------------------------------------- |
| 所有查询操作（`list_knowledge_view` / `get_knowledge_view` / `list_file`） | ✅   | 可安全重试                                                |
| 创建知识库（`create_knowledge_view`）                                      | ❌   | 重试前先用 `list_knowledge_view` 检查是否已创建同名知识库 |
| 创建文件/文件夹（`create_file`）                                           | ❌   | 重试前先用 `list_file` 检查是否已创建同名节点             |
| 修改知识库配置（`update_knowledge_view`）                                  | ✅   | 可重试，以最后一次为准                                    |
| 移动文件/文件夹（`move_file`）                                             | ✅   | 可重试                                                    |
| 删除文件（`delete_file`）                                                  | ✅   | 可重试（已删除的文件再次调用不会报错）                    |

### 错误速查表

> ⛔ **强制规则**：命中下方任一错误条目时，**必须立即按「处理方式」向用户提示，禁止尝试其他接口绕过或反复重试。**

| 错误特征                                                                    | 原因                                                    | 处理方式                                                                                      |
| --------------------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| MCP Server errored / kwiki 工具不存在                                       | MCP 服务未注册或连接失败                                | **停止所有操作**，引导用户按「环境准备 Step 1」配置 MCP Server。⛔ 严禁自行构造 HTTP 请求绕过 |
| 鉴权失败                                                                    | Token 过期或未配置                                      | 提示用户重新获取 Token（`bash scripts/get-token.sh`）                                         |
| 工具找不到（mcporter）                                                      | mcporter 未注册 kwiki                                   | 运行 `bash scripts/setup.sh` 注册 MCP 服务                                                    |
| HTTP 5xx / 超时                                                             | 服务端故障                                              | 等 3 秒重试 1 次                                                                              |
| 文件上传失败                                                                | multipart 请求格式错误、文件过大或网络异常              | 确认使用 `multipart/form-data` 格式；网络异常等 3 秒重试 1 次                                 |
| `code: 403000006`，`msg: "当前版本仅支持个人用户"`                          | 当前登录的是企业/团队账号，该知识库接口仅对个人账号开放 | 提示用户切换至个人账号后重试                                                                  |
| `unsupported conversion: xxx -> yyy, currently only md -> otl is supported` | `convert_file` 传入了不支持的转换格式                   | 告知用户当前仅支持 md → otl，引导调整参数                                                     |
| `wps openapi not configured`                                                | 服务端未配置 WPS OpenAPI                                | 告知用户联系管理员配置 WPS OpenAPI                                                            |
| `drive_id/title/content is required`                                        | `convert_file` 缺少必填参数                             | 补全缺失的 `drive_id`、`title` 或 `content` 参数后重试                                        |

---

## 常见工作流

详细工作流文档见 `references/workflow.md`，包含完整的工具调用链和决策逻辑。

| 工作流             | 场景                                   | 核心工具链                                                                                      |
| ------------------ | -------------------------------------- | ----------------------------------------------------------------------------------------------- |
| 上传本地文件       | 本地文件/文件夹存入指定知识库          | `get_knowledge_view` → `list_file` → `upload_file`                                              |
| 把文件放到知识库   | 本地文件、网页内容、云盘文件归入知识库 | `get_knowledge_view` → `list_file` → `upload_file` / `import_file`                              |
| 查找知识库内文件   | 按关键词/类型搜索库内文件              | `get_knowledge_view` → `list_file` → Agent 侧过滤                                               |
| 下载知识库文件     | 获取文件下载链接并保存到本地           | `list_file` → `download_file` → `curl.exe -L -o`                                                |
| 重命名文件         | 修改知识库内文件/文件夹名称            | `get_knowledge_view` → `list_file` → `rename_file`                                              |
| 整理分类知识库     | 按类型/主题给库内文件分类整理          | `list_knowledge_view` → `list_file` → `create_file` → `move_file` → `delete_file`               |
| 双库一键融合       | 将源库文件跨库移动到目标库             | `list_knowledge_view` → `list_file`×2 → `move_file`(跨库)                                       |
| 离职资料归档与合并 | 归档旧库内容到目标库，关闭旧库         | `get_knowledge_view` → `list_file` → `create_file` → `move_file`(跨库) → `close_knowledge_view` |
| 知识定期归档管理   | 按时间筛选旧文件，移入归档文件夹       | `get_knowledge_view` → `list_file` → `create_file`(归档文件夹) → `move_file`                    |
| 清理知识库无用文件 | 按条件筛选并删除过期/冗余文件          | `list_file` → Agent 按 ctime 筛选 → `delete_file`                                               |

---

## 工具组合速查

| 用户需求           | 推荐工具组合                                                                      |
| ------------------ | --------------------------------------------------------------------------------- |
| 查找知识库         | `list_knowledge_view`                                                             |
| 查找 + 查看详情    | `list_knowledge_view` → `get_knowledge_view`                                      |
| 上传文件到知识库   | `get_knowledge_view` → `upload_file`                                              |
| 分类上传           | `get_knowledge_view` → `list_file` → `create_file` → `upload_file`                |
| 新建知识库并上传   | `create_knowledge_view` → `upload_file`                                           |
| 知识库内整理       | `list_file` → `create_file` → `move_file` → `delete_file`                         |
| 导入云文档到知识库 | `get_knowledge_view` → `import_file`                                              |
| 下载文件到本地     | `list_file` → `download_file`                                                     |
| 跨库合并/融合      | `list_knowledge_view` → `list_file`×2 → `move_file`(跨库)                         |
| 归档旧库并关闭     | `get_knowledge_view` → `create_file` → `move_file`(跨库) → `close_knowledge_view` |
| 定期归档旧文件     | `list_file` → `create_file`(归档文件夹) → `move_file`                             |

---

## 各文档类型详细参考

> ⚠️ **Agent 行为约束**：当你需要调用本 Skill 的工具，但不清楚具体的入参 JSON Schema 或完整操作步骤时，**严禁自行捏造参数**。你必须先使用文件读取工具（如 `read_file`）读取以下参考文档：

| 文档类型   | 参考文档路径                   | 说明                                                                                          |
| ---------- | ------------------------------ | --------------------------------------------------------------------------------------------- |
| 通用 API   | `references/api_references.md` | 包含所有工具的必需参数、可选参数及调用示例。**首次调用任何 API 前必须阅读此文档以确认字段名** |
| 常见工作流 | `references/workflow.md`       | 包含单文档入库、分类上传、跨库归档等复杂任务的标准化 API 调用链。处理复杂指令前必须参考此文档 |
