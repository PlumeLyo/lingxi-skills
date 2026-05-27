# 设计视觉规范，输出 `<design_spec>`

以"高级视觉传达与品牌叙事专家"身份，基于网格系统（Grid System）和负空间艺术，生成具有行业深度和独特质感的全局视觉规范。

描述定量关系时，使用 ppt 系统常用的单位，如字号用 pt，尺寸用 inch。

---

## 配色原则

- **严禁使用 Office 默认配色**或饱和度过高的"PPT蓝"。
- **6:3:1 法则**：空间底色 (60%)、品牌主色 (30%)、功能性强调色 (10%)。
- **光影深邃感**：采用深色模式（Dark Mode）作为基调，利用微渐变（Subtle Gradients）和磨砂玻璃（Frosted Glass）质感增加层级。
- **高对比无障碍**：严格遵循 WCAG 2.1 AA 级标准，文字与背景对比度不低于 4.5:1。
- **明度差强制**：文字颜色与背景色(背景图片)的明度（Brightness）差异必须大于 70%。
  - 色值互斥律：若背景色 $Hex < \#666666$（深色），文字必须为 $\#FFFFFF$ 或明度高于 90% 的浅色；若背景色 $Hex > \#999999$（浅色），文字必须为 $\#000000$ 或明度低于 10% 的深色。
  - 严禁灰度粘连：严禁出现"深灰底+中灰字"或"白底+浅灰字"的搭配，必须有极强的明暗跳跃。

**配色速查表：**

| 风格分类   | 视觉感受           | 背景色           | 主色             | 强调/点缀色        | 推荐使用场景                   |
| ---------- | ------------------ | ---------------- | ---------------- | ------------------ | ------------------------------ |
| 经典商务   | 沉稳、专业、可信   | #FFFFFF (纯白)   | #1B263B (深海蓝) | #F28C28 (爱马仕橙) | 季度汇报、金融分析、项目投标   |
| 硬核科技   | 未来感、高冷、精致 | #121212 (石墨黑) | #2D2D2D (深灰)   | #00FFC8 (极光青)   | AI产品发布、数字化转型、大数据 |
| 莫兰迪人文 | 儒雅、舒适、高级灰 | #F5F5DC (燕麦色) | #967E76 (灰褐色) | #A45C40 (砖红色)   | 教育培训、生活方式、年度总结   |
| 极简主义   | 干净、通透、现代   | #F8F9FA (极浅灰) | #343A40 (炭灰)   | #002FA7 (克莱因蓝) | 创意策划、建筑设计、个人简历   |
| 新锐国风   | 韵味、优雅、大气   | #FCFAF2 (象牙白) | #5D655F (石板青) | #BD3124 (故宫红)   | 文化推广、中式品牌、政务宣讲   |
| 清冷职场   | 干练、冷静、理性   | #E9ECEF (冷灰)   | #495057 (铁灰)   | #748CAB (雾霾蓝)   | 咨询报告、医疗科研、法律事务   |

---

## 背景图规划原则

- **叙事化视觉**：封面图必须是具备"隐喻感"的高质量摄影或抽象渲染图，而非简单的素材堆砌。
- **沉浸式延展**：图片需具备大面积留白（Negative Space），以便文字布局，避免干扰阅读。
- **一致性滤镜**：描述中必须包含特定的灯光和色温要求，确保所有生成的图片像出自同一组商业摄影。
- **在 `<background_images>` 中为每种需要背景图的页面类型规划图片描述，第 3 步将据此生成**

---

## 安全区域机制（核心）

为避免背景图中的装饰元素与 PPT 内容重叠，**必须在图片描述中明确界定安全区域**。

**安全区域配置表：**

| 页面类型 | 安全区域位置 | 安全区域占比      | 装饰元素允许区域       | 内容布局约束                         |
| -------- | ------------ | ----------------- | ---------------------- | ------------------------------------ |
| 封面页   | 左侧或中央   | 宽 50-60%，高 70% | 右侧/底部边缘 30% 以内 | 标题、副标题放于安全区域内           |
| 目录页   | 中央         | 宽 70%，高 80%    | 四周边缘 15% 以内      | 目录列表放于中央安全区               |
| 章节页   | 中央         | 宽 60%，高 50%    | 四周边缘或对角         | 章节标题居中，避让装饰区             |
| 内容页   | 左侧+上方    | 宽 60%，高 70%    | 右下角 30% 以内        | 标题靠上、正文靠左，右下可留白或装饰 |
| 结尾页   | 中央         | 宽 50%，高 40%    | 四周边缘 25% 以内      | 结束语居中，四周可装饰               |

**安全区域描述语法（必须遵守）：**

在 `<bg_image>` 中必须使用以下格式描述安全区域：

- `safe zone: [position], [percentage] of frame clear for text overlay`
- `decorative elements confined to [allowed area]`
- `absolutely no text, no lettering, no numbers in the generated image`

**示例：**

```
safe zone: left 60% and top 70% of frame clear for content overlay,
decorative elements confined to bottom-right corner only,
absolutely no text in the image
```

---

## 排版与字体进化

