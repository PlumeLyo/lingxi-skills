import { PPTShapeElement, PPTElement } from '../../types/slides';
import { ResolveContext, BorderRadiusPt } from './types';
import { BorderEdgeDetail } from './borderUtils';
/**
 * 将闭合 SVG path 裁剪到可视矩形内，并将坐标平移为裁剪后 viewBox 的局部坐标
 */
/**
 * 解析 CSS clip-path: polygon(...) 为 SVG path 字符串
 * 支持百分比和 px 绝对值坐标
 */
declare function parseClipPathPolygon(clipPath: string | undefined | null, viewBoxW: number, viewBoxH: number): string | null;
/**
 * 构建圆角矩形 SVG path（含弧线段）
 * @param width 矩形宽度（pt）
 * @param height 矩形高度（pt）
 * @param radius 四角圆角半径
 * @returns SVG path 字符串
 */
declare function buildRoundRectPath(width: number, height: number, radius: BorderRadiusPt): string;
/**
 * 构建环形（donut）路径：外层圆角矩形顺时针 + 内层圆角矩形逆时针。
 * 用于 CSS mask 渐变边框：渐变填充仅渲染在边框区域。
 */
declare function buildFrameRoundRectPath(outerW: number, outerH: number, outerRadius: BorderRadiusPt, bwTopPt: number, bwRightPt: number, bwBottomPt: number, bwLeftPt: number): string;
type RepeatingLinearGradientShapeOptions = {
    backgroundImage?: string;
    backgroundColor?: string;
    backgroundPosition?: string;
    rect?: {
        left: number;
        top: number;
        width: number;
        height: number;
    };
    rotate?: number;
    borderRadius?: BorderRadiusPt;
    opacity?: number;
};
/**
 * 将 repeating-linear-gradient 拆成条纹形状。
 * 支持水平/垂直方向的矩形条纹和任意角度的多边形条纹。
 * 支持多层 repeating-linear-gradient（逗号分隔的多背景层）。
 *
 * 多层 + opacity < 1 时，将 opacity 预混合到条纹颜色中：
 * CSS 中 opacity 对整个元素的合成结果统一生效，上层条纹不透明地遮挡下层；
 * PPT 无法对一组独立形状统一设置透明度，因此通过将颜色与底层背景色
 * 按 alpha compositing 预混合来模拟该效果，每个条纹设为不透明。
 */
declare function resolveRepeatingLinearGradientShapes(element: Element, ctx: ResolveContext, options?: RepeatingLinearGradientShapeOptions): PPTShapeElement[] | null;
/**
 * 判断元素是否应被识别为形状
 * @param element DOM 元素
 * @returns 是否为形状元素
 */
declare function isShapeElement(element: Element): boolean;
/**
 * 解析形状元素为 PPTShapeElement
 * @param element 形状 DOM 元素
 * @param ctx 解析上下文
 * @returns PPT 形状元素，无法解析时返回 null
 */
declare function resolveShapeElement(element: Element, ctx: ResolveContext): PPTShapeElement | null;
/**
 * 解析 CSS outline 为无填充描边形状
 * @param element DOM 元素
 * @param ctx 解析上下文
 * @returns PPT 形状元素，无 outline 时返回 null
 */
declare function resolveCssOutline(element: Element, ctx: ResolveContext): PPTShapeElement | null;
/**
 * 检测 border-image 渐变，为每条有宽度的边生成渐变填充矩形。
 * PPT 线条不支持渐变色，需用矩形 shape 模拟。
 */
declare function resolveBorderImageGradientShapes(element: Element, ctx: ResolveContext): PPTShapeElement[];
/**
 * 将多边可见边框拆分为独立的填充形状（2~3 条边时生效）
 * @param element DOM 元素
 * @param ctx 解析上下文
 * @returns PPT 形状元素数组
 */
