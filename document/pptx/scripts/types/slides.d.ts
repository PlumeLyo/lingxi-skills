/**
 * PPT 元素类型定义
 *
 * 定义了 HTML → PPTX 转换流程中的中间表示（IR），
 * 包括文本、图片、形状、线条、表格、LaTeX 公式、图表七种元素类型。
 * html-parser 模块输出此格式，pptx-builder 模块消费此格式。
 *
 * @module types/slides
 */
/** 元素类型枚举常量 */
declare const enum ElementTypes {
    TEXT = "text",
    IMAGE = "image",
    SHAPE = "shape",
    LINE = "line",
    TABLE = "table",
    LATEX = "latex",
    CHART = "chart"
}
/**
 * 渐变
 *
 * type: 渐变类型（径向、线性）
 *
 * colors: 渐变颜色列表（pos: 百分比位置；color: 颜色）
 *
 * rotate: 渐变角度（线性渐变）
 */
type GradientType = "linear" | "radial";
type GradientColor = {
    pos: number;
    color: string;
    opacity?: number;
};
interface Gradient {
    type: GradientType;
    colors: GradientColor[];
    rotate: number;
    /** 径向渐变焦点，0~1 的相对坐标 */
    focusPoint?: {
        x: number;
        y: number;
    };
}
type LineStyleType = "solid" | "dash" | "dashDot" | "lgDash" | "lgDashDot" | "lgDashDotDot" | "sysDash" | "sysDot" | "double";
/**
 * 元素阴影
 *
 * h: 水平偏移量
 *
 * v: 垂直偏移量
 *
 * blur: 模糊程度
 *
 * color: 阴影颜色
 */
interface PPTElementShadow {
    h: number;
    v: number;
    blur: number;
    spread?: number;
    color: string;
    opacity?: number;
}
/**
 * 元素边框
 *
 * style?: 边框样式（实线或虚线）
 *
 * width?: 边框宽度
 *
 * color?: 边框颜色
 */
interface PPTElementOutline {
    style?: LineStyleType;
    width?: number;
    color?: string;
    opacity?: number;
}
type ElementLinkType = "web" | "slide";
/**
 * 元素超链接
 *
 * type: 链接类型（网页、幻灯片页面）
 *
 * target: 目标地址（网页链接、幻灯片页面ID）
 */
interface PPTElementLink {
    type: ElementLinkType;
    target: string;
}
/**
 * 元素通用属性
 *
 * id: 元素ID
 *
 * left: 元素水平方向位置（距离画布左侧）
 *
 * top: 元素垂直方向位置（距离画布顶部）
 *
 * groupId?: 组合ID（拥有相同组合ID的元素即为同一组合元素成员）
 *
 * width: 元素宽度
 *
 * height: 元素高度
 *
 * rotate: 旋转角度
 *
 * link?: 超链接
 *
 * name?: 元素名
 */
interface PPTBaseElement {
    id: string;
    left: number;
    top: number;
    groupId?: string;
    width: number;
    height: number;
    rotate: number;
    link?: PPTElementLink;
    name?: string;
    zIndex?: number;
}
type TextType = "title" | "subtitle" | "content" | "item" | "itemTitle" | "notes" | "header" | "footer" | "partNumber" | "itemNumber";
/**
 * 文本元素
 *
 * type: 元素类型（text）
 *
 * content: 文本内容（HTML字符串）
 *
 * defaultFontName: 默认字体（会被文本内容中的HTML内联样式覆盖）
 *
 * defaultColor: 默认颜色（会被文本内容中的HTML内联样式覆盖）
 *
 * outline?: 边框
 *
 * fill?: 填充色
 *
 * lineHeight?: 行高（倍），默认1.5
 *
 * wordSpace?: 字间距，默认0
 *
 * opacity?: 不透明度，默认1
 *
 * shadow?: 阴影
 *
 * paragraphSpace?: 段间距，默认 5px
 *
 * vertical?: 竖向文本
 *
 * textType?: 文本类型
 *
 * defaultFontSize?: 默认字体大小（pt）
 *
 * align?: 水平对齐方式
 */
