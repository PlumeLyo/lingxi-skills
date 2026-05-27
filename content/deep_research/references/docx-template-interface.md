# DOCX 模板适配接口

本文件只定义学术 DOCX 模板能力的通用接口。默认前提是任务已经进入学术文档路径；具体执行顺序见 `references/docx-template-workflow.md`。

## 一、接口约定

每个模板适配器都应通过统一接口暴露以下能力：

- `spec_family`：适配器消费的通用 JSON 协议版本；当前统一使用 `docx-report-spec-v1`
- `adapter_id`：适配器唯一标识，例如 `cjc`
- `description`：适配器用途说明
- `default_template_path`：默认模板路径；可指向服务内置模板
- `default_profile_path`：默认模板画像路径；无则留空
- `inspect_template(template_path, sample_limit=40)`：读取模板结构与样式画像
- `generate_document(template_path, spec, output_path)`：基于 spec 生成正式 `.docx`

当前统一 CLI 入口：

```bash
python cooffice/skills/deep_research/scripts/docx_template_runner.py list
python cooffice/skills/deep_research/scripts/docx_template_runner.py inspect --adapter cjc
python cooffice/skills/deep_research/scripts/docx_template_runner.py generate --adapter cjc --spec /tmp/report-spec.json --output /tmp/多智能体协作综述.docx
```

## 二、当前实现

当前已接入的适配器：

- `cjc`：基于 `scripts/cjc_docx_writer.py` 的 CJC 学术模板实现
- `jos`：基于 `scripts/jos_docx_writer.py` 的《软件学报》中文单栏模板实现
- `generic`：基于 `scripts/generic_docx_writer.py` 的 best-effort 通用模板实现，适合用户上传自定义 `.docx` 模板时先做 inspect 和试生成

`cjc` 只是当前默认实现，不是唯一实现。以后新增模板时，优先新增一个适配器实现并接入统一接口，而不是继续把新模板逻辑硬编码进 skill 主流程。

## 三、扩展约束

- 新增模板时，尽量复用统一 runner 和注册表
- 不要把模板路径、期刊名或画像文件名绑定成主流程里的特殊分支
- 不要绕开适配器直接在主流程里手写整套 `python-docx` 排版逻辑
- 模板私有固定块优先收敛在适配器私有 hook 中处理；静态块复制优先复用共享工具 `scripts/docx_writer_template_hooks.py`，动态块再保留在适配器私有函数中。只有多个模板都需要的能力才考虑上提到 core
