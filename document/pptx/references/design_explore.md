# PPT 风格探索指南

工作流：**调用封面配色函数 → 生成设计md → （可选）网页品牌提取 → 生成封面 HTML → 截图展示 → 用户选择 → 进入生成阶段**。

### 规范与美学
**开始前必读**：
- 阅读 [html_slide_technical_design.md](html_slide_technical_design.md) 了解HTML 技术规范 + 设计美学

---

## 1. 挑选贴合用户诉求的 3 套主题

调用 `list_cover_theme_candidates` 列出指定 scene 下全部候选主题（含 theme_id、palette、typography），从中挑选最贴合用户诉求的 3 套。

```python
import json
import os, sys
sys.path.insert(0, os.path.join(os.environ["SKILL_PATH"], "pptx", "scripts"))
from theme_api_client import list_cover_theme_candidates

candidates = list_cover_theme_candidates(scene="Business_Corporate")
print(json.dumps(candidates, ensure_ascii=False, indent=2))
```

scene 枚举值：`Business_Corporate` | `Technology_Innovation` | `Health_BioTech` | `Public_Government` | `Industry_Engineering` | `Empathy_NonProfit` | `Culture_History` | `Education_Academia` | `Fashion_Lifestyle` | `Nature_Sustainability`

根据返回的 palette 与 typography 信息，结合用户主题，从候选中选出 3 套最合适的主题。

---

## 2. 生成风格设计文档

基于上一步获取的 3 套主题数据，使用工具 `write_file`，在工作目录下创建 `style_design.md`，为每套主题编写一个设计方案。**禁止使用 Python 脚本写入文件。**

### 差异化约束

三个方案是「同一主题下的不同视觉表达」，必须在以下维度上呈现可识别的差异，禁止仅用同一套版式在三个主题色上反复套用。

1. **质感轴**：为每个方案指定截然不同的画面质感与视觉特效，三套方案内**不得**复用同一种质感或材质表现。
2. **构图与动势**：三个方案的版式动势与空间布局必须明显不同，禁止三套共用同一套骨架。

### 质量要求

- 每个方案的版面必须有一个明确的视觉重心，不允许没有焦点的平淡排布

每个方案仅包含：
- **风格描述**：英文短句（< 20 词）附带括号内中文翻译）；要求描述高度独特、视觉效果惊艳的世界级美学设计风格。它应该捕捉定义特征——布局节奏、纹理或光线提示。禁止所有模糊的形容词，如"干净"、"现代"、"优雅"、"简约"、"柔和"、"精致"。美学必须立即可识别，不可与通用企业或常见设计趋势混淆。
- **调色板**：直接使用对应的`palette`
- **字体方案**：展示字体（大标题用）+ 正文字体（正文用）的搭配方案，并说明与美学风格的关联。仅允许 Web-safe 系统字体栈

---

## 3. （可选）从网页提取设计元素

**触发条件：**用户明确提供了目标品牌/企业/高校/产品的网址或PPT主题涉及特定企业、机构或品牌，且有公开官网可访问

### 3.1 调用提取脚本

使用 `skills/pptx/scripts/web_style_extractor.py` 中的 `extract_web_page_styles` 函数，自动抓取并解析目标网页的 HTML 与 CSS

```python
from web_style_extractor import extract_web_page_styles

result = extract_web_page_styles("https://www.example.com")
print(result)
```

脚本会依次提取：

| 字段 | 类型 | 内容 |
|------|------|------|
| `primary_color` | `string \| null` | 可信度最高的主色（#RRGGBB） |
| `colors` | `string[]` | 主色与辅色列表（已去重、已过滤近白近黑低饱和、按可信度降序） |
| `bg_is_dark` | `bool \| null` | `true` = 页面偏深色背景；`false` = 偏浅色；`null` = 无法判断 |
| `logo_url` | `string \| null` | Logo 完整 URL，未找到为 `null` |
| `heading_font` | `string \| null` | 大标题字体（来自 h1/h2 选择器） |
| `body_font` | `string \| null` | 正文字体（来自 body 选择器） |
| `all_fonts` | `string[]` | 页面声明的全部字体名（含 @font-face），供映射到 Web-safe 字体 |
| `color_vars` | `object` | 颜色相关 CSS 自定义属性（`--varname: #hex`），供参考 |
| `error` | `string \| null` | 非 `null` 表示提取失败，内容为原因 |

### 3.2 补充第 4 套方案

脚本返回后，检查 `error` 字段：
- **`error` 为 `null` 且 `colors` 非空**：合成第四套方案，使用 `start_write_file` → `end_write_file` 追加写入 `style_design.md`。**禁止使用 Python 脚本写入文件。**
- **`error` 非 `null`**：跳过本步骤，仅保留 3 套预设方案

合成内容：
- **风格描述**：以品牌实际视觉语言为基准，用英文短句描述（附中文翻译）；参考 `bg_is_dark` 决定方案整体明暗基调
- **调色板**：以 `primary_color` 为主色核心，从 `colors` 列表中取辅色/强调色，构成完整的 3-5 色调色板
- **字体方案**：优先参考 `all_fonts` 列出的字体名，再看 `heading_font` / `body_font`；若均不在 Web-safe 字体白名单内，映射到气质最接近的许可字体
- **Logo**：若 `logo_url` 非空，记录该 URL，可在封面 HTML 中以 `<img>` 嵌入

---

## 4. 生成设计封面页（HTML）
**目标**：设计具有强烈视觉冲击力和叙事张力的封面页。

**基本原则：**
1. **可读性原则**：对比度充足，文字与关键视觉元素不重叠，标题层级清晰，主标题一眼可读。
2. **纯 HTML/CSS 原则**：封面表现力依赖排版、字体层级、配色与几何/渐变等 CSS 装饰，不依赖外部配图 URL。
3. **视觉冲击原则**：通过大字重对比、留白节奏、色彩张力与装饰几何形成第一眼记忆点。
4. **封面内容铁律**：封面页只能包含：主标题、副标题、演讲者/公司信息、日期。**严禁在封面页放置任何详细数据（如营收、利润、百分比）、图表或长段落文本**。封面是定调的，数据是内容的，绝不能混淆。

- 使用工具 `write_file` 将完整 HTML写入`slide_cover_xxx.html`文件。**禁止使用 Python 脚本写入 HTML 文件**
- 若有品牌方案且存在 `logo_url`，封面 HTML 中可用 `<img>` 嵌入 Logo，须指定固定像素宽高且不得破坏整体构图平衡

---

## 5. 截图展示与总结

所有封面 HTML 全部生成后，调用 `screenshot_slides` 一次性截图：

```python
from generate_pptx import screenshot_slides

print(screenshot_slides([
    # ...各设计封面页 html 文件路径
]))
```

---

## 6. 用户选择 → 进入生成阶段

所有方案全部展示完毕后，询问用户选择方案编号。

用户选定后，**读取同目录下的 `gen_ppt.md`，按其指引继续执行**。