declare function resolveMultiBorderShapes(element: Element, ctx: ResolveContext): PPTShapeElement[];
/**
 * 将单边（left/right/top/bottom）且带圆角的边框转换为填充形状。
 * 目的：保留边框端点与容器圆角一致的视觉效果。
 * @param element DOM 元素
 * @param ctx 解析上下文
 * @returns PPT 形状元素，不满足条件时返回 null
 */
declare function resolveRoundedSideBorderShape(element: Element, ctx: ResolveContext): PPTShapeElement | null;
/**
 * 将 outline-rect 的突出边框复用为带圆角端点的填充形状。
 */
declare function resolveRoundedBorderShapeForEdge(element: Element, border: BorderEdgeDetail, ctx: ResolveContext): PPTShapeElement | null;
/**
 * 将主元素的 CSS border 三角形/梯形解析为填充 shape。
 * 每条可见边框对应一个梯形区域（content 0×0 时退化为三角形），
 * 同色时合并为凸包多边形。
 * @param element DOM 元素
 * @param ctx 解析上下文
 * @returns 形状数组
 */
declare function resolveBorderTriangleShapes(element: Element, ctx: ResolveContext): PPTShapeElement[];
/**
 * 解析真实 DOM 元素 box-shadow 中的零模糊零扩展阴影为克隆形状。
 * 仅当有 >=2 个克隆阴影时才生成克隆形状（多点图案场景），
 * 单个克隆阴影由 PPT 原生阴影属性处理即可。
 */
declare function resolveBoxShadowClones(element: Element, ctx: ResolveContext): PPTShapeElement[];
/** 单侧边框描述 */
interface BorderSideSpec {
    width: number;
    style: string;
    color: string;
}
/**
 * 为非均匀边框生成独立的矢量形状，
 * 同时适用于真实 DOM 元素和伪元素。
 *
 * 椭圆 → 半弧 shape；圆角矩形 → 圆角路径 shape；无圆角 → 直线 line
 */
declare function buildIndividualBorderShapes(borders: {
    top: BorderSideSpec;
    right: BorderSideSpec;
    bottom: BorderSideSpec;
    left: BorderSideSpec;
}, leftPx: number, topPx: number, widthPx: number, heightPx: number, isEllipse: boolean, rotate: number, opacity: number | undefined, ownerDoc: Document, ctx: ResolveContext, borderRadius?: BorderRadiusPt | null): PPTElement[];
/**
 * 生成单侧边框的圆角矩形路径（含相邻两角的 quarter-arc）。
 * 顺时针方向绘制：起始角弧 → 直线段 → 结束角弧。
 */
declare function buildRoundedEdgePath(edge: "top" | "right" | "bottom" | "left", w: number, h: number, tl: number, tr: number, br: number, bl: number): string;
/**
 * 解析真实 DOM 元素上非均匀、带圆角的边框为矢量形状。
 * 椭圆 → 半弧；圆角矩形 → 圆角路径。
 *
 * 当 resolveRoundedSideBorderShape 无法处理（如 dashed 边框）时使用。
 */
declare function resolveRoundedBorderShapes(element: Element, ctx: ResolveContext): PPTElement[];
/**
 * 对边框元素列表应用元素自身的 CSS clip-path 裁剪。
 * 线条保留类型和样式属性，仅缩短为与 clip-path 的交集线段；
 * 形状通过多边形求交裁剪。
 */
declare function clipBorderElementsByClipPath(borderElements: PPTElement[], element: Element, ctx: ResolveContext): PPTElement[];
export { isShapeElement, resolveShapeElement, resolveRepeatingLinearGradientShapes, resolveBoxShadowClones, resolveCssOutline, resolveMultiBorderShapes, resolveBorderImageGradientShapes, resolveRoundedSideBorderShape, resolveRoundedBorderShapeForEdge, resolveBorderTriangleShapes, buildRoundRectPath, buildFrameRoundRectPath, buildIndividualBorderShapes, resolveRoundedBorderShapes, clipBorderElementsByClipPath, buildRoundedEdgePath, parseClipPathPolygon, };
export type { BorderSideSpec };
