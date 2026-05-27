# WPS KnowledgeBase Skill 常见工作流

本文档描述 Agent 在处理用户知识库操作请求时的常见工作流，包含完整的工具调用链和决策逻辑。

---

### 上传本地文件到知识库

**触发示例**：「把本地 XX 文件归档/上传/同步/放到 XX 库的 XX 文件夹」「把这些资料归档/上传/同步/放到 XX 库」「定时归档/上传/同步/放 XX 到 XX 库」

**流程**：

1. **获取知识库标识**：用户**精确提供**了完整知识库名称时，调用 `get_knowledge_view(name="准确名称")` 直接获取；仅提供**模糊关键词**或未指定时，调用 `list_knowledge_view(keyword="关键词")` 检索，若有多个结果则列出后询问用户
2. 如需放入子文件夹：
   - `list_file` 定位目标文件夹，获取其 `kuid`（用于 kwiki 操作）和 `file_id`（用于通用接口的 `parent_id`）
   - 放入根目录则 `parent_id="0"`
3. 按文件类型选择上传方式：

**常规文件（docx/pdf/pptx/xlsx 等）**：
`upload_file(drive_id=知识库drive_id, parent_link_id=目标文件夹link_id, files=本地文件)` — HTTP POST multipart/form-data 直传

**Markdown 文件（.md）**：

> 默认转为在线智能文档，保留格式和结构化内容。仅当用户明确要求"上传并保持 md 格式"时，才使用 `upload_file` 直接上传原始 `.md` 文件。

- 读取本地 `.md` 文件内容
- `convert_file(drive_id=知识库drive_id, title="文件名（不含后缀）", content=markdown原文)` 一步完成创建智能文档并写入内容
- 从 `list_file` 返回中获取 `link_id`，拼接在线链接

### 重命名知识库内的文件或文件夹

使用通用接口 `rename_file` 重命名知识库内的文件或文件夹：

1. `get_knowledge_view(name="知识库名")` 获取知识库的 `drive_id` 和 `kuid`
2. `list_file(kuid=知识库kuid)` 定位目标文件，获取 `file_id` 和 `drive_id`
3. `rename_file(drive_id=drive_id, file_id=file_id, dst_name="新名称")`
   - 文件须带后缀（如 `"新报告.docx"`）
   - 文件夹不带后缀（如 `"项目资料"`）

### 下载知识库文件到本地

**流程**：

1. `list_file(kuid=目标目录kuid)` 定位目标文件，获取 `kuid`、`title`、`doc_type`
2. `download_file(kuid=文件kuid)` 获取带签名的下载 URL（返回字段为 `download_url`）
3. **Agent 侧执行分发**：
   - 如果当前环境已注册本地执行工具，则调用工具执行 `curl -L -o "文件名" "download_url"` 进行下载
   - 如果无本地执行权限，则**向用户输出该下载链接或提供一条完整的 `curl` 命令**，并引导用户："文件已准备好，请点击链接下载，或在终端运行以下命令保存到本地"

> **注意**：`download_file` 返回的 `download_url` 带签名，可直接下载，无需登录态。
> 如遇受保护文件（SecureDocumentError / forbidProtectedFile），所有导出接口均无法操作，需提示用户。

### 把文件放到知识库

**触发示例**：「帮我把 XX 放到 XX 知识库」「把这些文件归档到 XX 库的 XX 文件夹」「帮我把本地文件放到 XX 库」「把公众号文章存入 XX 知识库」「把这个链接存到知识库里」

**流程**：

1. **定位知识库**：用户精确提供库名 → `get_knowledge_view(name=...)`；仅提供模糊关键词或未指定 → `list_knowledge_view(keyword=...)` 检索，多结果时列出询问用户，零结果时引导创建
2. **定位目标路径**：指定文件夹 → `list_file` 逐层查找，不存在则 `create_file(doc_type="folder")` 按层级创建；未指定 → 根目录
3. **按来源选择归档方式**：
   - **本地文件/文件夹** → 按「上传本地文件到知识库」流程逐个上传，保持子目录结构时递归创建文件夹
   - **网页内容** → 先用 `web_fetch`、`web_search` 或浏览器抓取网页内容转为 Markdown，再调用 `convert_file(drive_id=知识库drive_id, title="页面标题", content=markdown内容)` 转为智能文档存入知识库
   - **云盘已有文件** → `import_file(action="copy"/"shortcut")`
4. **确认结果**：`list_file` 返回存放路径与直达链接；批量时展示成功/失败明细

