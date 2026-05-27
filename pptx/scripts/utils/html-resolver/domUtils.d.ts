import { BorderRadiusPt } from './types';
import { TextAlign } from '../../types/slides';
/** 解析时需要跳过的不可见标签集合 */
declare const SKIP_TAGS: Set<string>;
/**
 * 判断元素是否为纯色背景（无背景图且非透明）
 * @param element DOM 元素
 * @returns 是否为纯色背景
 */
declare function isSolidBackground(element: Element): boolean;
/**
 * 判断 backgroundImage 是否包含多层渐变（2 层及以上）。
 * 多层渐变在 PPTX 中无法用原生渐变表达，需降级为截图。
 */
declare function hasMultiLayerGradient(backgroundImage: string): boolean;
/**
 * 根据 font-weight 判断是否为粗体
 * @param fontWeight CSS font-weight 值
 * @returns 是否为粗体
 */
declare function isFontBold(fontWeight: string): boolean;
/**
 * 从 font-family 中选取第一个 PPT 支持的字体，否则返回默认字体
 * @param rawFontFamily 原始 font-family 字符串
 * @returns PPT 支持的字体名
 */
declare function normalizeFontFamily(rawFontFamily: string): string;
/**
 * 判断元素是否应跳过解析（脚本/样式/隐藏/零尺寸等）
 * @param element DOM 元素
 * @returns 是否应跳过
 */
declare function shouldSkipElement(element: Element): boolean;
/**
 * 判断是否为纯装饰元素，满足以下任一组条件：
 * 1. pointer-events:none、无文本、有非渐变背景图
 * 2. 无文本、无子元素、背景仅含 repeating-linear-gradient（条纹装饰）
 * @param element DOM 元素
 * @returns 是否为装饰元素
 */
declare function isDecorativeElement(element: Element): boolean;
/**
 * 判断文本的父元素是否在 SKIP_TAGS 中，应跳过文本提取
 * @param parentElement 父元素
 * @returns 是否应跳过
 */
declare function shouldSkipTextParent(parentElement: Element | null): boolean;
/**
 * 获取元素四角圆角值（pt），椭圆圆角时同时填充 XY 字段
 * @param element DOM 元素
 * @returns 四角圆角 pt 值
 */
declare function getBorderRadiusPtPerCorner(element: Element): BorderRadiusPt;
/**
 * 查找最近的 overflow:hidden/clip 祖先
 * @param element 起始 DOM 元素
 * @returns 最近的裁剪祖先；不存在则返回 null
 */
declare function findOverflowClipAncestor(element: Element): Element | null;
/**
 * 判断元素是否具有可见圆角
 * @param element DOM 元素
 * @returns 任一角半径大于 0 时返回 true
 */
declare function hasRoundedCorners(element: Element): boolean;
/**
 * 判断是否有椭圆圆角（某角含 x y 两个值）
 * @param element DOM 元素
 * @returns 是否有椭圆圆角
 */
declare function hasIrregularBorderRadius(element: Element): boolean;
type VerticalAlign = "top" | "middle" | "bottom";
/**
 * 判断样式是否为 Flex 容器
 * @param style 元素计算样式
 * @returns 是否为 Flex 容器
 */
declare function isFlexContainer(style: CSSStyleDeclaration): boolean;
/**
 * 判断计算后的 display 值是否为块级布局
 */
declare function isBlockDisplay(display: string): boolean;
/**
 * 判断 Flex 主轴是否为水平方向
 * @param style 元素计算样式
 * @returns 是否为 row 或 row-reverse
 */
declare function isFlexRow(style: CSSStyleDeclaration): boolean;
/**
 * 解析 Flex 容器内单子项的对齐方式
 * @param style 元素计算样式
 * @returns 水平与垂直对齐，非 Flex 容器时返回 null
 */
declare function resolveSingleItemFlexAlignment(style: CSSStyleDeclaration): {
    hAlign: TextAlign;
    vAlign: VerticalAlign;
} | null;
type RadiusInput = number | {
    rx: number;
    ry: number;
};
/**
 * 计算圆角缩放因子
 * @param tl 左上角半径
 * @param tr 右上角半径
 * @param br 右下角半径
 * @param bl 左下角半径
 * @param width 宽度
 * @param height 高度
 * @returns ≤1 的缩放因子
 */
declare function computeRadiusClampFactor(tl: RadiusInput, tr: RadiusInput, br: RadiusInput, bl: RadiusInput, width: number, height: number): number;
type ShapeTypeResolution = {
    shapeType?: "ellipse" | "roundRect";
    keypoints?: number[];
};
/**
 * 根据圆角信息推断形状类型
 * @param borderRadius 圆角信息
 * @param widthPt 宽度
 * @param heightPt 高度
 * @returns 形状类型
 */
declare function inferShapeTypeFromRadius(borderRadius: BorderRadiusPt, widthPt: number, heightPt: number): ShapeTypeResolution;
/**
 * 从 DOM 元素解析 CSS z-index，返回有效数值或 NaN
 * @param element 待解析的 DOM 元素
 * @returns CSS z-index 数值，无效时返回 NaN
 */
declare function parseCssZIndex(element: Element): number;
interface MaskGradientBorderWidths {
    borderTop: number;
    borderRight: number;
    borderBottom: number;
    borderLeft: number;
}
/**
 * 检测 CSS mask 渐变边框技巧：
 * gradient background + transparent border + CSS mask。
 * 同时适用于 DOM 元素和伪元素。
 * @returns 各边 border 宽度（px），未检测到则返回 null
 */
declare function isMaskGradientBorder(style: CSSStyleDeclaration): MaskGradientBorderWidths | null;
/**
 * 递归查找元素中第一个可见文本节点（按文档顺序）。
 * 跳过绝对/固定定位的子元素，因为它们不参与正常文本流布局。
 */
declare function findFirstVisibleTextNode(element: Element): ChildNode | null;
/**
 * 测量元素中第一个文本字符的 DOMRect（利用 Range API）。
 * 返回 null 表示元素无可见文本或测量失败。
 */
declare function measureFirstCharRect(element: Element): DOMRect | null;
export type { ShapeTypeResolution, MaskGradientBorderWidths };
/**
 * 计算非绝对定位伪元素在父容器内的布局偏移。
 * 根据父容器的 flex/block 布局属性推算伪元素的 localLeft/localTop。
 */
declare function computeStaticPseudoOffset(containerStyle: CSSStyleDeclaration, pseudoStyle: CSSStyleDeclaration, containerW: number, containerH: number, itemW: number, itemH: number): {
    left: number;
    top: number;
};
/**
 * 判断元素是否与浮动元素隔离（建立了独立的块格式化上下文）。
 * 隔离元素的边界框不会延伸到浮动区域下方，无需位移修正。
 */
declare function isIsolatedFromFloat(style: CSSStyleDeclaration): boolean;
export { SKIP_TAGS, isSolidBackground, isFontBold, normalizeFontFamily, shouldSkipElement, isDecorativeElement, shouldSkipTextParent, getBorderRadiusPtPerCorner, findOverflowClipAncestor, hasRoundedCorners, hasIrregularBorderRadius, isFlexContainer, isBlockDisplay, isFlexRow, resolveSingleItemFlexAlignment, computeRadiusClampFactor, inferShapeTypeFromRadius, parseCssZIndex, isMaskGradientBorder, hasMultiLayerGradient, findFirstVisibleTextNode, measureFirstCharRect, computeStaticPseudoOffset, isIsolatedFromFloat, };