interface PPTTextElement extends PPTBaseElement {
    type: "text";
    content: string;
    defaultFontName: string;
    defaultColor: string;
    defaultColorOpacity?: number;
    outline?: PPTElementOutline;
    fill?: string;
    lineHeight?: number;
    wordSpace?: number;
    opacity?: number;
    shadow?: PPTElementShadow;
    paragraphSpace?: number;
    vertical?: boolean;
    textType?: TextType;
    defaultFontSize?: number;
    align?: TextAlign;
    bold?: boolean;
    italic?: boolean;
    valign?: "top" | "middle" | "bottom";
    rectRadius?: number;
    indent?: number;
    textGradient?: Gradient;
    /** 文字描边宽度（pt），来自 -webkit-text-stroke */
    textStrokeWidth?: number;
    /** 文字描边颜色（hex） */
    textStrokeColor?: string;
    /** 文字描边颜色透明度 */
    textStrokeOpacity?: number;
    /** 禁止自动换行（来自 white-space: nowrap / pre） */
    noWrap?: boolean;
}
/**
 * 图片翻转、形状翻转
 *
 * flipH?: 水平翻转
 *
 * flipV?: 垂直翻转
 */
interface ImageOrShapeFlip {
    flipH?: boolean;
    flipV?: boolean;
}
/**
 * 图片滤镜
 *
 * https://developer.mozilla.org/zh-CN/docs/Web/CSS/filter
 *
 * 'blur'?: 模糊，默认0（px）
 *
 * 'brightness'?: 亮度，默认100（%）
 *
 * 'contrast'?: 对比度，默认100（%）
 *
 * 'grayscale'?: 灰度，默认0（%）
 *
 * 'saturate'?: 饱和度，默认100（%）
 *
 * 'hue-rotate'?: 色相旋转，默认0（deg）
 *
 * 'opacity'?: 不透明度，默认100（%）
 */
type ImageElementFilterKeys = "blur" | "brightness" | "contrast" | "grayscale" | "saturate" | "hue-rotate" | "opacity" | "sepia" | "invert";
interface ImageElementFilters {
    blur?: string;
    brightness?: string;
    contrast?: string;
    grayscale?: string;
    saturate?: string;
    "hue-rotate"?: string;
    sepia?: string;
    invert?: string;
    opacity?: string;
}
type ImageClipDataRange = [[number, number], [number, number]];
/**
 * 图片裁剪
 *
 * range: 裁剪范围，例如：[[10, 10], [90, 90]] 表示裁取原图从左上角 10%, 10% 到 90%, 90% 的范围
 *
 * shape: 裁剪形状，见 configs/imageClip.ts CLIPPATHS
 */
interface ImageElementClip {
    range: ImageClipDataRange;
    shape: string;
}
type ImageType = "pageFigure" | "itemFigure" | "background";
/**
 * 图片元素
 *
 * type: 元素类型（image）
 *
 * fixedRatio: 固定图片宽高比例
 *
 * src: 图片地址
 *
 * outline?: 边框
 *
 * filters?: 图片滤镜
 *
 * clip?: 裁剪信息
 *
 * flipH?: 水平翻转
 *
 * flipV?: 垂直翻转
 *
 * shadow?: 阴影
 *
 * radius?: 圆角半径
 *
 * colorMask?: 颜色蒙版
 *
 * imageType?: 图片类型
 */
interface PPTImageElement extends PPTBaseElement {
    type: "image";
    fixedRatio: boolean;
    src: string;
    outline?: PPTElementOutline;
    filters?: ImageElementFilters;
    clip?: ImageElementClip;
    flipH?: boolean;
    flipV?: boolean;
    shadow?: PPTElementShadow;
    radius?: number;
    colorMask?: string;
    imageType?: ImageType;
    opacity?: number;
    /** 自定义几何裁剪路径（SVG path d），用于 clip-path polygon 等非矩形裁剪 */
    customPath?: string;
    /** 自定义几何的 viewBox [width, height]，与 customPath 配合使用 */
    customViewBox?: [number, number];
}
type ShapeTextAlign = "top" | "middle" | "bottom";
/**
 * 形状内文本
 *
 * content: 文本内容（HTML字符串）
 *
 * defaultFontName: 默认字体（会被文本内容中的HTML内联样式覆盖）
 *
 * defaultColor: 默认颜色（会被文本内容中的HTML内联样式覆盖）
 *
 * align: 文本对齐方向（垂直方向）
 *
 * lineHeight?: 行高（倍），默认1.5
 *
 * wordSpace?: 字间距，默认0
 *
 * paragraphSpace?: 段间距，默认 5px
 *
 * type: 文本类型
 */