### 查找知识库内的文件

**触发示例**：「帮我找一下 XX 文件」「在 XX 库里找 XX 相关的资料」「我要找关于 XX 的文档」

**流程**：

1. **提取条件**：从用户指令中识别关键词、指定库名、文件类型等筛选条件
2. **定位搜索范围**：
   - 精确指定库名 → `get_knowledge_view(name=...)` 确认库存在，获取 `kuid`
   - 模糊关键词或未指定 → `list_knowledge_view(keyword=...)` 检索，多结果时列出询问用户
3. **遍历文件列表**：`list_file(kuid=知识库kuid)` 获取库内全部文件；如需递归子文件夹，继续用文件夹 `kuid` 调用 `list_file`
4. **Agent 侧过滤**：按用户关键词匹配 `title`，按 `doc_type` 过滤文件类型
5. **返回结果**：展示文件名、类型、创建时间、直达链接（`https://www.kdocs.cn/wiki/l/${kuid}`）；结果过多时提示用户按文件类型或时间范围二次筛选
6. **展示结果并询问用户** → 展示文件信息 + **主动询问是否下载到本地或打开查看（提供在线链接）**

- `list_file` 返回的 `kuid` 可用于 `download_file` 获取下载链接
- 根据文件类型选择下载方式，详见「下载知识库文件到本地」流程

### 整理分类知识库

**触发示例**：「帮我整理一下 XX 知识库」「把 XX 库里的文件按类型分类」

> ⚠️ **场景识别**：当用户明确提到「知识库」「库」「资料库」等关键词时，优先使用 `*` 系列接口完成整理/分类，确保知识库内部元数据（索引、搜索等）一致。

**流程**：

1. `list_knowledge_view(keyword="库名")` 搜索目标知识库，获取 `drive_id`、`group_id`、`kuid` 等关键标识
2. `list_file(kuid=知识库kuid)` 遍历根目录内容；如需递归遍历子文件夹，继续用文件夹的 `kuid` 调用 `list_file`。收集每个文件的 `kuid`、`title`、`doc_type` 信息
3. 列出需新建的分类文件夹、文件移动目标、建议删除的内容，明确标注操作影响范围，**提交用户确认后再执行**
4. 批量创建文件夹（`create_file`）→ 批量移动文件（`move_file`）→ 删除确认的冗余内容（`delete_file`），提示回收站恢复路径（7 天内可恢复）

### 双库一键融合

**触发示例**：「把 XX 库的资料同步到 XX 库」「合并这两个知识库」「把 A 库和 B 库合并」

**流程**：

1. `list_knowledge_view` 查询源库和目标库，获取各自的 `drive_id`、`group_id`、`kuid`
2. `list_file(kuid=源库kuid)` 盘点源库全部文件
3. `list_file(kuid=目标库kuid)` 盘点目标库，检查是否有同名文件冲突
4. **向用户展示合并方案**：列出待移动文件清单及同名冲突处理策略（跳过 / 覆盖 / 重命名），**等待确认**
5. `move_file(group_id=源库group_id, drive_id=源库drive_id, dest_drive_id=目标库drive_id, dest_parent_id="0", file_kuids=[...], space_kuid=源库kuid)` 跨库批量移动
6. `list_file(kuid=目标库kuid)` 验证文件已到达目标库

> **注意**：`dest_parent_id` 为必传参数，移到目标库根目录时传 `"0"`。

### 资料归档与合并

**触发示例**：「帮我把 XX 的知识库归档到 XX 库」「把 A 的资料合并到团队库 B」「归档 A 库并关闭」

**流程**：

1. `get_knowledge_view` 分别查询待归档库和目标库的详情
2. `list_file` 分别盘点两个库的文件，识别重复内容
3. 在目标库创建归档文件夹：`create_file(doc_type="folder", kuid=目标库kuid, title="XX归档")`
4. `list_file(kuid=目标库kuid)` 获取归档文件夹的 `file_id`
5. `move_file` 将待归档库的全部文件/文件夹跨库移入归档目录
6. （如有重复）`delete_file` 清理重复文件
7. **向用户确认后** `close_knowledge_view(drive_id=旧库drive_id)` 关闭旧库
8. `list_file(kuid=归档文件夹kuid)` 验证归档完整

> ⚠️ 关闭知识库不可恢复，必须向用户二次确认。

### 知识定期归档管理

**触发示例**：「每季度归档一次 XX 库的旧文件」「把 3 个月未修改的文件归档」「把 XX 库里过期的资料归档到 XX 文件夹」

