# lingxi-skills

WPS 灵犀（Lingxi）AgentSkill 合集，包含 52 个技能模块，覆盖文档处理、内容创作、知识管理、网页自动化等场景。

## 快速安装

### 一键安装全部

```powershell
git clone https://github.com/PlumeLyo/lingxi-skills.git
cd lingxi-skills
.\install.ps1 --all
```

### 按需安装指定技能

```powershell
.\install.ps1 docx pptx xlsx
```

### 列出所有可用技能

```powershell
.\install.ps1 --list
```

### 其他操作

```powershell
.\install.ps1 --update docx        # 更新已安装的技能（覆盖）
.\install.ps1 --uninstall docx     # 卸载指定技能
```

> 安装目标：`%APPDATA%\WPS 灵犀\serverdir\skills\`，覆盖前建议备份。

---

## 技能一览

> 每个技能下方的安装命令需在 `lingxi-skills` 目录下执行。

### 文档处理

| 技能 | 说明 | 安装 |
|------|------|------|
| [docx](docx/) | 创建、编辑 Word 文档（.docx），支持样式、公式、表格 | `.\install.ps1 docx` |
| [xlsx](xlsx/) | 创建、编辑 Excel 表格，支持公式重算和格式化 | `.\install.ps1 xlsx` |
| [pptx](pptx/) | 创建、编辑 PPT 演示文稿，支持主题和模板 | `.\install.ps1 pptx` |
| [pdf](pdf/) | PDF 读取、合并、拆分、OCR、水印等操作 | `.\install.ps1 pdf` |
| [wps_docs](wps_docs/) | WPS 云文档（表格、智能文档、多维表）操作 | `.\install.ps1 wps_docs` |

### 内容创作

| 技能 | 说明 | 安装 |
|------|------|------|
| [content-creator](content-creator/) | 内容创作起点，风格画像→大纲→研究→写作→定稿 | `.\install.ps1 content-creator` |
| [content-digest](content-digest/) | 任意内容提炼为结构化知识笔记，保存到 WPS 笔记 | `.\install.ps1 content-digest` |
| [wechat-publisher](wechat-publisher/) | WPS 笔记排版导出为微信公众号 HTML | `.\install.ps1 wechat-publisher` |
| [xiaohongshu-note-creator](xiaohongshu-note-creator/) | 文章/笔记转小红书图文方案 | `.\install.ps1 xiaohongshu-note-creator` |
| [short-video-copywriter](short-video-copywriter/) | 长文改写为短视频口播文案+分镜脚本 | `.\install.ps1 short-video-copywriter` |
| [deep_research](deep_research/) | 多来源深度调研、交叉核验与研究写作 | `.\install.ps1 deep_research` |
| [paper-writer](paper-writer/) | 学术论文写作助手 | `.\install.ps1 paper-writer` |
| [paper-researcher](paper-researcher/) | 论文搜索、下载、存入 WPS 笔记、精读分析 | `.\install.ps1 paper-researcher` |
| [solar-term-article](solar-term-article/) | 二十四节气公众号文案（节气×心理学融合） | `.\install.ps1 solar-term-article` |
| [solar-term-illustration](solar-term-illustration/) | 二十四节气工笔重彩风格插画生成 | `.\install.ps1 solar-term-illustration` |

### 知识与笔记

| 技能 | 说明 | 安装 |
|------|------|------|
| [wps-note](wps-note/) | 通过 MCP 工具读取、编辑和管理 WPS 笔记 | `.\install.ps1 wps-note` |
| [wps-knowledgebase](wps-knowledgebase/) | WPS 个人知识库（zhishi.wps.cn）操作 | `.\install.ps1 wps-knowledgebase` |
| [ima-skill](ima-skill/) | IMA 知识库（ima.qq.com）笔记和知识文档管理 | `.\install.ps1 ima-skill` |
| [tag-organize](tag-organize/) | 笔记标签整理，支持 MCP 和 CLI 双模式 | `.\install.ps1 tag-organize` |
| [news-to-note](news-to-note/) | 新闻智能解读，存入笔记并关联知识库 | `.\install.ps1 news-to-note` |
| [note-copilot](note-copilot/) | 笔记协作助手，处理标记、逻辑检查 | `.\install.ps1 note-copilot` |
| [wps-note-intelligent-search](wps-note-intelligent-search/) | 笔记深度搜索，混合检索+关联发现 | `.\install.ps1 wps-note-intelligent-search` |
| [doc-importer](doc-importer/) | 本地文档批量导入到 WPS 笔记 | `.\install.ps1 doc-importer` |
| [web-importer](web-importer/) | 网页/公众号/推文导入到 WPS 笔记 | `.\install.ps1 web-importer` |
| [literature-reader](literature-reader/) | PDF 论文精读，生成结构化文献笔记 | `.\install.ps1 literature-reader` |

### 学习辅助

| 技能 | 说明 | 安装 |
|------|------|------|
| [class-note-builder](class-note-builder/) | 课堂逐字稿/零散资料整理为结构化学习笔记 | `.\install.ps1 class-note-builder` |
| [notes-to-flashcards](notes-to-flashcards/) | 学习笔记转为可主动回忆的复习卡片 | `.\install.ps1 notes-to-flashcards` |
| [notes-to-lesson-plan](notes-to-lesson-plan/) | 笔记整理为可讲给别人听的讲解提纲 | `.\install.ps1 notes-to-lesson-plan` |
| [lecture-focus-extractor](lecture-focus-extractor/) | 从长笔记中提取最值得复习的重点 | `.\install.ps1 lecture-focus-extractor` |
| [misconception-finder](misconception-finder/) | 检查学习笔记中的理解错误和逻辑跳步 | `.\install.ps1 misconception-finder` |
| [prerequisite-gap-finder](prerequisite-gap-finder/) | 找出学不下去的前置知识缺口 | `.\install.ps1 prerequisite-gap-finder` |
| [study-note-linker](study-note-linker/) | 把新笔记和已有旧笔记关联起来 | `.\install.ps1 study-note-linker` |
| [live-transcript-summary](live-transcript-summary/) | 边听边总结，实时整理录音转写内容 | `.\install.ps1 live-transcript-summary` |

### 灵感引擎

| 技能 | 说明 | 安装 |
|------|------|------|
| [ie-engine](ie-engine/) | 灵感引擎统一入口，串联记忆→连接→洞见完整流水线 | `.\install.ps1 ie-engine` |
| [ie-retrieve-memory](ie-retrieve-memory/) | 从历史笔记中检索过去的知识和想法 | `.\install.ps1 ie-retrieve-memory` |
| [ie-connect-dots](ie-connect-dots/) | 语义聚类、发现笔记间的隐含连接 | `.\install.ps1 ie-connect-dots` |
| [ie-generate-insight](ie-generate-insight/) | 将分析结果转化为可阅读的灵感文本 | `.\install.ps1 ie-generate-insight` |
| [ie-recall-memory](ie-recall-memory/) | 在写新内容时召回过去最相关的旧笔记 | `.\install.ps1 ie-recall-memory` |

### 创作工具

| 技能 | 说明 | 安装 |
|------|------|------|
| [novel-writer](novel-writer/) | AI 陪伴式长篇小说创作（MCP + CLI 双模式） | `.\install.ps1 novel-writer` |
| [image-gen](image-gen/) | AI 图像生成（文生图/图生图，多服务商） | `.\install.ps1 image-gen` |
| [web_builder](web_builder/) | 从零构建网站和 Web 应用 | `.\install.ps1 web_builder` |
| [skill_creator](skill_creator/) | 创建、编辑、审查 AgentSkill | `.\install.ps1 skill_creator` |
| [coding-assistant](coding-assistant/) | 多平台编码助手，自动生成技术文档 | `.\install.ps1 coding-assistant` |
| [media-insight](media-insight/) | 新媒体内容深度分析（抖音/小红书/视频号） | `.\install.ps1 media-insight` |

### 平台与工具

| 技能 | 说明 | 安装 |
|------|------|------|
| [browser](browser/) | 浏览器自动化，信息检索、网页抓取 | `.\install.ps1 browser` |
| [wps365](wps365/) | WPS 协作（IM）、WPS 邮箱操作 | `.\install.ps1 wps365` |
| [wpsnote-beautifier](wpsnote-beautifier/) | WPS 笔记智能美化排版 | `.\install.ps1 wpsnote-beautifier` |
| [stock_analysis](stock_analysis/) | 股票和公司金融数据分析 | `.\install.ps1 stock_analysis` |
| [dbsheet](dbsheet/) | WPS 多维表操作与管理 | `.\install.ps1 dbsheet` |
| [aihot](aihot/) | 中文 AI 资讯查询日报 | `.\install.ps1 aihot` |
| [hv-analysis](hv-analysis/) | 假日分析报告生成 | `.\install.ps1 hv-analysis` |
| [note-calendar](note-calendar/) | WPS 笔记与 macOS 日历双向联动 | `.\install.ps1 note-calendar` |

---

## 目录结构

```
skill-name/
├── SKILL.md              # 技能定义文件（必须）
├── references/           # 参考文档、模板、提示词（可选）
├── scripts/              # Python/JS/Shell 脚本（可选）
├── templates/            # 模板文件（可选）
└── assets/               # 静态资源（可选）
```

## 技能定义格式

每个技能的核心是 `SKILL.md`，采用 YAML frontmatter + Markdown 正文：

```yaml
---
name: my-skill
description: "技能描述，用于触发匹配"
---

# 技能标题

技能的完整使用说明、工作流程、代码示例等。
```

## 维护记录

- **2026-05-27** 初始提交，52 个技能 + 安装脚本
  - 删除：getnote、neat-freak（无关内容）
  - 合并：novel-writer-cli → novel-writer、tag-organize-cli → tag-organize
  - 清理：node_modules（8.8MB）、__pycache__（9 个目录）
  - 整理：17 个散落文件归入 references/scripts/

## 许可证

见 [License.txt](License.txt)
