import { BorderDirection, RgbColor, StrokeDashType } from './types';
/**
 * 判断某条边框是否可见（有宽度且非透明）
 * @param widthPx 边框宽度（像素）
 * @param color 边框颜色
 * @returns 是否可见
 */
declare function isBorderSideVisible(widthPx: number, color: string | null): boolean;
/**
 * 将 CSS border-style 映射为 PPT 线条虚线类型
 * @param borderStyle CSS 边框样式
 * @returns PPT 线条虚线类型
 */
declare function getDashType(borderStyle: string | null | undefined): StrokeDashType;
/** 单边边框的详细信息 */
interface BorderEdgeDetail {
    edge: BorderDirection;
    color: RgbColor;
    widthPt: number;
    dashType: StrokeDashType;
}
/** 元素边框形状分析结果 */
interface BorderShapeInfo {
    shapeKind: "line" | "outline-rect";
    strokeColor: RgbColor;
    strokeWidthPt: number;
    lineDirection?: "horizontal" | "vertical";
    lineEdge?: BorderDirection;
    strokeDashType: StrokeDashType;
    /** 四边不均匀时，与主体不同的突出边框列表 */
    accentEdges?: BorderEdgeDetail[];
}
/**
 * 获取元素边框形状信息（单边返回 line，四边相同返回 outline-rect）
 * @param element DOM 元素
 * @returns 边框形状信息，无可见边框则返回 null
 */
declare function getBorderShapeInfo(element: Element): BorderShapeInfo | null;
/**
 * 获取元素所有可见边框信息（用于将多边边框拆分为多条线条）
 * @param element DOM 元素
 * @returns 可见边框的形状信息数组
 */
declare function getVisibleBorders(element: Element): BorderShapeInfo[];
/**
 * 检测主元素是否使用了 CSS border 三角形/梯形技巧
 * （content 尺寸为 0×0，同时存在可见边框和透明边框）
 * @param element DOM 元素
 * @returns 是否为三角形边框
 */
declare function isCssBorderTriangle(element: Element): boolean;
/**
 * 检测计算样式中是否存在渐变 border-image（会覆盖普通 border 的视觉渲染）。
 */
declare function hasBorderImageGradient(style: CSSStyleDeclaration): boolean;
export type { BorderEdgeDetail, BorderShapeInfo };
export { isBorderSideVisible, getDashType, getBorderShapeInfo, getVisibleBorders, isCssBorderTriangle, hasBorderImageGradient, };