| 视觉风格方向 | 建议标题字体                    | 建议正文字体               | 适用场景         |
| ------------ | ------------------------------- | -------------------------- | ---------------- |
| 科技/未来    | Orbitron / 阿里巴巴普惠体 Heavy | Inter / 思源黑体           | 方案、产品发布   |
| 专业/权威    | Playfair Display / 华文细黑     | Source Sans Pro / 微软雅黑 | 报告、金融、咨询 |
| 工业/极简    | Roboto Condensed / 仓耳今楷     | Helvetica / 细体黑体       | 艺术、建筑、制造 |

---

## 设计禁忌

- **绝不使用边框/轮廓线**：现代设计靠色块投影和留白区分层级。
- **拒绝图标异样化**：所有图标必须统一线宽或填充风格，严禁混搭。
- **严禁居中主义**：除非是封面，否则正文内容应严格遵循非对称平衡。

---

## 输出模板

调用 `start_write_file(path="{pptdir}/design.xml")` 开启写作模式，直接输出以下 XML 内容，输出完毕后调用 `end_write_file()` 保存：

```xml
<design_spec>
<design_style>
[风格名：例如"赛博朋克深邃主义"或"北欧极简工业风"]。
核心逻辑：利用[大字重标题]建立视觉锚点，通过[非对称式网格]布局，结合[毛玻璃质感容器]承载核心数据，营造具有电影感的商务氛围。
</design_style>

<color_system>
主色：#XXXXXX      /* 提取自行业特性的高识别色（如钛金灰或极光绿） */
辅助色：#XXXXXX    /* 用于次级装饰，降低明度 */
强调色：#FF3B30    /* 仅用于重点数字、警示或CTA按钮 */
</color_system>

<typography>
封面页：
• 标题：[字体名], 54 pt, Bold, 白色
• 副标题：[字体名], 18 pt, 强调色

目录页：
• 标题：[字体名], 36 pt, 底部装饰色块(不使用线)
• 章节索引：[字体名], 24 pt, 灰度处理, 配合数字编号

内容页：
• 幻灯片标题：[字体名], 27 pt, 靠左上对齐, 主色
• 正文/列表：[字体名], 13.5 pt, 白色

结束页：
• 核心标语：[字体名], 42 pt, 居中对齐, 强调色
</typography>

<background_images>
<!--背景图设计：仅用于提供干净背景与基础对比度，不承担视觉主体。必须极简。-->
<bg_image type="封面页">
Minimal background, single focal subject related to [具体主题描述], large empty space.
Composition must be extremely clean with very few elements (max 1–2).
Safe zone: left 60% and center must remain empty.
Decorative elements allowed only on right edge or bottom corner, very subtle.
No text, no symbols, no complex patterns.
Soft lighting, low contrast, no vivid or rich colors.
</bg_image>
<bg_image type="目录页">
Minimal abstract background, very light geometric or texture hint only.
Composition must be simple and uniform, no strong shapes.
Safe zone: central 70% must remain completely clean.
Decorative elements limited to edges, extremely subtle (almost unnoticeable).
No text, no symbols.
Flat lighting, low contrast, avoid visual noise.
</bg_image>
<bg_image type="章节页">
Minimal scene related to [主题相关描述], simplified shapes only.
At most one visual anchor element.
Safe zone: center area must remain clean for title.
Decorative elements only at corners or diagonal edges, very sparse.
No text, no symbols.
Soft lighting, restrained contrast, no complex textures.
</bg_image>
<bg_image type="内容页">
Minimal neutral background with slight texture or single subtle element.
No strong visual center.
Safe zone: left 60% and top 70% must remain empty.
Decorative elements limited to bottom-right corner only, extremely minimal.
No text, no symbols.
Very clean, low contrast, no visual clutter.
</bg_image>
<bg_image type="结尾页">
Minimal background with one subtle symbolic element related to [主题相关描述].
Large empty space in center.
Safe zone: central 50% must remain clean.
Decorative elements only at edges, very light presence.
No text, no symbols.
Soft lighting, calm and simple atmosphere.
</bg_image>
</background_images>

<background_designs>
<!--背景设计，叠加在背景图之上，用于确保文字内容有足够的对比度，清晰可见。 仅允许描述遮罩和纯色填充，不支持渐变背景。	-->
<!-- 遮罩必须简单、可实现，仅用于增强文字对比度 -->
<!-- 仅允许：纯色半透明遮罩 -->
<design type="封面页">
overlay:
纯色半透明遮罩：全幅覆盖一层 60% 黑色透明遮罩，用于压低背景对比度，保证目录文字清晰。
solid_fill:
背景底层填充为纯黑 (#050505)，防止高分辨率图片加载前的视觉闪烁。
</design>
<design type="目录页">
overlay:
全幅半透明遮罩：覆盖一层 70% 不透明度的深色图层，增加高斯模糊效果，使几何背景图案虚化，确保前景目录文字的绝对清晰。
solid_fill:
无，依赖背景图案的低对比度渲染。
</design>
<design type="章节页">
...
</design>
<design type="内容页">
...
</design>
<design type="结尾页">
...
</design>
</background_designs>
</design_spec>
```

---

**本步产出物：** `{pptdir}/design.xml`

**type 说明：** type 用来区分页面类型，目前支持的页面类型仅有 `["封面页", "目录页", "章节页", "内容页", "结尾页"]`
