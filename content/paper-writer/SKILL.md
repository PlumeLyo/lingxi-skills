---
name: paper-writer
description: "撰写中英文学术论文的技能，支持docx文档导出。支持毕业论文、课程论文、开题报告、文献综述、文献精读、选题报告、thesis、journal article、conference paper、research proposal 等学术文体。覆盖完整流程：学术文献检索 → 分章节写作 → 科研图表 → DOCX 排版与导出。"
---

# 学术论文写作

端到端论文写作流程。支持中文学术论文（GB/T 7714 引用）和英文学术论文（APA/IEEE/Chicago 等引用）。使用本技能提供的参考 API 即可完成论文写作，无需参考其它 skill。

## 重要规则
1. 禁止在写js的时候输出unicode
2. 禁止用 Python 代码拼接生成 JS 文件内容
3. 写入方式：调用 `write_file(path, content, mode="write")`，长篇分章追加用 `mode="append"`（append 是往同一个 JS 文件追加，`h`/`refs` 在骨架中定义一次即可，禁止重复 require）
4. **读取参考文件时完整读取，不要截断**
5. 执行 JS 必须通过 `run_node_docx`
6. 保留最后的 JS 文件
7. **真实性第一**：严禁手写参考文献、严禁改写/补写 `references.json`；正文只允许使用 `[@key]` 引用，缺失引用宁可忽略也不编造

---

## 执行流程

按顺序执行，每步完成后再进入下一步。

开始前一次性读取对应语言的参考文档和 DOCX API 参考：

- **[中文]** [chinese-paper-reference.md](references/chinese-paper-reference.md) + [docx-api.md](references/docx-api.md)
- **[EN]** [international-paper-reference.md](references/international-paper-reference.md) + [docx-api.md](references/docx-api.md)

### 步骤 1：文献检索

用 `multi_round_search` 一次调用完成全部检索，**必须传 `refs_json` 参数落盘**。中文论文**必须传 `zh_ratio`**（从参考文档字数表查值），不足时自动追加中文检索。

检索预算、代码模板、数据源选择见参考文档"文献检索"章节。

写作中引用不足时，用 `search_and_save` 补检索（传相同 `refs_json` 追加）。只引用学术来源，禁止 CSDN/知乎/百度百科等非学术网页。

**此步骤不可跳过**。`refs_json` 文件是后续生成参考文献的唯一数据来源。

### 步骤 2：写作规划

1. **确定文体**：根据用户描述匹配（提到"毕业"→学位论文，"课程/作业"→课程论文，"开题"→开题报告……），无法判断时询问用户
2. **章节结构以参考文档为准**：从参考文档查该文体的章节模板和各章字数分配，严格按此结构写作

### 步骤 3：分章节写作与 DOCX 排版

按 [docx-api.md](references/docx-api.md) 的分批规则和排版要求逐章写入。写作规范和文风要求见参考文档。

关键规则：
- **按章节分批写入**，每个一级章节至少单独一批
- **段落 ≥ 250 字**（英文 ≥ 180 words），禁止压缩式写作
- **写后自检**：每章写完统计字数，低于目标 80% 则追加补写同一章节
- **引用约束**：每章的"必引"文献必须全部出现 `[@key]`，综述章每个主题段同时引用 ≥ 3 篇
- **参考文献**：正文用 `[@key]`，文末用 `refs.autoBibliography()` 自动生成，禁止手写条目
- **图表**：用 `scientific_visualization` 生成 300dpi PNG，API 见 docx-api.md 第七节

