/**
 * HTML 解析器内部类型定义
 */
export type { RgbColor } from '../shared/colorUtils';
/** 根容器的位置与尺寸（像素），用于计算子元素的相对坐标 */
interface RootRect {
    left: number;
    top: number;
    width: number;
    height: number;
}
/** PPT 线条虚线类型 */
type StrokeDashType = "solid" | "dash" | "dashDot" | "lgDash" | "lgDashDot" | "lgDashDotDot" | "sysDash" | "sysDot" | "double";
/** 边框方向 */
type BorderDirection = "top" | "bottom" | "left" | "right";
/** 四角圆角半径（pt 单位） */
interface BorderRadiusPt {
    topLeft: number;
    topRight: number;
    bottomRight: number;
    bottomLeft: number;
    /** 椭圆圆角时各角的水平/垂直半径（仅 rx≠ry 时填充） */
    topLeftX?: number;
    topLeftY?: number;
    topRightX?: number;
    topRightY?: number;
    bottomRightX?: number;
    bottomRightY?: number;
    bottomLeftX?: number;
    bottomLeftY?: number;
}
/** 解析上下文，贯穿整个 DOM 递归过程 */
interface ResolveContext {
    /** 根容器位置信息 */
    rootRect: RootRect;
    /** 生成唯一元素 ID */
    generateId: () => string;
    /** 当前层级继承的 CSS z-index 值 */
    currentZIndex: number;
    stackingBase: number;
    stackingSize: number;
    /** 当前是否处于显式 z-index 创建的层叠上下文内部 */
    inStackingContext?: boolean;
}
export type { RootRect, StrokeDashType, BorderDirection, BorderRadiusPt, ResolveContext, };
