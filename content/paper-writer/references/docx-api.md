# 论文 DOCX API

> 论文写作专用的 docx-helper API 子集。只含论文场景需要的接口，排版参数已按学术规范预设。

---

## 一、初始化配置

### 中文单栏（学位论文 / 课程论文 / 开题报告 / 综述）— 完整示例

```javascript
const path = require('path');
const h = require(path.join(process.env.SKILL_PATH, 'docx', 'scripts', 'docx-helper'))({
  fonts: { heading: '黑体', body: '宋体', english: 'Times New Roman' },
  sizes: { h1: 44, h2: 32, h3: 30, h4: 28, body: 24, small: 21, caption: 18, ref: 21, pageNum: 21 },
  colors: { primary: '000000', text: '000000', border: '000000', light: 'FFFFFF', white: 'FFFFFF' },
  spacing: { heading: { before: 156, after: 156 }, body: { after: 0, line: 360, lineRule: 'auto' } },
  page: { width: 11906, height: 16838, margins: { top: 1701, bottom: 1418, left: 1701, right: 1418 } },
  indent: 480,
});
```

- 字号半磅：24=小四12pt / 32=三号16pt / 44=二号22pt
- A4，页边距上 3cm 下 2.5cm 左 3cm 右 2.5cm，1.5 倍行距（line 360），首行缩进 2 字符（480 DXA）
- 学术论文全部纯黑（000000），禁止彩色
- **section 结构**（每个 section 自动另起一页）：
  - **单栏论文**：封面、目录、每个一级章节（h.h1）各占一个 section。同一章内的 h.h2/h.h3 连续排列，禁止为二三级标题单独建 section
  - **双栏论文**：题目+摘要为一个单栏 section，正文全部放一个双栏 section 连续排列，**一级标题之间不分 section 不分页**

### 其他配置 — 只列差异，其余字段同上（colors 全黑不变）

| 配置 | 适用场景 | fonts | sizes (h1/h2/h3/body) | spacing.body.line | page | indent | 额外 |
|------|---------|-------|----------------------|-------------------|------|--------|------|
| 中文双栏 | 会议论文/期刊短文 | 黑体/宋体/TNR | 30/24/22/20 | 260 | A4, margins 1418/1418/1134/1134 | 400 | `columns: { count: 2, space: 468 }` |
| 英文单栏 | Thesis/Journal Article | TNR/TNR | 32/28/24/24 | 480 | US Letter 12240x15840, margins all 1440 | — | — |
| 英文双栏 | Conference Paper/IEEE | TNR/TNR | 28/22/20/20 | 240 | US Letter, margins 1440/1440/1268/1268 | — | `columns: { count: 2, space: 468 }` |

中文双栏无封面，题目+作者+摘要为单栏全宽，正文起双栏。heading spacing 改为 `before: 156, after: 78`。

### 配置项说明

| 配置 | 说明 |
|------|------|
| `fonts.english` | 设置后自动复合字体：ASCII 用 english，eastAsia 用中文字体 |
| `indent` | 正文首行缩进（DXA），`h.p()` 自动应用（标题和列表除外） |
| `columns` | 分栏设置，表格和图片自动缩放到栏宽 |
| `h.contentWidth` | 初始化后可用，单栏可用宽度（双栏时自动减半） |
| `h.fullContentWidth` | 始终为页面全宽（双栏跨栏元素用） |

---

## 二、写入与执行

### JS 文件写入

调用 `write_file(path, content, mode="write")` 一次性写入完整 JS 代码。长篇文档分章追加时用 `mode="append"`。

**所有 append 都是往同一个 JS 文件追加代码，不是创建独立模块。** `h`、`refs` 等变量在第一次 write 的骨架中定义一次，后续 append 的函数处于同一文件作用域，可直接使用 `h`、`refs`，**禁止重复 require 或重新定义 `h`**。

编码注意：中文文本直接写原始字符，不要写 `\uXXXX` 转义。

### 执行

**必须通过 `run_node_docx` 执行 JS 文件，禁止直接 `subprocess.run(["node", ...])`。** `run_node_docx` 包含预检、运行和后处理三个阶段，其中后处理会自动修复目录（TOC）缓存条目、Heading 大纲级别、书签 ID 等 docx-js 无法独立完成的工作。直接调用 `node` 会导致目录为空、样式缺失等问题。