interface ShapeText {
    content: string;
    defaultFontName: string;
    defaultColor: string;
    opacity?: number;
    align: ShapeTextAlign;
    hAlign?: TextAlign;
    lineHeight?: number;
    wordSpace?: number;
    paragraphSpace?: number;
    type?: TextType;
}
declare const enum ShapePathFormulasKeys {
    ROUND_RECT = "roundRect",
    ROUND_RECT_DIAGONAL = "roundRectDiagonal",
    ROUND_RECT_SINGLE = "roundRectSingle",
    ROUND_RECT_SAMESIDE = "roundRectSameSide",
    CUT_RECT_DIAGONAL = "cutRectDiagonal",
    CUT_RECT_SINGLE = "cutRectSingle",
    CUT_RECT_SAMESIDE = "cutRectSameSide",
    CUT_ROUND_RECT = "cutRoundRect",
    MESSAGE = "message",
    ROUND_MESSAGE = "roundMessage",
    L = "L",
    RING_RECT = "ringRect",
    PLUS = "plus",
    TRIANGLE = "triangle",
    PARALLELOGRAM_LEFT = "parallelogramLeft",
    PARALLELOGRAM_RIGHT = "parallelogramRight",
    TRAPEZOID = "trapezoid",
    BULLET = "bullet",
    INDICATOR = "indicator",
    DONUT = "donut",
    DIAGSTRIPE = "diagStripe"
}
/**
 * 形状元素
 *
 * type: 元素类型（shape）
 *
 * viewBox: SVG的viewBox属性，例如 [1000, 1000] 表示 '0 0 1000 1000'
 *
 * path: 形状路径，SVG path 的 d 属性
 *
 * fixedRatio: 固定形状宽高比例
 *
 * fill: 填充，不存在渐变时生效
 *
 * gradient?: 渐变，该属性存在时将优先作为填充
 *
 * pattern?: 图案，该属性存在时将优先作为填充
 *
 * outline?: 边框
 *
 * opacity?: 不透明度
 *
 * flipH?: 水平翻转
 *
 * flipV?: 垂直翻转
 *
 * shadow?: 阴影
 *
 * special?: 特殊形状（标记一些难以解析的形状，例如路径使用了 L Q C A 以外的类型，该类形状在导出后将变为图片的形式）
 *
 * text?: 形状内文本
 *
 * pathFormula?: 形状路径计算公式
 * 一般情况下，形状的大小变化时仅由宽高基于 viewBox 的缩放比例来调整形状，而 viewBox 本身和 path 不会变化，
 * 但也有一些形状希望能更精确的控制一些关键点的位置，此时就需要提供路径计算公式，通过在缩放时更新 viewBox 并重新计算 path 来重新绘制形状
 *
 * keypoints?: 关键点位置百分比
 */
interface PPTShapeElement extends PPTBaseElement {
    type: "shape";
    viewBox: [number, number];
    path: string;
    fixedRatio: boolean;
    fill: string;
    gradient?: Gradient;
    pattern?: string;
    outline?: PPTElementOutline;
    opacity?: number;
    flipH?: boolean;
    flipV?: boolean;
    shadow?: PPTElementShadow;
    special?: boolean;
    text?: ShapeText;
    pathFormula?: ShapePathFormulasKeys;
    keypoints?: number[];
    shapeType?: "ellipse" | "roundRect";
    fillTransparency?: number;
}
type LinePoint = "" | "arrow" | "dot";
/**
 * 线条元素
 *
 * type: 元素类型（line）
 *
 * start: 起点位置（[x, y]）
 *
 * end: 终点位置（[x, y]）
 *
 * style: 线条样式（实线、虚线、点线）
 *
 * color: 线条颜色
 *
 * points: 端点样式（[起点样式, 终点样式]，可选：无、箭头、圆点）
 *
 * shadow?: 阴影
 *
 * broken?: 折线控制点位置（[x, y]）
 *
 * broken2?: 双折线控制点位置（[x, y]）
 *
 * curve?: 二次曲线控制点位置（[x, y]）
 *
 * cubic?: 三次曲线控制点位置（[[x1, y1], [x2, y2]]）
 */
interface PPTLineElement extends Omit<PPTBaseElement, "height" | "rotate"> {
    type: "line";
    start: [number, number];
    end: [number, number];
    style: LineStyleType;
    color: string;
    points: [LinePoint, LinePoint];
    shadow?: PPTElementShadow;
    strokeWidth?: number;
    opacity?: number;
    broken?: [number, number];
    broken2?: [number, number];
    curve?: [number, number];
    cubic?: [[number, number], [number, number]];
}
type TextAlign = "left" | "center" | "right" | "justify";
/**
 * 表格单元格单边边框
 */
