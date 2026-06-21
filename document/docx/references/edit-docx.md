# 编辑 DOCX 文档

> 完整 API（参数、返回值、正则示例、低层 XML 编辑）见 `references/edit-docx-api.md`。

通过 `edit_docx()` 完成文本替换（内部自动：解包 → 合并同样式 run → 替换 → 重打包 → 校验）。通过 **`python_cell_exec` 工具**执行：

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

**替换命中数为 0？** 通常是目标文本被 Word 拆成了多个 XML run，退回低层 `unpack_docx()` / `pack_docx()` 手动处理，详见 `references/edit-docx-api.md` "低层 XML 编辑"章节。

## 编辑规则

- `edit_docx()` 只做文本替换，不负责批注、修订和复杂域代码
- 解包时自动合并相邻同样式 run，提高命中率
- `pack_docx()` 自动修复常见的 XML 空白属性和 `durableId` 溢出问题

---

## Troubleshooting

| 问题 | 处理方式 |
|------|----------|
| `replacements_applied` 中某项 `count` 为 0 | 先 `unpack_docx()` 检查目标文本是否被拆成多个 XML run |
| `DOCX 验证失败` | 检查修改过的 XML 文件是否有语法错误 |
