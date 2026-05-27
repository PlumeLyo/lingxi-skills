# 跑版检测与修复

上一步生成的 PPT 可能存在元素越界、文本溢出、元素重叠等布局问题（跑版）。本步骤使用 `analyze_pptx.py` 中的 `check_layouts()` 进行自动化检测，并根据检测结果修改各页的构建脚本来修复问题。

## 运行跑版检测

使用 `jupyter_cell_exec`工具 执行以下代码，对刚生成的 `.pptx` 文件进行全量布局检测：

```python
import sys, json, os

# 导入布局检测模块
sys.path.insert(0, 'skills/pptx/scripts')
from analyze_pptx import check_layouts,

# 打开刚生成的 pptx 文件
pptx_path = r'<上一步输出的 pptx 文件绝对路径>'
from pptx import Presentation
prs = Presentation(pptx_path)

print(check_layouts(prs, "inch")) # 页面的唯一标识: slide_idx:    当前页码（1-based，可选）
```

对于包含文本的元素， check_layouts 使用文本的实际渲染尺寸进行检测。 当遇到包含文本元素的布局问题时， 需要考虑文本自动换行造成的影响。

对于装饰性元素的 越界问题， 可能是装饰设计需要， 允许忽略。

## 修复构建脚本

**核心思路**：布局问题的根因在 `_slide_XX.py` 构建脚本中的坐标/尺寸参数，因此修复目标是修改脚本源码而非直接操作 pptx 文件。修改后重新执行 `build_pptx.py` 即可生成修复后的 pptx。
