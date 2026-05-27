# 调用工具生成 PPT

使用 `init_slides` 工具，将 {pptdir} 路径作为参数传入：

工具会解析 XML，通过两阶段 LLM 调用生成 python-pptx 代码，最终在输出目录中产出一个可直接运行的 `build_pptx.py` 脚本。

**工具内部流程：**

1. **并发生成**：背景生成（`set_background`）和各页内容生成（`build_slide_XX`）在同一个并发队列中同时执行，互不依赖。背景任务通览整体大纲和设计规范，生成统一的 `set_background(slide, page_type)` 函数；各页任务仅接收页面信息和设计规范，生成对应的 `build_slide_XX(slide)` 函数，页面内容直接硬编码在函数体内
2. **组装**：将 `set_background`、所有 `build_slide_XX` 和 `build_presentation()` 主函数组装为完整的 `build_pptx.py` 脚本

**输出物：** `{pptdir}/` 目录下的多文件 Python 项目：

```
{pptdir}/
  build_pptx.py          -- 主脚本（导入子模块并组装演示文稿）
  gen_script.py          -- 通用工具函数库（自动复制，供各页 import）
  _background.py         -- set_background 背景设置函数
  _slide_01.py           -- 第 1 页 build_slide_01 函数
  _slide_02.py           -- 第 2 页 build_slide_02 函数
  ...
```

`gen_script.py` 提供了 `add_textbox`、`add_paragraph`、`add_rect`、`add_rounded_rect`、`add_picture` 等封装函数，各页代码通过 `from gen_script import ...` 引用，大幅减少重复代码。

每个子模块在写入前会自动进行引号修复（AST 校验 + 嵌套引号替换为中文直角引号），确保代码可直接运行。
