# 准备图片与图标素材，输出 `<image_plan>`

本步处理三类素材：**背景图**、**页面图**、**图标**。

**执行顺序：** 先处理背景图 → 再处理页面图 → 最后处理图标。

---

## a. 生成背景图并转存到本地

遍历 `design.xml` 中 `<background_images>` 下的所有 `<bg_image>`，为每个调用 `generate_image` 工具：

| 参数     | 必填 | 说明（背景图专用）                                     |
| -------- | ---- | ------------------------------------------------------ |
| `prompt` | ✅   | **英文**详细描述背景图内容、色调、氛围。**关键要求：** |

1. **高审美标准**：加入 `high quality, professional, cinematic lighting, minimalist` 等修饰词。

2. **安全区域约束（必须）**：直接使用 `design.xml` 中 `<bg_image>` 的描述，确保安全区域信息完整传递。若需补充，使用以下格式：
   - `safe zone: [position], [percentage] of frame clear for text overlay`
   - `decorative elements confined to [allowed area]`
   - `absolutely no text, no lettering, no numbers in the generated image`

   **安全区域速查表：**
   | 页面类型 | 安全区域 | 装饰元素区域 |
   |---------|---------|------------|
   | 封面页 | 左侧 55%+ 中央 | 右侧 30% + 底部边缘 |
   | 目录页 | 中央 70% | 四周边缘 15% |
   | 章节页 | 中央 60%×50% | 四周边缘或对角 |
   | 内容页 | 左侧 60% + 上方 70% | 右下角 30% |
   | 结尾页 | 中央 50% | 四周边缘 25% |

3. **色调协调**：背景图色调必须与对应页面类型的背景色协调。 |
   | `path` | ✅ | 图片保存目录，填写 `{pptdir}/images/` |
   | `aspect_ratio` | ✅ | 背景图必须使用 `16:9`（铺满整张幻灯片） |
   | `brief` | | 一句话描述，如"为封面页生成深色科技感背景图" |
   | `title` | | 保存的文件名，建议以 `bg_` 前缀命名，如 `bg_cover`、`bg_ending` |
   `generate_image`工具返回图片URL， 通过URL将图片下载到本地进行保存。 后续的图片路径始终使用本地路径.

---

## b. 生成页面图

遍历第 2 步大纲中所有 `<visual_element type="image">`，为每个调用 `generate_image` 工具：
`generate_image`工具返回图片URL， 通过URL将图片下载到本地进行保存。 后续的图片路径始终使用本地路径.

> **页面图比例与排版建议（基于 16:9 PPT 页面）：**
>
> | 页面布局                 | 推荐 `aspect_ratio` | 图片占页面比例      | 适用场景                                 |
> | ------------------------ | ------------------- | ------------------- | ---------------------------------------- |
> | 左右分栏（图文各占一半） | `4:3` 或 `3:4`      | 宽度约占页面 40-50% | 配合大段文字说明，图文并茂，图片占据半屏 |
> | 左右分栏（图片为主）     | `16:9` 或 `3:2`     | 宽度约占页面 60-70% | 图片为主要内容，配合少量文字标注         |
> | 上下分栏 / 横幅配图      | `21:9` 或 `32:9`    | 高度约占页面 30-40% | 作为页面上方/下方的视觉横幅或装饰带      |
> | 小型装饰图 / 图标配图    | `1:1`               | 尺寸约占页面 15-25% | 用于要点卡片、步骤说明等局部装饰         |
>
> **尺寸建议：**
>
> - **左右分栏图**：建议使用 `4:3` 比例（如 2048×1536px），既能保证清晰度，又不会在半屏显示时显得过于狭长
> - **横幅配图**：使用 `21:9` 或 `32:9` 比例（如 3584×1536px），与 16:9 页面宽度协调
> - **方形装饰图**：使用 `1:1` 比例（如 2048×2048px），适合卡片式布局
>
> _避坑指南：`generate_image` 工具强制要求生成图片的总像素数（宽×高）≥ 3,686,400。请勿传入过小的尺寸参数，建议直接使用 `aspect_ratio` 让工具自动计算。_

---

## c. 获取图标并转换为 PNG

先读取图标获取指南，了解搜索和下载接口的详细用法：

```
通过 `jupyter_cell_exec`工具 读取 `skills/pptx/get_icons.md`。
```

然后遍历第 2 步大纲中所有 `<visual_element type="icon">`，按以下流程处理每个图标：

