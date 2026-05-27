# DOCX 模板通用流程

本文件只在任务已经进入学术文档路径后使用。它描述所有模板适配器共用的执行顺序，不负责再次判断是否进入学术路径。

## 一、目标

通用流程固定为：

1. 选择适配器
2. 读取模板画像
3. 必要时运行 `inspect`
4. 按通用协议整理 `report-spec.json`
5. 调用统一入口生成最终 `.docx`
6. 若需修订，优先修改 spec 后重生成

新增模板时，默认复用这套流程；不要为每个模板再复制一份 workflow 文档。只有存在明显私有差异时，才额外补一份适配器说明。

## 二、执行顺序

### 1. 选择适配器

- 先阅读 `references/docx-template-interface.md`
- 根据用户指定的模板、期刊或版式要求选择适配器
- 若用户上传了自定义模板，且当前没有对应专用适配器，优先使用 `generic`
- 若用户没有指定模板，可使用默认适配器

### 2. 优先读取模板画像

- 若该适配器存在默认模板画像，优先读取它
- 模板画像只用于理解模板结构、样式槽位和版式特征
- 模板画像不是生成时的唯一输入；正式生成仍以真实模板 `.docx` 与 `report-spec.json` 为准

### 3. 只有必要时才 `inspect`

以下情况才运行模板 inspect：

- 模板文件被替换
- 样式名或版式疑似失配
- 已有模板画像明显过期
- 当前适配器还没有模板画像可用

### 4. 整理通用 spec

- 按 `references/docx-report-spec.md` 编写 `report-spec.json`
- 优先复用 `assets/docx-report-spec-template.json`
- `report-spec.json` 只描述文档内容，不写模板私有样式名

### 5. 生成最终 `.docx`

- 优先使用统一入口 `scripts/docx_template_runner.py`
- 输出文件名按任务主题与交付类型语义命名，不要固定写成 `report.docx`

命令骨架：

```bash
python cooffice/skills/deep_research/scripts/docx_template_runner.py generate \
  --adapter <adapter_id> \
  --spec /tmp/report-spec.json \
  --output /tmp/<final-docx-name>.docx
```

如需显式指定模板：

```bash
python cooffice/skills/deep_research/scripts/docx_template_runner.py generate \
  --adapter <adapter_id> \
  --template /abs/path/to/template.docx \
  --spec /tmp/report-spec.json \
  --output /tmp/<final-docx-name>.docx
```

### 6. 修订策略

- 小改动优先修改 `report-spec.json` 后重生成
- 不要反复手工破坏模板正文结构
- 若同一模板连续生成结果异常，再回头检查 profile 或重新 inspect

## 三、扩展约束

- 新增模板时，优先新增 adapter 实现并注册到统一入口
- 默认不需要新增 workflow 文档；只有模板存在明显私有固定块、特殊前后置 hook 或独有字段时，才补充 adapter-specific notes
- 通用能力优先沉到 `docx_writer_core.py` 或共享 hooks，不要在 skill 主流程里分叉硬编码