```python
import sys, os
sys.path.insert(0, os.path.join(os.environ['SKILL_PATH'], 'docx', 'scripts'))
from run_code_docx import run_node_docx

output = r'<OUTPUT_ROOT>/论文标题.docx'
run_node_docx(r'<OUTPUT_ROOT>/论文标题.js', output=output)
```

---

## 三、API 子集

### 段落与文字

| API | 说明 |
|-----|------|
| `h.p(content, opts?)` | 段落。content 为字符串或 `[str, TextRun, ...]` 混排数组 |
| `h.h1/h2/h3(text, opts?)` | 标题，自动防止与下文分页 |
| `h.text(content, props?)` | 自定义样式文字，用于混排。props: `bold, italic, color, size, font` |
| `h.bold(text)` | 快捷粗体 |

`h.p()` opts 常用属性：`align`（left/center/right/justify）、`size`（半磅字号）、`bold`、`spacing`（`{before, after, line}`）。

### 学术三线表

```javascript
h.threeLineTable({
  widths: [3000, 3000, 3000],
  header: ['变量', '均值', 'p值'],
  rows: [['温度', '23.5', '<0.01'], ['湿度', '65.2', '0.03']],
  caption: '表 1  实验数据汇总',
  captionPosition: 'top',
})
```

有 caption 时返回 `[captionPara, table]` 数组，可直接展开到 children；无 caption 时返回 Table 对象。

### 公式

```javascript
h.p('其中 $\\alpha$ 为显著性水平，$p < 0.05$ 时拒绝原假设。')

h.formula('L = -\\sum_{i=1}^{n} y_i \\log(\\hat{y}_i)', { eqNumber: '1' })

h.p(['由欧拉公式 ', h.math('e^{i\\pi} + 1 = 0'), '，可知...'])
```

- `$...$`：字符串中自动转为行内公式
- `h.math(latex)`：行内公式，放在 `h.p()` 混排数组中
- `h.formula(latex, opts?)`：独立公式段落（居中），`eqNumber` 添加右对齐编号

### 引用管理

```javascript
const refs = h.refTracker();

// 正文中用 [@key] 引用（key 来自检索结果的 stdout 输出）
h.p('深度学习取得显著进展[@wang2024]。多项研究[@li2023,zhang2024]证实有效。'),
h.p('王等人[@wang2024]再次被复用同一序号。'),

// 参考文献：从检索 JSON 自动生成
h.h1('参考文献'),
...refs.autoBibliography(r'<OUTPUT_ROOT>/references.json'),
```

- `[@key]`：内联引用，自动替换为上标编号。多 key 逗号分隔
- 同一 key 复用编号；连续编号自动压缩为范围（如 `[1-4]`）
- `refs.autoBibliography(jsonPath)`：从检索落盘的 JSON 自动筛选被引条目，按首次出现顺序生成参考文献，无需手写条目

### 图片

`h.img()` 返回 Paragraph，**直接放入 sections children，不要嵌套在 `h.p()` 内**：

```javascript
h.img('/path/to/chart.png', { width: 500, height: 300 }),
h.p('图 1  实验结果对比', { size: 18, align: 'center' }),
```

### 布局

| API | 说明 |
|-----|------|
| `h.spacer(height?)` | 空白间距（DXA，默认 400） |
| `h.headerFooter(text)` | 页眉+页脚，展开到 section：`{ ...h.headerFooter('标题'), children }` |
| `h.toc()` | 目录，默认收录 Heading 1-3 |
| `h.fullWidth(...children)` | 双栏文档中让表格/图片横跨整个页面宽度。浮动元素不能跨页，大表格（≥7行）不宜使用 |

---

## 四、封面页

学位论文封面独立为一个 section，不带页眉页脚。信息字段（学院、专业等）**用无边框两列表格对齐**，禁止用全角空格 `\u3000` 手动填充。

封面 section 必须标记 **`cover: true`**，系统会自动检测内容高度并等比压缩 spacer，确保封面不超过一页：

