# 论文 DOCX 生成流程图

本文件只解释“学术文档路径”里论文生成 `.docx` 的调用关系，不解释普通报告路径。

## 一、整体流程

```mermaid
flowchart TD
    A[用户任务进入 deep_research<br/>并已分流到学术文档路径]
    B[references/paper-writing.md<br/>学术写作规则]
    C[output/research-plan.md<br/>研究框架与章节计划]
    D[output/evidence-ledger.md<br/>证据台账]
    E[output/report-spec.json<br/>通用内容 spec]
    F[references/docx-template-interface.md<br/>模板接口说明]
    G[选择 adapter<br/>generic / cjc / jos]
    H[用户模板或内置模板 .docx]
    I[可选：template-profile.json<br/>模板画像缓存]
    J[scripts/docx_template_runner.py<br/>统一命令入口]
    K[scripts/docx_template_adapters.py<br/>adapter 注册表]
    L[scripts/generic_docx_writer.py<br/>或 cjc/jos adapter]
    M[scripts/docx_writer_core.py<br/>通用写入核心]
    N[最终 xxx.docx]

    A --> B
    B --> C
    C --> D
    D --> E
    A --> F
    F --> G
    G --> H
    G -.可选先读.-> I
    E --> J
    H --> J
    J --> K
    K --> L
    I -.仅部分 adapter 参考.-> L
    L --> M
    H --> M
    E --> M
    M --> N
```

## 二、调用关系

```mermaid
flowchart LR
    subgraph Inputs
        A1[report-spec.json]
        A2[template.docx]
        A3[template-profile.json<br/>可选]
    end

    subgraph Entry
        B1[docx_template_runner.py]
    end

    subgraph Registry
        C1[docx_template_adapters.py]
    end

    subgraph Adapters
        D1[generic_docx_writer.py]
        D2[cjc_docx_writer.py]
        D3[jos_docx_writer.py]
    end

    subgraph Core
        E1[docx_writer_core.py]
    end

    subgraph Output
        F1[xxx.docx]
    end

    A1 --> B1
    A2 --> B1
    B1 --> C1
    C1 --> D1
    C1 --> D2
    C1 --> D3
    A3 -.可选.-> D1
    A3 -.可选.-> D2
    A3 -.可选.-> D3
    D1 --> E1
    D2 --> E1
    D3 --> E1
    A1 --> E1
    A2 --> E1
    E1 --> F1
```

## 三、每个文件做什么

- `output/research-plan.md`：研究范围、章节计划、执行顺序。
- `output/evidence-ledger.md`：关键判断与来源台账，正文内容应先在这里被证据约束。
- `output/report-spec.json`：通用内容协议，描述标题、作者、摘要、章节、参考文献等“写什么”。
- `references/paper-writing.md`：学术写作规则，决定怎么组织论文内容。
- `references/docx-template-interface.md`：说明有哪些 adapter、统一入口是什么。
- `scripts/docx_template_runner.py`：外部统一调用入口，接收 `inspect` / `generate`。
- `scripts/docx_template_adapters.py`：adapter 注册表，负责把 `generic`、`cjc`、`jos` 挂进统一接口。
- `scripts/generic_docx_writer.py`：通用模板适配器，适合用户上传自定义模板时做 best-effort 适配。
- `scripts/cjc_docx_writer.py`：`cjc` 专用适配器。
- `scripts/jos_docx_writer.py`：`jos` 专用适配器。
- `scripts/docx_writer_core.py`：真正的通用写入核心，负责清空正文、写 front matter、正文、参考文献、附录，并保留模板版式。
- `template.docx`：真实 Word 模板，决定样式、分栏、页眉页脚、版式。
- `template-profile.json`：可选模板画像，帮助 adapter 预先理解模板结构；不是所有 adapter 都必须依赖它。
- `xxx.docx`：最终正式稿，文件名按任务语义命名。

## 四、最短理解

```mermaid
flowchart TD
    A[report-spec.json<br/>写什么]
    B[adapter<br/>怎么映射]
    C[template.docx<br/>长什么样]
    D[docx_writer_core.py<br/>真正写入]
    E[xxx.docx]

    A --> B
    C --> B
    B --> D
    A --> D
    C --> D
    D --> E
```