### 流程说明

1. **搜索图标**：使用 `jupyter_cell_exec`工具 调用 `search_icons(query, limit=10)` 搜索图标
2. **选择图标**：从搜索结果中选择语义最匹配的图标（查看 `id` 和 `name` 字段）
3. **下载 SVG**：调用 `download_icon(icon_id, save_path, width=512, height=512, color=主色)` 下载为 SVG 文件
4. **转换为 PNG**：使用 Python 将 SVG 转换为 PNG 格式（python-pptx 不支持直接插入 SVG）

### 完整执行代码模板

对每个图标，使用 `jupyter_cell_exec`工具 执行以下代码：

```python
import sys, os
sys.path.insert(0, '/skills/pptx/scripts')
from icon import search_icons, download_icon

# ── 配置（根据当前图标修改）──
keyword = "<第3步大纲中的搜索关键词>"       # 如 "shield", "chart-line", "rocket"
save_dir = r"{pptdir}/images/icons"     # 图标保存目录
icon_color = "<主色十六进制>"              # 从 design_spec 的 color_system 中取主色，如 "#2C5F2D"
output_name = "<图标文件名>"               # 如 "icon_shield"

# ── 1. 搜索图标 ──
results = search_icons(keyword, limit=10)
print(f"搜索 '{keyword}' 返回 {len(results)} 个结果：")
for r in results:
    print(f"  {r['id']} ({r['pack_name']}, {r['license']})")

# ── 2. 选择最合适的图标（根据搜索结果修改 icon_id）──
icon_id = results[0]['id']  # 默认取第一个，可根据语义选择更合适的
print(f"\n选择图标: {icon_id}")

# ── 3. 下载 SVG ──
svg_path = os.path.join(save_dir, f"{output_name}.svg")
abs_svg = download_icon(icon_id, svg_path, width=512, height=512, color=icon_color)
print(f"SVG 已下载: {abs_svg}")

# ── 4. 转换为 PNG ──
import puresvg
from PIL import Image

#将svg转成png
arr = puresvg.render("input.svg", width={width}, height={height})

img = Image.fromarray(arr)
img.save("output.png")
```

> **注意事项：**
>
> - `icon_color` 应从第 1 步 `<design_spec>` 的 `<color_system>` 中取**主色**，确保图标与整体配色一致
> - 如果 cairosvg 未安装，先执行 `!pip install cairosvg` 安装
> - 转换后的 JPEG 图标建议统一尺寸为 512×512 像素
> - 图标保存路径统一放在 `{pptdir}/images/icons/` 目录下

---

## d. 汇总输出 `<image_plan>`

所有素材（背景图、页面图、图标）处理完毕后，调用 `start_write_file(path="{pptdir}/images.xml")` 开启写作模式，直接输出以下 XML 内容，输出完毕后调用 `end_write_file()` 保存：

```xml
<image_plan>
  <!-- 背景图：按页面类型指定，用于铺满整页背景 -->
  <background_image type="封面页">
    <path>/absolute/path/to/bg_cover.jpeg</path>       <!-- 填入 generate_image 返回的 saved_files 绝对路径 -->
    <description>深色科技感背景，中央留有暗区</description>
  </background_image>
  <background_image type="结尾页">
    <path>/absolute/path/to/bg_ending.jpeg</path>
    <description>深蓝渐变背景，底部留有暗区</description>
  </background_image>

  <!-- 页面图(包括图标)：按页码指定，用于页面内内容配图 -->
  <page_image page="3">
    <path>/absolute/path/to/page3_image.jpeg</path>    <!-- 填入 generate_image 返回的 saved_files 绝对路径 -->
    <position>页面右侧，占宽 40%</position>             <!-- 描述该图片在当前 PPT 页面中的排版位置和大小占比 -->
  </page_image>

  <page__image page="3">
    <path>/absolute/path/to/icons/icon_shield.png</path>   <!-- 填入转换后的 JPEG 绝对路径 -->
    <position>第一个卡片的标题旁，48x48像素</position>     <!-- 描述图标在页面中的具体位置和尺寸 -->
  </page__image>
  <page__image page="3">
    <path>/absolute/path/to/icons/icon_chart.png</path>
    <position>第二个卡片的标题旁，48x48像素</position>
  </page__image>

  <!-- 无需配图/图标的页面不出现在此文件中 -->
</image_plan>
```

**本步产出物：** `{pptdir}/images.xml`（无需任何素材时可省略）
