## HTML 技术规范

所有 HTML 生成均须遵守本章全部规则。

### 版面契约（防跑版：固定画布 / 无叠字 / 无滚动）

以下三条与「美观」并列，**违反任一条即视为跑版**，必须在交付前消除。

1. **固定画布 1280×720px（16:9）**
  - `html`、`body`、`.slide-container` 在 CSS 中写死为 `width:1280px; height:720px;`（可用 `max-width`/`max-height` 同值兜底）。
  - 整页视觉内容只存在于这一矩形内，**不得**依赖浏览器窗口缩放或大于画布的隐式尺寸撑开页面。

2. **禁止滚动与「滑动查看」**
  - `html, body { overflow: hidden; }`，`.slide-container { overflow: hidden; }`。
  - 不得出现纵向/横向滚动条，不得用 `overflow: auto|scroll` 在页内藏第二屏内容。内容过多时**拆页或减字**，绝不靠滚动解决。

3. **禁止可感知的文字/正文块互相遮挡**
  - 主排版**必须**使用 **CSS Grid**（详见下文「布局」与「Grid 使用规范」），保证块与块之间留白可预期。
  - **禁止**为「塞下更多字」把多块文字压到同一视觉区域。

### HTML 结构与命名约定

- 每页幻灯片生成一个**完整独立的 HTML 文件**，CSS/JS 全部内联，不依赖外部文件（CDN 资源除外）
- HTML 文件命名范式：`slide_xxx.html`，**必须以 `slide_` 开头**，且正文页用序号表明，例如：`slide_02.html`
- class 命名使用 `slide-` 前缀（如 `slide-title`、`slide-card`），避免与 Tailwind 冲突

### 资源规范

**仅允许**使用以下三个 CDN，**禁止引用其他任何 JS 库或 CDN**：

```
Tailwind CSS：
<script src="https://qn.cache.wpscdn.cn/copilot-test/copilot-cdn/js/tailwindcss@3.4.17.js"></script>

FontAwesome（图标与文本一一对应，禁止孤立/装饰性图标）：
<link href="https://qn.cache.wpscdn.cn/copilot-test/copilot-cdn/css/fontawesome-free@6.4.0.css" rel="stylesheet" />

ECharts（数据可视化）：
<script src="https://qn.cache.wpscdn.cn/copilot-test/copilot-cdn/js/echarts@5.4.3.min.js"></script>
```

- **FontAwesome 与样式表成对**：凡在 `body` 内使用 FontAwesome（如 class 含 `fa-`、`fas`/`far`/`fab`/`fa-solid` 等前缀，或 `<i>`/`<span>` 仅作图标占位），必须在 `<head>` 中按上文 URL 引入 FontAwesome

**禁止**引用 Google Fonts（`fonts.googleapis.com`）、jQuery、Bootstrap 等。

### Tailwind CSS 使用限制

- **`class` 与 utility 防撞**：自定义语义类仅限 **`slide-*`**；若在 HTML 中写与 Tailwind 同名的字符串（如 **`table-row`**，浏览器会载入 `display:table-row` 型 utility **压过**手写 `.table-row{ display:grid }`，表格/网格会整块塌成竖条）。**好处**：布局由你定义的 CSS 做主。
- 仅使用 Tailwind 内置 utility class，**禁止**运行时能力：`tailwind.config` 注入、`text/tailwindcss` 样式块、`@layer` / `@apply` 指令、非官方默认 class
- Tailwind Preflight 会重置标题标签样式，必须用高权重选择器或 `!important` 覆盖关键字号：
  - 用 `.slide-container h1 { font-size: 64px !important; }` 而非 `h1 { font-size: 64px; }`
  - 涉及 `font-size`、`font-weight`、`line-height` 时，必要时加 `!important`
- **禁止**使用圆角卡片、左/右边框强调卡片、阴影框等网页 UI 样式
- **禁止**使用 CSS 动画、`@keyframes`、`transition`、`hover` 效果（静态幻灯片，不是交互网站）

### ECharts 使用规范