interface TableCellBorderStyle {
    style?: LineStyleType;
    width?: number;
    color?: string;
    opacity?: number;
}
/**
 * 表格单元格样式
 *
 * bold?: 加粗
 *
 * em?: 斜体
 *
 * underline?: 下划线
 *
 * strikethrough?: 删除线
 *
 * color?: 字体颜色
 *
 * backcolor?: 填充色
 *
 * fontsize?: 字体大小
 *
 * fontname?: 字体
 *
 * align?: 水平对齐方式
 *
 * valign?: 垂直对齐方式（top/middle/bottom）
 *
 * paddingTop/paddingRight/paddingBottom/paddingLeft?: 内边距（pt）
 */
interface TableCellStyle {
    bold?: boolean;
    em?: boolean;
    underline?: boolean;
    underlineColor?: string;
    strikethrough?: boolean;
    color?: string;
    opacity?: number;
    backcolor?: string;
    backcolorOpacity?: number;
    fontsize?: string;
    fontname?: string;
    align?: TextAlign;
    valign?: "top" | "middle" | "bottom";
    lineHeight?: number;
    paddingTop?: number;
    paddingRight?: number;
    paddingBottom?: number;
    paddingLeft?: number;
    borderTop?: TableCellBorderStyle;
    borderRight?: TableCellBorderStyle;
    borderBottom?: TableCellBorderStyle;
    borderLeft?: TableCellBorderStyle;
}
/**
 * 表格单元格内的文本片段（富文本 run）
 *
 * 当单元格内有多个不同样式的子元素时，每个子元素对应一个 run。
 */
interface TableCellTextRun {
    text: string;
    bold?: boolean;
    em?: boolean;
    underline?: boolean;
    underlineColor?: string;
    strikethrough?: boolean;
    color?: string;
    opacity?: number;
    fontsize?: string;
    fontname?: string;
    indent?: number;
}
/**
 * 表格单元格
 *
 * id: 单元格ID
 *
 * colspan: 合并列数
 *
 * rowspan: 合并行数
 *
 * text: 文字内容
 *
 * textRuns?: 富文本片段（优先于 text + style 渲染）
 *
 * style?: 单元格样式
 */
interface TableCell {
    id: string;
    colspan: number;
    rowspan: number;
    text: string;
    textRuns?: TableCellTextRun[];
    style?: TableCellStyle;
}
/**
 * 表格主题
 *
 * color: 主题色
 *
 * rowHeader: 标题行
 *
 * rowFooter: 汇总行
 *
 * colHeader: 第一列
 *
 * colFooter: 最后一列
 */
interface TableTheme {
    color: string;
    rowHeader: boolean;
    rowFooter: boolean;
    colHeader: boolean;
    colFooter: boolean;
}
/**
 * 表格元素
 *
 * type: 元素类型（table）
 *
 * outline: 边框
 *
 * theme?: 主题
 *
 * colWidths: 列宽数组，如[0.3, 0.5, 0.2]表示三列宽度分别占总宽度的30%, 50%, 20%
 *
 * cellMinHeight: 单元格最小高度
 *
 * data: 表格数据
 */
interface PPTTableElement extends PPTBaseElement {
    type: "table";
    outline?: PPTElementOutline;
    theme?: TableTheme;
    colWidths: number[];
    rowHeights: number[];
    cellMinHeight: number;
    data: TableCell[][];
}
/**
 * LaTeX元素（公式）
 *
 * type: 元素类型（latex）
 *
 * latex: latex代码
 *
 * path: svg path
 *
 * color: 颜色
 *
 * strokeWidth: 路径宽度
 *
 * viewBox: SVG的viewBox属性
 *
 * fixedRatio: 固定形状宽高比例
 */
interface PPTLatexElement extends PPTBaseElement {
    type: "latex";
    latex: string;
    path: string;
    color: string;
    opacity?: number;
    strokeWidth: number;
    viewBox: [number, number];
    fixedRatio: boolean;
}
/**
 * 图表类型（PPT 原生支持）
 *
 * bar: 柱状图 / 条形图
 * line: 折线图
 * pie: 饼图
 * scatter: 散点图
 * radar: 雷达图
 * candlestick: K 线图
 */
