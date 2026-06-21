# lingxi-skills

> WPS 灵犀 AgentSkill 合集 — 54 个技能模块，覆盖文档处理、内容创作、知识管理、学习辅助、网页自动化等场景。

个人维护的灵犀技能仓库，持续更新。欢迎 Star 和 Issue。

---

## 快速开始

```powershell
git clone https://github.com/PlumeLyo/lingxi-skills.git
cd lingxi-skills
.\install.ps1 --all
```

所有技能安装到 `%APPDATA%\WPS 灵犀\serverdir\skills\`，灵犀会自动识别。

## 按需安装

## 快速安装

```powershell
git clone https://github.com/PlumeLyo/lingxi-skills.git
cd lingxi-skills
.\install.ps1 --all
```

### 按需安装

```powershell
# 安装单个技能
.\install.ps1 docx

# 安装多个技能
.\install.ps1 docx pptx xlsx

# 安装整个分类
.\install.ps1 --cat content

# 查看所有分类及技能
.\install.ps1 --categories
```

### 其他操作

```powershell
.\install.ps1 --list                # 列出所有可用技能
.\install.ps1 --update docx         # 更新已安装的技能
.\install.ps1 --uninstall docx      # 卸载指定技能
```

> 安装目标：`%APPDATA%\WPS 灵犀\serverdir\skills\`，安装后技能展平到根目录。

---

## 技能分类

### document — 文档处理

| 技能 | 说明 | 安装 |
|------|------|------|
| [docx](document/docx/) | 创建、编辑 Word 文档，支持样式、公式、表格 | `.\install.ps1 docx` |
| [xlsx](document/xlsx/) | 创建、编辑 Excel 表格，支持公式重算和格式化 | `.\install.ps1 xlsx` |
| [pptx](document/pptx/) | 创建、编辑 PPT 演示文稿，支持主题和模板 | `.\install.ps1 pptx` |
| [pdf](document/pdf/) | PDF 读取、合并、拆分、OCR、水印等 | `.\install.ps1 pdf` |
| [wps_docs](document/wps_docs/) | WPS 云文档（表格、智能文档、多维表） | `.\install.ps1 wps_docs` |

### content — 内容创作

| 技能 | 说明 | 安装 |
|------|------|------|
| [content-creator](content/content-creator/) | 内容创作起点，风格画像→大纲→研究→写作→定稿 | `.\install.ps1 content-creator` |
| [content-digest](content/content-digest/) | 任意内容提炼为结构化知识笔记 | `.\install.ps1 content-digest` |
| [wechat-publisher](content/wechat-publisher/) | WPS 笔记排版导出为公众号 HTML | `.\install.ps1 wechat-publisher` |
| [xiaohongshu-note-creator](content/xiaohongshu-note-creator/) | 文章/笔记转小红书图文方案 | `.\install.ps1 xiaohongshu-note-creator` |
| [short-video-copywriter](content/short-video-copywriter/) | 长文改写为短视频口播文案+分镜脚本 | `.\install.ps1 short-video-copywriter` |
| [deep_research](content/deep_research/) | 多来源深度调研、交叉核验与研究写作 | `.\install.ps1 deep_research` |
| [paper-writer](content/paper-writer/) | 学术论文写作助手 | `.\install.ps1 paper-writer` |
| [paper-researcher](content/paper-researcher/) | 论文搜索、下载、精读分析 | `.\install.ps1 paper-researcher` |
| [solar-term-article](content/solar-term-article/) | 二十四节气公众号文案（节气×心理学） | `.\install.ps1 solar-term-article` |
| [solar-term-illustration](content/solar-term-illustration/) | 二十四节气工笔重彩风格插画 | `.\install.ps1 solar-term-illustration` |
| [xzsk-publisher](content/xzsk-publisher/) | 彳亍时刻公众号四模板排版（光迹/星光/光境/余温） | `.\install.ps1 xzsk-publisher` |

### knowledge — 知识与笔记

| 技能 | 说明 | 安装 |
|------|------|------|
| [session-sync](knowledge/session-sync/) | 会话收尾七层同步（增量→记忆→知识库→文件分流） | `.\install.ps1 session-sync` |
| [neat-freak](knowledge/neat-freak/) | 文档整洁+记忆同步，项目里程碑收尾 | `.\install.ps1 neat-freak` |
| [wps-note](knowledge/wps-note/) | MCP 工具读取、编辑和管理 WPS 笔记 | `.\install.ps1 wps-note` |
| [wps-knowledgebase](knowledge/wps-knowledgebase/) | WPS 个人知识库操作 | `.\install.ps1 wps-knowledgebase` |
| [ima-skill](knowledge/ima-skill/) | IMA 知识库笔记和知识文档管理 | `.\install.ps1 ima-skill` |
| [tag-organize](knowledge/tag-organize/) | 笔记标签整理（MCP + CLI 双模式） | `.\install.ps1 tag-organize` |
| [news-to-note](knowledge/news-to-note/) | 新闻智能解读，存入笔记并关联知识库 | `.\install.ps1 news-to-note` |
| [note-copilot](knowledge/note-copilot/) | 笔记协作助手，处理标记、逻辑检查 | `.\install.ps1 note-copilot` |
| [wps-note-intelligent-search](knowledge/wps-note-intelligent-search/) | 笔记深度搜索，混合检索+关联发现 | `.\install.ps1 wps-note-intelligent-search` |
| [doc-importer](knowledge/doc-importer/) | 本地文档批量导入到 WPS 笔记 | `.\install.ps1 doc-importer` |
| [web-importer](knowledge/web-importer/) | 网页/公众号/推文导入到 WPS 笔记 | `.\install.ps1 web-importer` |
| [literature-reader](knowledge/literature-reader/) | PDF 论文精读，生成结构化文献笔记 | `.\install.ps1 literature-reader` |

### learning — 学习辅助

| 技能 | 说明 | 安装 |
|------|------|------|
| [class-note-builder](learning/class-note-builder/) | 课堂资料整理为结构化学习笔记 | `.\install.ps1 class-note-builder` |
| [notes-to-flashcards](learning/notes-to-flashcards/) | 学习笔记转为复习卡片 | `.\install.ps1 notes-to-flashcards` |
| [notes-to-lesson-plan](learning/notes-to-lesson-plan/) | 笔记整理为讲解提纲 | `.\install.ps1 notes-to-lesson-plan` |
| [lecture-focus-extractor](learning/lecture-focus-extractor/) | 从长笔记中提取复习重点 | `.\install.ps1 lecture-focus-extractor` |
| [misconception-finder](learning/misconception-finder/) | 检查笔记中的理解错误和逻辑跳步 | `.\install.ps1 misconception-finder` |
| [prerequisite-gap-finder](learning/prerequisite-gap-finder/) | 找出学不下去的前置知识缺口 | `.\install.ps1 prerequisite-gap-finder` |
| [study-note-linker](learning/study-note-linker/) | 新旧笔记关联 | `.\install.ps1 study-note-linker` |
| [live-transcript-summary](learning/live-transcript-summary/) | 边听边总结，实时整理录音转写 | `.\install.ps1 live-transcript-summary` |

### inspiration — 灵感引擎

| 技能 | 说明 | 安装 |
|------|------|------|
| [ie-engine](inspiration/ie-engine/) | 灵感引擎入口，记忆→连接→洞见 | `.\install.ps1 ie-engine` |
| [ie-retrieve-memory](inspiration/ie-retrieve-memory/) | 检索历史笔记中的知识和想法 | `.\install.ps1 ie-retrieve-memory` |
| [ie-connect-dots](inspiration/ie-connect-dots/) | 语义聚类，发现笔记间隐含连接 | `.\install.ps1 ie-connect-dots` |
| [ie-generate-insight](inspiration/ie-generate-insight/) | 分析结果转化为灵感文本 | `.\install.ps1 ie-generate-insight` |
| [ie-recall-memory](inspiration/ie-recall-memory/) | 写新内容时召回最相关的旧笔记 | `.\install.ps1 ie-recall-memory` |

### creative — 创作工具

| 技能 | 说明 | 安装 |
|------|------|------|
| [novel-writer](creative/novel-writer/) | AI 陪伴式长篇小说创作（MCP+CLI） | `.\install.ps1 novel-writer` |
| [image-gen](creative/image-gen/) | AI 图像生成（文生图/图生图，多服务商） | `.\install.ps1 image-gen` |
| [web_builder](creative/web_builder/) | 从零构建网站和 Web 应用 | `.\install.ps1 web_builder` |
| [skill_creator](creative/skill_creator/) | 创建、编辑、审查 AgentSkill | `.\install.ps1 skill_creator` |
| [coding-assistant](creative/coding-assistant/) | 多平台编码助手，自动生成技术文档 | `.\install.ps1 coding-assistant` |
| [media-insight](creative/media-insight/) | 新媒体内容深度分析 | `.\install.ps1 media-insight` |

### platform — 平台与工具

| 技能 | 说明 | 安装 |
|------|------|------|
| [browser](platform/browser/) | 浏览器自动化，信息检索、网页抓取 | `.\install.ps1 browser` |
| [wps365](platform/wps365/) | WPS 协作（IM）、WPS 邮箱 | `.\install.ps1 wps365` |
| [wpsnote-beautifier](platform/wpsnote-beautifier/) | WPS 笔记智能美化排版 | `.\install.ps1 wpsnote-beautifier` |
| [stock_analysis](platform/stock_analysis/) | 股票和公司金融数据分析 | `.\install.ps1 stock_analysis` |
| [dbsheet](platform/dbsheet/) | WPS 多维表操作与管理 | `.\install.ps1 dbsheet` |
| [aihot](platform/aihot/) | 中文 AI 资讯查询日报 | `.\install.ps1 aihot` |
| [hv-analysis](platform/hv-analysis/) | 假日分析报告生成 | `.\install.ps1 hv-analysis` |
| [note-calendar](platform/note-calendar/) | WPS 笔记与 macOS 日历双向联动 | `.\install.ps1 note-calendar` |

---

## 目录结构

```
lingxi-skills/
├── document/        # 文档处理（5）
├── content/         # 内容创作（11）
├── knowledge/       # 知识与笔记（12）
├── learning/        # 学习辅助（8）
├── inspiration/     # 灵感引擎（5）
├── creative/        # 创作工具（6）
├── platform/        # 平台与工具（8）
├── install.ps1      # 安装脚本
├── README.md
└── License.txt
```

每个技能子目录：

```
skill-name/
├── SKILL.md              # 技能定义文件（必须）
├── references/           # 参考文档、模板（可选）
├── scripts/              # 脚本文件（可选）
├── templates/            # 模板文件（可选）
└── assets/               # 静态资源（可选）
```

## 技能定义格式

```yaml
---
name: my-skill
description: "技能描述，用于触发匹配"
---

# 技能标题

技能的完整使用说明、工作流程、代码示例等。
```

## 维护记录

- **2026-06-21** 新增 session-sync、neat-freak（knowledge）、xzsk-publisher（content），更新 README
- **2026-05-27** 按分类整理仓库结构（7 个分类目录）
- **2026-05-27** 初始提交，52 个技能 + 安装脚本

## 许可证

见 [License.txt](License.txt)