```javascript
function coverSection() {
  const fields = [
    ['题　　目：', '基于深度学习的目标检测研究'],
    ['学　　院：', '计算机科学与技术学院'],
    ['专　　业：', '计算机科学与技术'],
    ['学　　号：', '2024XXXXX'],
    ['姓　　名：', 'XXXXX'],
    ['指导教师：', 'XXXXX'],
  ];
  return [
    h.spacer(2000),
    h.p('XX大学', { size: 44, bold: true, align: 'center' }),
    h.spacer(400),
    h.p('本科毕业论文', { size: 36, bold: true, align: 'center' }),
    h.spacer(1200),
    h.table({
      widths: [3200, 5400],
      rows: fields.map(([label, value]) => [
        { text: label, align: 'right', bold: true, size: 28 },
        { text: value, size: 28 },
      ]),
      noBorders: true,
      align: 'center',
    }),
    h.spacer(800),
    h.p('2025 年 6 月', { size: 24, align: 'center' }),
  ];
}

// build 时标记 cover: true
h.build({
  sections: [
    { children: coverSection(), cover: true },
    // ...其他 section
  ],
});
```

封面字段根据用户提供的信息填写，未提供的保留占位符。硕博论文可增加"研究方向""学位类别"等字段。英文论文同理，替换为对应英文内容。

---

## 五、摘要与关键词

学位论文的中文摘要和英文摘要各自独立为一个 section（自动分页）。

### 单栏（学位论文）

**中文摘要**：

```javascript
function chineseAbstract() {
  return [
    h.h1('摘要', { align: 'center' }),
    h.p('本文提出了一种基于深度学习的...'),
    h.p('...'),
    h.p([h.text('关键词：', { bold: true, font: '黑体' }), h.text('深度学习；目标检测；遥感影像')]),
  ];
}
```

**英文摘要**（独立 section，全文 Times New Roman）：

```javascript
function englishAbstract() {
  return [
    h.h1('Abstract', { align: 'center' }),
    h.p('This paper proposes a deep learning-based approach for...', { font: 'Times New Roman' }),
    h.p('...', { font: 'Times New Roman' }),
    h.p([h.text('Keywords: ', { bold: true, font: 'Times New Roman' }), h.text('deep learning, object detection, remote sensing', { font: 'Times New Roman' })]),
  ];
}
```

### 双栏（期刊/会议论文）

不用标题，"摘要："作为段内粗体标签，摘要在首页而非独立页：

```javascript
h.p([h.text('摘要：', { bold: true, font: '黑体' }), h.text('本文提出...')], { size: 18 }),
h.p([h.text('关键词：', { bold: true, font: '黑体' }), h.text('深度学习；...')], { size: 18 }),
```

英文版同理，换 `font: 'Times New Roman'`，标签改 `Abstract: ` / `Keywords: `。

---

## 六、文档组装

### 单栏（学位论文）

封面 → 中文摘要 → 英文摘要 → 目录 → 各章节，每个均为独立 section：

```javascript
const hf = h.headerFooter('论文标题');

h.build({
  sections: [
    { children: coverSection() },
    { ...hf, children: chineseAbstract() },
    { ...hf, children: englishAbstract() },
    { ...hf, children: tocSection() },
    { ...hf, children: [...introduction()] },
    { ...hf, children: [...litReview()] },
    { ...hf, children: [...methods()] },
    { ...hf, children: [...results()] },
    { ...hf, children: [...conclusion(), h.h1('参考文献'), ...refs.autoBibliography(r'<OUTPUT_ROOT>/references.json')] },
  ],
});
```

### 双栏（期刊/会议论文）

```javascript
const { SectionType } = h.raw;

h.build({
  sections: [
    { children: [...titleBlock(), ...abstractSection()] },
    {
      properties: { type: SectionType.CONTINUOUS, column: { count: 2, space: 468 } },
      children: [
        ...introduction(),
        ...methods(),
        // 栏内表格：widths 基于 h.contentWidth
        // 跨栏表格/图片：...h.fullWidth(h.threeLineTable({...})) 或 ...h.fullWidth(h.img(...), h.p(...))
        ...results(),
        ...conclusion(),
        h.h1('References'),
        ...refs.autoBibliography(r'<OUTPUT_ROOT>/references.json'),
      ],
    },
  ],
});
```

---

## 七、科研可视化 API

在 `python_cell_exec` 中生成图表，保存为 300dpi PNG，然后在 JS 中用 `h.img()` 插入。图片内部**不写标题**（标题写在 DOCX 图注里）。

```python
import sys, os
sys.path.insert(0, os.path.join(os.environ['SKILL_PATH'], 'paper-writer', 'scripts'))
import scientific_visualization as sv

sv.setup_chart_font('zh')  # 中文论文用 'zh'，英文用 'en'。必须在绑图前调用
```