**流程**：

1. `get_knowledge_view(name=...)` 定位目标知识库
2. `list_file(kuid=知识库kuid)` 遍历全库文件，收集 `kuid`、`title`、`ctime`
3. Agent 按 `ctime` 筛选：早于归档阈值（如 3 个月前）的文件列入归档清单
4. 创建时间维度归档文件夹：`create_file(doc_type="folder", kuid=知识库kuid, title="YYYY-QN归档")`
5. `list_file(kuid=知识库kuid)` 获取新文件夹的 `file_id`
6. `move_file` 将过期文件移入归档文件夹
7. `list_file(kuid=归档文件夹kuid)` 验证归档结果

### 清理知识库无用文件

**触发示例**：「清理 XX 库里 1 个月未修改的文件」「删掉 XX 库里的空文件夹」「把 XX 库里过期的资料清理一下」

**流程**：

1. `list_file(kuid=空间kuid)` 递归遍历全库，获取每个文件/文件夹的 `kuid`、`title`、`doc_type`、`ctime`
2. Agent 按 `ctime` 或用户指定条件筛选待删除文件
3. **向用户展示待删除清单并确认**
4. `delete_file(kuid=xxx)` 逐个删除（进入回收站，7 天内可恢复）
5. 空文件夹可同样通过 `delete_file` 删除

---

## 通用规则

以下规则适用于所有工作流：

1. **知识库查询优先**：任何涉及知识库的操作，第一步始终是获取知识库标识。用户精确提供了完整库名时用 `get_knowledge_view(name=...)`，仅有模糊关键词或未指定时用 `list_knowledge_view(keyword=...)` 检索，再由 Agent 按 `space_name` 进行名称匹配。
2. **模糊匹配多结果**：`list_knowledge_view` 返回多个匹配时，列出名称、简介、创建时间，询问用户选择。超过 5 条折叠分页。
3. **零匹配处理**：用户指定了知识库名称但列表中无任何 `space_name` 包含该关键词时，告知用户"未找到名为 XX 的知识库，是否为您创建？"。**严禁在此场景下列出其他不相关知识库供选择。**
4. **创建前必须确认（强制）**：调用 `create_knowledge_view` 或 `create_file` 创建知识库/文件夹**之前**，必须先向用户说明即将创建的内容并等待用户明确确认。**严禁跳过确认直接创建。** 此规则适用于所有创建场景，包括但不限于：目标知识库不存在需新建、已有知识库状态异常需重建、需要新建分类文件夹等。
5. **分类方案必须确认（强制）**：涉及文件分类上传时，Agent 拟定或用户指定的分类方案必须以表格形式完整展示，**等待用户明确回复确认后**才能开始创建文件夹和上传文件。严禁展示方案后在同一轮对话中直接执行。
6. **上传后验证**：上传完成后，调用 `list_file` 验证文件是否出现在目标位置。
7. **进度反馈**：批量操作时逐个反馈进度，不要静默等待全部完成。
8. **错误恢复**：单个文件上传失败不应中断整个流程，记录失败项，全部完成后汇总告知用户。
9. **链接输出规范**：MCP 返回的 `url` 是相对路径，拼接完整链接时**必须使用 `https://www.kdocs.cn` 作为域名**，严禁使用 `zhishi.wps.cn` 或从 MCP 服务端点推断域名。
10. **mcporter 调用格式**：通过 `mcporter call` 调用工具时，**必须使用 `--args` 传递 JSON 参数，严禁使用 `--json`**（`--json` 会导致参数丢失）。
11. **严格区分并校验 ID 字段（强制）**：各种查询接口会返回多种标识符，调用下游 API 时必须严格核对参数要求：`upload_file` 的父目录参数必须使用 `parent_link_id`；通用操作（如 `rename_file`）必须使用 `file_id`；大部分 Kwiki 体系内操作及页面拼接使用 `kuid`。**严禁**将 `kuid` 当作 `file_id` 或 `link_id` 传递，调用前务必二次检查当前持有的 ID 类型。
12. **同名文件冲突处理**：在执行上传（`upload_file`）、新建（`create_file`）或重命名（`rename_file`）遇到同名冲突报错时，Agent 应在文件名后自动追加数字（如 `文件名(1)`）进行重试，或向用户询问是否需要覆盖原始文件。
13. **空结果处理**：在调用 `list_file` 进行文件查找时，若返回结果为空，Agent 应明确告知用户"该目录下未找到符合条件的文件"，并主动建议用户更换搜索关键词或检查知识库名称。