- 图表容器必须用具有明确像素宽高的父 `div` 包裹（如 `style="width: 600px; height: 360px;"`）
- 每列最多一个图表
- 图表颜色从调色板派生，去除不必要的网格线和背景，保持极简风格
- 标签字号必须足够大（>= 18px），确保投影清晰
- **图例防跑版铁律**：必须显式指定 `legend` 的位置和间距（如 `left: 'center', itemGap: 20`），并确保图表容器宽度足够，防止图例文字因拥挤而换行错位。
- **禁止**生成虚构数据；所有数字必须来自可验证来源，并标注数据源

---

## 设计指导

### 设计原则

**在实现每个页面前，先思考：**

- **目的**：这页要传达什么核心信息？受众在这页停留的焦点是什么？
- **基调**：这页如何延续已选主题的配色关系、字体气质，并服务当前内容目标？
- **差异化**：这页的视觉重心是什么？用户会记住的一件事是什么？

关键在于**意图性和整体一致性**，而非盲目追求复杂或简约。

### 布局

- 页面固定尺寸 **1280×720px**（16:9），所有元素必须在此范围内，不得溢出
- 在所有 CSS 之前重置默认样式（`margin: 0; padding: 0; list-style: none; text-decoration: none; box-sizing: border-box;`）
- **Grid 定骨架，Flex 分比例**：Grid 将页面切成职责明确的带，边界预先锁死，不受内容影响；Flex 在已有确定高度的 Grid 子区内按比例分配空间。二者缺一不可——没有 Grid 给出容器高度，Flex 的 `flex: 1` 无处伸展，内容只会堆在顶部。
- 使用 `slide-container` 作为最外层容器；**`.slide-container` 自身**不要用 `padding`（避免与固定 1280×720 叠加算错尺寸）；
- 采用**水平布局**，始终限制每个元素的高度，禁止垂直堆叠多个图表
- 图表元素必须指定**固定像素**的宽高，禁止使用百分比或 flex 弹性尺寸
- **单行文本（标题、标签、署名等）必须加 `white-space: nowrap`**，防止因容器宽度不足意外换行
- 用 `::before/::after` 画装饰线条时，承载容器必须在线条一侧留出 `padding`（≥16px），防止伪元素线条与文字在像素级重叠
- **章节页主体上下居中**：章节过渡页中，承载章节标题与主体文案的区域须在 **1280×720 可视区内纵向居中**，排除页眉页脚等固定边带后勿再将整块主体贴顶。**好处**：上下留白对称，过渡页一眼成章，避免大半空白挤在下半屏像版心没落稳。

#### 版面饱满度

- **硬性目标**：每张 1280×720 页须 **观感充实、层次分明**，避免出现「大块未设计的纯色 + 几段孤零零正文」的空泛稿；留白应是 **刻意分区与呼吸带**，而非无话可说的空洞。
- **实现路径：在无编造前提下丰富版面**：至少覆盖下列中的多项——**① 背景层**：微渐变、低对比网格/斜纹、角部色带或大号淡色水印编号（须满足对比度章节）；**② 结构带**：明确页眉/标题区、主内容栅格与底栏/页码带，各分区禁止重合，用 `gap`、细线或半透明分区底形成层次；**③ 字阶与数据呈现**：标题/副标/正文至少两级跳变，已有数字用标签、色条、进度条等用纯 CSS 强化；要点配与句意对应的 FontAwesome；**④ 少字页加码**：正文偏少时更不能交白卷，须用 ①②③ 把 **1280×720 画幅用起来**，但禁止捏造事实与注水套话。
- **多列网格保底**：对称多列若每格字数仍少，优先 **减列、合并格子或增大字号/层级、抬升字阶/数据条** 占满栅格意图，避免多条「高竖条空心卡」。**好处**：格间留白像设计过的分栏，而非随机条缝。
- 合理设置正文区域内容：去除固定页面元素（标题、脚注等）后，正文内容区的布局也应均匀合理分布：
  * **避免内容过度集中**：避免内容高度远小于页面正文区高度（如正文区高度 500px，内容仅 200px）。优先通过「字号自适应规则」调大字号和间距来填充空间；其次通过增加装饰元素；最后才考虑让内容居中（居中只解决视觉偏移，不解决空洞感）
  * **避免头重脚轻**：内容集中在顶部的根本原因是主内容容器缺少 `justify-content: center`（详见「防内容贴顶铁律」）。在排查内容偏上问题时，**首先检查 CSS 而非调整内容位置**。
  * **视觉重心检验**：在脑中将页面三等分（上 1/3 / 中 1/3 / 下 1/3），内容视觉重心应落在中间 1/3 区域内。若视觉重心明显偏离（如集中在上 1/3），则须回头检查容器 flex 设置和字号是否符合自适应规则

