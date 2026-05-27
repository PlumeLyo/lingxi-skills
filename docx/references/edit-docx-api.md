# edit_docx() API 参考

通过 `edit_docx()` 对现有 `.docx` 做文本替换。内部流程：解包 → 合并相邻同样式 run → 文本替换 → 重打包 → 校验。

## 基本用法

通过 **`python_cell_exec` 工具**执行：

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'docx', 'scripts'))
from edit_docx import edit_docx

result = edit_docx(
    input_docx="<OUTPUT_ROOT>/input.docx",
    output_docx="<OUTPUT_ROOT>/xxx.docx",
    replacements=[
        {"from": "旧公司名称", "to": "新公司名称"},
        {"from": "2024年", "to": "2025年"},
    ],
)
print(result)
```

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input_docx` | `str` | — | 输入文件完整路径 |
| `output_docx` | `str` | — | 输出文件完整路径 |
| `replacements` | `list[dict]` | — | 替换规则列表，每项含 `"from"` 和 `"to"` |
| `parts` | `list[str] \| None` | `None` | 要处理的 XML 部件（支持 glob），默认 `document.xml` + `header*.xml` + `footer*.xml` |
| `match_mode` | `str` | `"literal"` | `"literal"` 精确匹配 或 `"regex"` 正则匹配 |
| `ignore_case` | `bool` | `False` | 是否忽略大小写 |

## 返回值

```python
{
    "ok": True,
    "input_path": "...",
    "output_path": "...",
    "match_mode": "literal",
    "ignore_case": False,
    "files_modified": ["word/document.xml"],
    "replacements_applied": [
        {"from": "旧公司名称", "to": "新公司名称", "count": 3},
    ],
    "validation": {"ok": True, "errors": [], "warnings": []},
}
```

## 正则替换示例

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'docx', 'scripts'))
from edit_docx import edit_docx

result = edit_docx(
    input_docx="<OUTPUT_ROOT>/input.docx",
    output_docx="<OUTPUT_ROOT>/xxx.docx",
    replacements=[{"from": r"Q([1-4]) 2024", "to": r"Q\1 2025"}],
    match_mode="regex",
    ignore_case=True,
)
print(result)
```

## 低层 XML 编辑

如果 `edit_docx()` 替换命中数为 0，通常是目标文本被 Word 拆成了多个 XML run。可退回低层工具链手动处理：

```python
import sys, os
from pathlib import Path

sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'docx', 'scripts'))
from office.unpack import unpack_docx
from office.pack import pack_docx

source = Path("<OUTPUT_ROOT>/input.docx")
unpacked = Path("<OUTPUT_ROOT>/input_unpacked")
output = Path("<OUTPUT_ROOT>/xxx.docx")

unpack_docx(source, unpacked)   # 解包并合并相邻同样式 run
# 用 python_cell_exec 工具读取并修改 unpacked/word/*.xml
pack_docx(unpacked, output)     # 重打包（默认含校验，失败会抛 ValueError）
```

重点文件：

- `word/document.xml`：正文
- `word/header*.xml`：页眉
- `word/footer*.xml`：页脚
- `word/styles.xml`：样式

## 规则

- `edit_docx()` 是基础文本替换工具，不负责批注、修订和复杂域代码
- 解包时会合并相邻的同样式 run，提高文本替换命中率
- 对于被 Word 拆成复杂片段的文本，退回 `unpack_docx()` 手动处理
- `pack_docx()` 会自动修复常见的 XML 空白属性和 `durableId` 溢出问题
