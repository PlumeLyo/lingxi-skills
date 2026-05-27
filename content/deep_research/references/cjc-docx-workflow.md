# CJC 适配器补充说明

本文件只补充 `cjc` 适配器的私有信息。通用执行顺序统一遵循 `references/docx-template-workflow.md`，不要再把本文件当成模板通用流程。

## 一、何时优先使用

以下场景可优先选择 `cjc` 适配器：

- 目标是中文期刊、中文论文、中文综述或规范排版稿
- 用户明确要求正式学术 Word 稿
- 用户没有指定其他模板实现，且当前默认服务模板可满足要求

当前默认模板：

- `skills/deep_research/assets/CJC-Templet_Word2003.docx`
- `skills/deep_research/references/cjc-template-profile.json`：已解析好的模板画像，默认先读它

共享脚本：

- `skills/deep_research/scripts/cjc_docx_writer.py`
- `skills/deep_research/scripts/docx_template_runner.py`：统一适配器入口，当前通过 `--adapter cjc` 调用本实现

## 二、命令示例

检查模板：

```bash
python skills/deep_research/scripts/docx_template_runner.py inspect \
  --adapter cjc \
  --template skills/deep_research/assets/CJC-Templet_Word2003.docx
```

生成文稿：

```bash
python skills/deep_research/scripts/docx_template_runner.py generate \
  --adapter cjc \
  --template skills/deep_research/assets/CJC-Templet_Word2003.docx \
  --spec /tmp/sandbox/report-spec.json \
  --output /tmp/sandbox/多智能体协作综述.docx
```

在当前运行环境中，如果只能通过 `python_cell_exec`工具 调用 Python，优先直接复用共享写入器，不要手写新的 `python-docx` 逻辑：

```python
import json
import sys, os

sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'deep_research', 'scripts'))
from cjc_docx_writer import generate_document

with open("/tmp/sandbox/report-spec.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

generate_document(
    template_path="skills/deep_research/assets/CJC-Templet_Word2003.docx",
    spec=spec,
    output_path="/tmp/sandbox/多智能体协作综述.docx",
)
```

如果当前工作目录不是应用根目录，就把上面的相对路径替换成对应的绝对路径。

## 三、当前模板中的关键样式

脚本会优先使用以下样式：

- 中文标题：`Subtitle`
- 中文作者：`作者`
- 中文单位：`单位`
- 中文摘要：`摘要`
- 中文关键词：`关键词`
- 英文标题：`Title1`
- 英文作者：`Name`
- 英文单位：`Depart.Correspond`
- 英文摘要：`Abstract`
- 英文关键词：`Key words`
- 正文：`Body Text`
- 标题：`Heading 1` / `Heading 2` / `Heading 3`
- 英文参考文献：`Text of Reference`
- 中文参考文献：`Text of 中文参考文献`

## 四、私有注意事项

- 模板必须是 `.docx`，不是 `.doc`
- 默认先复用已解析好的 `cjc-template-profile.json`
- 只有模板变更或 profile 失效时，才重新 inspect
- spec 里没有的数据不要编造；`report-spec.json` 仍应保持通用 JSON 结构，不要把样式名写进 spec
- 最终 `.docx` 文件名按任务主题与交付类型语义命名
- 如果只是生成 section 草稿，不必强行生成正式 `.docx`
- `report-spec.json` 优先使用 `sections[].level/title/paragraphs` 和 `subsections[]`；参考文献优先写成字符串数组
- 不要自己从 `Document()` 开始拼段落、分页、样式；这类逻辑统一交给 `cjc_docx_writer.py`