type ChartType = "bar" | "line" | "pie" | "scatter" | "radar" | "candlestick";
/** 面积填充渐变色标 */
interface ChartGradientStop {
    offset: number;
    color: string;
    opacity: number;
}
/** 面积填充配置 */
interface ChartAreaFill {
    type: "solid" | "gradient";
    color?: string;
    opacity?: number;
    gradientStops?: ChartGradientStop[];
}
/** 折线图线条与标记样式 */
interface ChartLineStyle {
    /** 是否平滑曲线 */
    smooth?: boolean;
    /** 线宽（pt），默认 2 */
    width?: number;
    /** 虚线样式 */
    dash?: "solid" | "dash" | "dot" | "dashDot";
    /** 是否显示数据点标记，默认 true */
    showMarkers?: boolean;
    /** 数据点标记颜色（不同于线条颜色时使用） */
    markerColor?: string;
    /** 数据点标记大小（OOXML size 单位，2~72），默认 5 */
    markerSize?: number;
    /** 数据点标记是否实心填充（false/undefined=空心） */
    markerFilled?: boolean;
    /** 数据点标记描边颜色（HEX） */
    markerBorderColor?: string;
    /** 数据点标记描边宽度（pt） */
    markerBorderWidth?: number;
    /** 面积填充配置（折线图下方填充） */
    areaFill?: ChartAreaFill;
}
/** 数据标签配置 */
interface ChartDataLabel {
    /** 是否显示数据标签 */
    show?: boolean;
    /** 需要显示数值标签的数据点索引列表（用于 markPoint） */
    indices?: number[];
    /** 标签/标注点颜色 */
    color?: string;
    /** 字号（百分之一磅，OOXML sz 值） */
    fontSize?: number;
    /** 加粗 */
    bold?: boolean;
    /** 数值格式（OOXML numFmt formatCode） */
    format?: string;
    /** 位置（OOXML dLblPos val） */
    position?: "t" | "b" | "l" | "r" | "ctr" | "inBase" | "inEnd" | "outEnd";
    /** 是否显示类别名（饼图） */
    showCatName?: boolean;
    /** 是否显示数值（默认 true，饼图无 formatter 时为 false） */
    showVal?: boolean;
    /** 是否显示百分比（ECharts {d} 变量） */
    showPercent?: boolean;
    /** 多个标签部分之间的分隔文本 */
    separator?: string;
    /** 逐数据点格式（函数 formatter 对不同数据点产生不同前缀/后缀时使用） */
    pointFormats?: (string | undefined)[];
    /** 逐数据点位置（数据项级 label.position 不统一时使用） */
    pointPositions?: (ChartDataLabel["position"] | undefined)[];
    /** 逐数据点颜色（数据项级 label.color 不统一时使用） */
    pointColors?: (string | undefined)[];
}
/** 单个数据点的独立样式 */
interface ChartPointStyle {
    /** 颜色（HEX） */
    color?: string;
    /** 纯色不透明度（0~1），用于 rgba 颜色 */
    opacity?: number;
    /** 渐变填充 */
    gradient?: ChartGradientStop[];
    /** 渐变角度（OOXML 单位：60000 分之一度） */
    gradientAngle?: number;
}
/** 散点图数据点 [x, y] */
type ScatterDataPoint = [number, number];
/** 散点图单个数据点的独立样式 */
interface ScatterPointStyle {
    /** 标记颜色（HEX） */
    color?: string;
    /** 标记不透明度 0~1 */
    opacity?: number;
    /** 标记大小（OOXML size 单位，2~72） */
    symbolSize?: number;
    /** 标记阴影颜色（HEX）*/
    shadowColor?: string;
    /** 标记阴影不透明度（0~1）*/
    shadowOpacity?: number;
}
/** 散点图标记样式（系列级默认值） */
interface ChartScatterStyle {
    /** 标记符号形状 */
    symbol?: "circle" | "square" | "diamond" | "triangle";
    /** 标记大小（OOXML size 单位，2~72），默认 5 */
    symbolSize?: number;
    /** 标记是否实心，默认 true */
    filled?: boolean;
    /** 标记边框颜色（HEX） */
    borderColor?: string;
    /** 标记边框宽度（pt） */
    borderWidth?: number;
    /** 每个数据点的独立样式（颜色/大小不同于系列默认值时） */
    pointOverrides?: (ScatterPointStyle | undefined)[];
    /** 是否显示标记点，默认 true。line 转 scatter 时设为 false */
    showMarker?: boolean;
    /** 连接线宽度（px），大于 0 时画线 */
    lineWidth?: number;
    /** 连接线虚线类型（OOXML preset dash） */
    lineDash?: string;
    /** 数据标签文本列表（与 scatterData 一一对应） */
    labels?: (string | undefined)[];
    /** 数据标签位置（OOXML dLblPos） */
    labelPosition?: string;
    /** 数据标签字号（百分之一磅） */
    labelFontSize?: number;
    /** 数据标签颜色（HEX） */
    labelColor?: string;
    /** 数据标签是否加粗 */
    labelBold?: boolean;
    /** 标记阴影模糊半径（pt），来自 ECharts itemStyle.shadowBlur */
    shadowBlurPt?: number;
    /** 标记阴影颜色（HEX） */
    shadowColor?: string;
    /** 标记阴影不透明度（0~1） */
    shadowOpacity?: number;
    /** 标记径向渐变填充停靠点（来自 ECharts 渐变色 itemStyle.color） */
    radialGradientStops?: ChartGradientStop[];
}
/** K 线图数据点 [open, close, low, high] */
type CandlestickDataPoint = [number, number, number, number];
/** K 线图专属配置 */
interface ChartCandlestickConfig {
    /** 上涨颜色（HEX），默认红色 */
    upColor?: string;
    /** 下跌颜色（HEX），默认绿色 */
    downColor?: string;
    /** 上涨边框颜色（HEX） */
    upBorderColor?: string;
    /** 下跌边框颜色（HEX） */
    downBorderColor?: string;
}
/** markLine 末尾标签 */
interface ChartMarkLineLabel {
    text: string;
    color?: string;
    /** 字号（百分之一磅，OOXML sz 值） */
    fontSize?: number;
    /** 是否加粗 */
    bold?: boolean;
    /** 标签位置（OOXML dLblPos 值），默认 'r' */
    position?: string;
}
/** 图表数据系列 */
interface ChartSeries {
    name: string;
    type: ChartType;
    data: (number | null)[];
    color?: string;
    /** 系列颜色不透明度（0~1），默认 1 */
    opacity?: number;
    /** 绑定的数值轴索引（0=主轴, 1=次轴），默认 0 */
    valueAxisIndex?: number;
    /** 折线图样式（仅 type='line' 时使用） */
    lineStyle?: ChartLineStyle;
    /** 数据标签配置 */
    dataLabel?: ChartDataLabel;
    /** 每个数据点的独立样式 */
    pointStyles?: (ChartPointStyle | undefined)[];
    /** 系列级渐变填充（柱状图渐变色等） */
    gradientFill?: ChartGradientStop[];
    /** 渐变角度（OOXML 单位：60000 分之一度），5400000=自上而下，0=自左而右 */
    gradientAngle?: number;
    /** 饼图/圆环图：系列独立类别名（嵌套环形图中每个 series 类别不同） */
    categories?: string[];
    /** 饼图/圆环图：系列独立内孔大小（嵌套环形图中每个 series 半径不同） */
    holeSize?: number;
    /** 散点图 XY 数据（仅 type='scatter' 时使用），与 data 互斥 */
    scatterData?: ScatterDataPoint[];
    /** 散点图标记样式（仅 type='scatter' 时使用） */
    scatterStyle?: ChartScatterStyle;
    /** 雷达图填充区域不透明度（0~1），仅 type='radar' 且 radarStyle='filled' 时使用 */
    areaOpacity?: number;
    /** K 线图 OHLC 数据（仅 type='candlestick' 时使用），与 data 互斥 */
    candlestickData?: CandlestickDataPoint[];
    /** markLine 末尾标签（在最后一个数据点显示自定义文本） */
    markLineLabel?: ChartMarkLineLabel;
}
/** 图表类别轴 */
interface ChartAxis {
    categories: string[];
    title?: string;
    /** 轴标签字体颜色 */
    labelColor?: string;
    /** 轴标签是否加粗 */
    labelBold?: boolean;
    /** 轴标签字号（百分之一磅，OOXML sz 值） */
    labelFontSize?: number;
    /** 是否显示轴线，默认 true */
    showAxisLine?: boolean;
    /** 轴线颜色（HEX） */
    axisLineColor?: string;
    /** 轴线宽度（磅） */
    axisLineWidth?: number;
    /** 是否显示刻度标记，默认 true */
    showTickMarks?: boolean;
    /** 数据点是否在刻度之间（true=柱状图默认，false=折线图 boundaryGap:false） */
    crossBetween?: boolean;
    /** 轴标签跳过间隔（1=每个都显示，2=隔一个显示一个，依此类推） */
    tickLabelSkip?: number;
    /** 是否显示网格线（来自 splitLine.show） */
    showGridLines?: boolean;
    /** 网格线颜色 */
    gridLineColor?: string;
    /** 网格线不透明度（0~1） */
    gridLineOpacity?: number;
    /** 网格线宽度（磅） */
    gridLineWidth?: number;
    /** 网格线样式 */
    gridLineDash?: "solid" | "dash" | "dot";
}
/** 图表数值轴 */
interface ChartValueAxis {
    /** 是否隐藏整个轴（标签、轴线、刻度不显示，网格线保留） */
    hidden?: boolean;
    title?: string;
    /** 轴标题位置：'end'=轴末端（默认）, 'middle'=居中并旋转 */
    titleLocation?: "start" | "middle" | "end";
    /** 轴标题宽高占图表容器的比例（0~1） */
    titleSize?: {
        w: number;
        h: number;
    };
    min?: number;
    max?: number;
    /** 轴位置（l=左, r=右, t=上, b=下） */
    position?: "l" | "r" | "t" | "b";
    /** 主刻度间隔 */
    majorUnit?: number;
    /** 是否显示网格线 */
    showGridLines?: boolean;
    /** 网格线颜色 */
    gridLineColor?: string;
    /** 网格线不透明度（0~1），默认 1 */
    gridLineOpacity?: number;
    /** 网格线宽度（磅） */
    gridLineWidth?: number;
    /** 网格线样式 */
    gridLineDash?: "solid" | "dash" | "dot";
    /** 轴标签字体颜色 */
    labelColor?: string;
    /** 轴标签字号（百分之一磅，OOXML sz 值） */
    labelFontSize?: number;
    /** 轴标题字号（百分之一磅，OOXML sz 值） */
    titleFontSize?: number;
    /** 轴标题颜色 */
    titleColor?: string;
    /** 轴标签数值格式（OOXML numFmt formatCode） */
    numFmt?: string;
    /** 是否显示轴线，默认 true */
    showAxisLine?: boolean;
    /** 轴线颜色（HEX） */
    axisLineColor?: string;
    /** 轴线宽度（磅） */
    axisLineWidth?: number;
    /** 是否显示刻度标记，默认 true */
    showTickMarks?: boolean;
}
/**
 * 图表元素
 *
 * type: 元素类型（chart）
 *
 * chartType: 图表主类型（bar / line / pie）
 *
 * series: 数据系列列表
 *
 * categoryAxis?: 类别轴（bar/line 使用）
 *
 * title?: 图表标题
 *
 * colors?: 调色板（覆盖默认配色）
 *
 * showLegend?: 是否显示图例
 *
 * barDir?: 柱状图方向（col=纵向, bar=横向）
 *
 * stacked?: 是否堆叠
 */