#### 内容密度铁律

- 每页最多 5 个要点（多了拆页，绝不硬塞）
- 单张幻灯片只传达一个核心信息，有且仅有一个视觉重心
- 正文行长不超过页面宽度的 65%

#### Grid 布局原则
**目标**：用 Grid 把页面切成职责清晰的带，让每个分区获得正确的空间比例；再在各分区内用 Flex 完成内容的比例分配与对齐。最终实现主内容饱满、页眉/页脚紧凑、所有内容在 1280×720 内完整呈现，无溢出、无塌缩。
- **轨道数与子项数一一对应**：写 `grid-template-rows/columns` 前，先数清直接子元素的个数（装饰条、分隔线也算）。轨道数不足时，多余子项落入隐式 `auto` 轨道，预留的主内容区会被前面的元素提前瓜分，塌缩到底部。
- **按职责分配轨道**：高度固定的元素（页眉、页脚、装饰线）用 `auto` 或像素值；承载主内容的区域用 `1fr` 占据剩余空间。
- **两层职责分离**：`.slide-main`（`1fr` 行）自身用 `display: grid; align-content: center` 将所有子块整体垂直居中，子块保持 `auto` 自然高度；每个子内容块（卡片、列表区、图表区）内部用 `display: flex` 编排块内元素。不要在 `.slide-main` 上混用 flex，避免子块被意外拉伸。
- **跨列/跨行元素显式声明**：用 `grid-column: span N` 或 `grid-row` 精确指定，禁止靠自动流式排布猜测落点。

#### 防内容贴顶铁律（每页必须执行）

**最常见跑版原因**：Grid 给了主内容区正确高度，但区域内部没有居中指令，内容默认贴顶，底部出现大块空白。

**强制规范**：两层职责分离——`.slide-main` 负责将所有子内容块作为整体垂直居中；每个子内容块（卡片、列表区、图表区等）内部用 flex 编排自身内容。

```css
/* ① 主内容区：align-content: center 将子块整体居中，子块保持 auto 自然高度 */
.slide-main {
  display: grid;
  align-content: center;   /* 垂直居中核心：将所有子行作为整体居中 */
  min-height: 0;           /* 防止撑破 grid 行高 */
}

/* ② 子内容块（卡片/列表/图表区）：用 flex 编排块内元素 */
.slide-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
```

> **为什么用 `align-content` 而非 `justify-content`**：`align-content: center` 作用于 grid 容器的行轨道——所有子块保持 `auto` 自然高度，整体作为一组垂直居中，上下留白对称。`justify-content: center` 是 flex 方向上的居中，配合 `flex-direction: column` 也能实现类似效果，但子块若不显式限制高度容易被拉伸。优先用 `align-content` 方案，子块高度更可预期。

**标准三行骨架参考**（页眉 + 主内容 + 页脚，适用于绝大多数内容页）：

```html
<div class="slide-container" style="
  width:1280px; height:720px; overflow:hidden;
  display: grid;
  grid-template-rows: 72px 1fr 48px;   /* 页眉 | 主内容 | 页脚 */
">
  <!-- 页眉区 -->
  <header class="slide-header" style="display:flex; align-items:center; padding:0 56px;">
    <!-- 标题、进度条等 -->
  </header>

  <!-- 主内容区：align-content:center 将子块整体垂直居中 -->
  <main class="slide-main" style="
    display: grid;
    align-content: center;
    gap: 24px;
    padding: 0 56px;
    min-height: 0;
  ">
    <!-- 子内容块：各自用 flex 编排块内元素 -->
    <div class="slide-card" style="display:flex; flex-direction:column; gap:12px;">
      <!-- 卡片内容 -->
    </div>
    <div class="slide-card" style="display:flex; flex-direction:column; gap:12px;">
      <!-- 卡片内容 -->
    </div>
  </main>

  <!-- 页脚区 -->
  <footer class="slide-footer" style="display:flex; align-items:center; padding:0 56px;">
    <!-- 页码、来源注释等 -->
  </footer>
</div>
```