配色 `palette`：`'nature'`（默认）、`'science'`、`'lancet'`、`'nejm'`，每组 8-10 色。

### 图表函数

| 函数 | 说明 | 返回 |
|------|------|------|
| `sv.create_bar_chart(categories, values_dict, title, xlabel, ylabel, palette)` | 分组柱状图 | `fig` |
| `sv.create_line_chart(x_data, lines_dict, title, xlabel, ylabel, palette, markers)` | 折线图 | `fig` |
| `sv.create_scatter_chart(datasets, title, xlabel, ylabel, palette, trendline)` | 散点图 | `fig` |
| `sv.create_pie_chart(labels, values, title, palette, donut)` | 饼图 / 环形图 | `fig` |
| `sv.create_radar_chart(categories, series_dict, title, palette)` | 雷达图 | `fig` |
| `sv.create_heatmap(data, row_labels, col_labels, title, palette, annotate, cmap)` | 热力图 | `fig` |
| `sv.create_flowchart(nodes, edges, title, figsize)` | 流程图 | `fig` |
| `sv.create_architecture_diagram(groups, nodes, connections, title, figsize)` | 架构图（同 flowchart + groups 分组框） | `fig` |
| `sv.render_molecule(smiles, size)` | SMILES → 化学结构式 PNG（需 RDKit） | `BytesIO` or `None` |

**注意**：`title` 参数保持为空（默认 `''`），标题统一写在 DOCX 图注段落里。

### create_bar_chart 示例

```python
fig = sv.create_bar_chart(
    categories=['A组', 'B组', 'C组'],
    values_dict={'方法1': [85, 90, 78], '方法2': [88, 82, 91]},
    xlabel='实验组', ylabel='准确率 (%)', palette='nature',
)
fig.savefig(r'<OUTPUT_ROOT>/bar.png', dpi=300)
```

### flowchart / architecture_diagram 参数

支持**自动布局**（推荐）和手动坐标两种模式。省略所有节点的 `x`, `y` 时自动根据拓扑关系排列，无需手动计算坐标。

| 参数 | 字段 | 说明 |
|------|------|------|
| node | `id`, `text` | 必须 |
| node | `color` | `blue\|green\|orange\|purple\|red\|gray\|teal\|yellow` |
| node | `shape` | `rounded\|rect\|diamond\|ellipse`（默认 rounded） |
| node | `width`, `height` | 可选，默认按 shape 自动 |
| node | `x`, `y` | 可选，全部提供时走手动布局 |
| node | `group` | 可选，architecture_diagram 中指定所属分组 id |
| edge | `from`, `to` | node id |
| edge | `label` | 可选，边上文字 |
| edge | `style` | `solid\|dashed` |
| group | `id`, `label` | 必须（architecture_diagram 专用） |
| group | `color`, `style` | 可选 |

```python
# 自动布局：只需 id, text, color, shape + edges，无需坐标
fig = sv.create_flowchart(
    nodes=[
        {'id': 'start', 'text': '开始', 'shape': 'ellipse', 'color': 'teal'},
        {'id': 'step1', 'text': '数据采集', 'shape': 'rounded', 'color': 'blue'},
        {'id': 'step2', 'text': '数据处理', 'shape': 'rounded', 'color': 'green'},
        {'id': 'end', 'text': '结束', 'shape': 'ellipse', 'color': 'gray'},
    ],
    edges=[
        {'from': 'start', 'to': 'step1'},
        {'from': 'step1', 'to': 'step2'},
        {'from': 'step2', 'to': 'end'},
    ],
)
fig.savefig(r'<OUTPUT_ROOT>/flow.png', dpi=300)
```

---

## 八、排版要点

- **三线表**：顶线 1.5pt + 表头下线 0.75pt + 底线 1.5pt；标题在表格上方居中
- **图题**：图片下方居中，格式 `图 章.序 标题`（英文 `Figure N. Title`）
- **公式**：居中显示，右对齐编号；变量斜体，函数名正体；化学式用上下标 `$Bi_2WO_6$`

## 九、禁止事项

- 禁止写 TypeScript 语法
- 禁止 `new Table()` / `new Paragraph()` / `require('docx')` — 全部通过 `h.xxx()` 调用
- 禁止用 `h.p()` + indent 模拟列表
- 禁止在独立 section 之间加 `h.pageBreak()` — section 自动分页
- 禁止用 Python 写 JS 文件