/** 饼图/圆环图专属配置 */
interface ChartPieConfig {
    /** 圆环图内孔大小（0~90%），大于 0 时生成 doughnutChart */
    holeSize?: number;
    /** 起始角度（OOXML 单位：度，默认 0） */
    firstSliceAng?: number;
    /** 扇区边框颜色（HEX），用于扇区间白色间隔效果 */
    borderColor?: string;
    /** 扇区边框宽度（pt） */
    borderWidth?: number;
    /** 标签引导线颜色（HEX） */
    labelLineColor?: string;
    /** 标签引导线不透明度（0~1） */
    labelLineOpacity?: number;
    /** 圆环图中心文本（position: 'center' 的 label） */
    centerText?: ChartCenterText;
}
/** 雷达图轴归一化信息（各 indicator max 不一致时使用） */
interface ChartRadarNormalization {
    /** 每个类别（indicator）的缩放比例，length = categories.length */
    ratios: number[];
    /** 归一化前的原始数据，[seriesIdx][catIdx] */
    rawData: (number | null)[][];
}
/** 雷达图专属配置 */
interface ChartRadarConfig {
    /** 雷达图样式：radar=仅线条, marker=带标记, filled=填充 */
    style?: "radar" | "marker" | "filled";
    /** 轴归一化信息（各 indicator max 不一致时，数据乘以缩放比例使图形不畸形） */
    normalization?: ChartRadarNormalization;
}
/** 柱状图专属配置 */
interface ChartBarConfig {
    /** 方向（col=纵向, bar=横向） */
    dir?: "col" | "bar";
    /** 间隙宽度（OOXML gapWidth 百分比），默认 150 */
    gapWidth?: number;
    /** 副轴柱系列的间隙宽度，未设置时回退到 gapWidth */
    secondaryGapWidth?: number;
    /** 重叠度（OOXML overlap，-100~100），负值表示柱子间有间距 */
    overlap?: number;
}
interface PPTChartElement extends PPTBaseElement {
    type: "chart";
    chartType: ChartType;
    series: ChartSeries[];
    categoryAxis?: ChartAxis;
    /** 数值轴列表（主轴 + 可选次轴） */
    valueAxes?: ChartValueAxis[];
    title?: string;
    /** 图表标题字号（百分之一磅，OOXML sz 值） */
    titleFontSize?: number;
    /** 图表标题颜色（HEX） */
    titleColor?: string;
    colors?: string[];
    showLegend?: boolean;
    /** 图例位置 */
    legendPosition?: "b" | "t" | "l" | "r";
    /** 图例字号（百分之一磅，OOXML sz 值） */
    legendFontSize?: number;
    /** 图例文字颜色（HEX） */
    legendFontColor?: string;
    stacked?: boolean;
    /** 柱状图配置 */
    barConfig?: ChartBarConfig;
    /** 饼图/圆环图配置 */
    pieConfig?: ChartPieConfig;
    /** 雷达图配置 */
    radarConfig?: ChartRadarConfig;
    /** K 线图配置 */
    candlestickConfig?: ChartCandlestickConfig;
    /** 图表区域背景色（HEX） */
    backgroundColor?: string;
    /** 图表区域圆角半径（pt） */
    borderRadius?: number;
    /** 绘图区域边距（0~1 相对坐标） */
    plotArea?: {
        x: number;
        y: number;
        w: number;
        h: number;
    };
    /** ECharts graphic 文本叠加层 */
    graphicTexts?: ChartGraphicText[];
}
/** 圆环图中心富文本中的单个文本片段 */
interface ChartCenterTextRun {
    text: string;
    /** 字号（百分之一磅，OOXML sz 值） */
    fontSize?: number;
    bold?: boolean;
    /** 颜色（HEX） */
    color?: string;
}
/** 圆环图中心文本，由多行富文本组成 */
interface ChartCenterText {
    lines: ChartCenterTextRun[][];
}
/** ECharts graphic 文本元素（叠加在图表上方的自定义文本） */
interface ChartGraphicText {
    text: string;
    /** 水平位置（0~1 相对坐标） */
    x: number;
    /** 垂直位置（0~1 相对坐标） */
    y: number;
    /** 字号（百分之一磅，OOXML sz 值） */
    fontSize?: number;
    bold?: boolean;
    color?: string;
    fontFamily?: string;
    align?: "left" | "center" | "right";
}
type PPTElement = PPTTextElement | PPTImageElement | PPTShapeElement | PPTLineElement | PPTTableElement | PPTLatexElement | PPTChartElement;
export { ElementTypes, ShapePathFormulasKeys };
export type { GradientType, GradientColor, Gradient, LineStyleType, PPTElementShadow, PPTElementOutline, ElementLinkType, PPTElementLink, TextType, PPTTextElement, ImageOrShapeFlip, ImageElementFilterKeys, ImageElementFilters, ImageClipDataRange, ImageElementClip, ImageType, PPTImageElement, ShapeTextAlign, ShapeText, PPTShapeElement, LinePoint, PPTLineElement, TextAlign, TableCellBorderStyle, TableCellStyle, TableCellTextRun, TableCell, TableTheme, PPTTableElement, PPTLatexElement, ChartType, ChartGradientStop, ChartAreaFill, ChartLineStyle, ChartDataLabel, ChartPointStyle, ScatterDataPoint, ScatterPointStyle, ChartScatterStyle, ChartMarkLineLabel, ChartSeries, ChartAxis, ChartValueAxis, ChartPieConfig, ChartRadarNormalization, ChartRadarConfig, ChartBarConfig, CandlestickDataPoint, ChartCandlestickConfig, ChartCenterTextRun, ChartCenterText, ChartGraphicText, PPTChartElement, PPTElement, };