**多栏布局时的居中**：若主内容区是左右分栏（如左图右文），在 `.slide-main` 上改用列轨道，`align-content: center` 仍然负责整体垂直居中；每一栏内部各自用 flex 编排。

```css
/* 左右分栏：主内容区改为两列 grid，align-content 仍负责垂直居中 */
.slide-main {
  display: grid;
  grid-template-columns: 1fr 1fr;   /* 或按比例如 5fr 4fr */
  align-content: center;
  align-items: center;              /* 两栏等高时各自内部也居中 */
  gap: 48px;
  padding: 0 56px;
  min-height: 0;
}
/* 每栏内部用 flex 编排子元素 */
.slide-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
```

### 字体控制
- 使用确定的展示字体 + 正文字体搭配方案，不得引入其他字体
- 字号层级清晰，**font-size**：标题不低于48px，正文不低于22px，辅助文字不低于18px
- 如果用户明确指定了字体要求，严格按照用户的要求执行，可不遵循上述默认要求

#### 内容稀少时的字号自适应规则（防字小页空）
**问题场景**：当一页只有 2–4 个要点/卡片时，若使用最小字号（22px），内容总高度仅占正文区 30%，即使居中也视觉空洞。
**强制规则**：根据页面内容块数量，按下表调整字号与间距，**禁止在内容稀少时使用字号下限值敷衍了事**：

| 内容块数量 | 正文/列表项字号 | 行高 | 项目间 gap | 备注 |
|-----------|---------------|------|-----------|------|
| ≤ 2 个 | ≥ 32px | ≥ 1.7 | ≥ 40px | 字重可加粗（500–600）|
| 3 个 | ≥ 28px | ≥ 1.6 | ≥ 32px | 配合装饰元素填充空间 |
| 4 个 | ≥ 26px | ≥ 1.5 | ≥ 28px | - |
| 5 个以上 | ≥ 22px | ≥ 1.45 | ≥ 20px | 正常密度 |

- **配合装饰元素**：内容块 ≤ 3 个时，除调大字号外，还须至少添加一项视觉补充（背景装饰数字、强调色宽边框、配套 icon、底部装饰线等），确保画幅被充分利用
- **章节过渡页**：通常只有一个章节标题 + 一句副标题，标题字号须 ≥ 60px，副标题 ≥ 28px；两者之间留 `margin-top: 24px`；整块内容在 720px 垂直方向居中

### 美学关注点

#### 色彩与对比度（硬性约束）
- **WCAG 对比度底线**：任何可见的正文、标题、数据，其前景色与背景色的对比度必须 ≥ 4.5:1。
- **深色背景上的辅助文字**：禁止使用暗灰色或深蓝色。在深色背景（如 `#0F1B2D`）上，辅助文字最暗只能用到 `rgba(255,255,255,0.6)` 或浅灰色（如 `#94A3B8`）。
- **装饰性大字（如背景编号"01"）**：
  - 在深色背景上：禁止使用深色（如深蓝、深灰），必须使用**强调色**或**白色低透明度**（如 `rgba(255,255,255,0.15)`）。
  - 在浅色背景上：使用主题色的极浅版本（如 `rgba(59,130,246,0.1)`）或浅灰色。
- 主色调搭配鲜明强调色，优于均匀分布的配色
- 避免陈词滥调的配色（尤其是白底紫色渐变）

#### 背景与细节

- 创造氛围和深度，而非默认纯色背景
- 可用纯 CSS 实现的纹理效果：渐变叠加、重复线条图案、几何背景、分层透明度、戏剧性阴影

### 核心要求

- **每页版面饱满**：落实上文「版面饱满度」，禁止交「整块空底 + 几段正文」的半成品幻灯片。
- **实现复杂度匹配页面目标**：需要冲击力的页面要拉开对比，需要克制表达的页面要精准控制间距和字号
- **每页视觉语言一致**：任意抽出一页，都应能认出它属于这套 PPT