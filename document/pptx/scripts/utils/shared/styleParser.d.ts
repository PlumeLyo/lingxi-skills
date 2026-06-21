import { PPTElementShadow, ImageElementClip } from '../../types/slides';
/**
 * 从 CSS transform 字符串中提取旋转角度（支持 rotate() 和 matrix() 格式）
 */
declare function parseRotateFromTransform(transform: string): number;
/**
 * 从 CSS transform 字符串中提取水平/垂直翻转信息（scale/scaleX/scaleY）
 */
declare function parseFlipFromTransform(transform: string): {
    flipH: boolean;
    flipV: boolean;
};
/**
 * 从 CSS box-shadow 中解析单层阴影（仅处理第一个阴影）
 */
declare function parseBoxShadowToElementShadow(boxShadow: string): PPTElementShadow | undefined;
/**
 * 获取元素的原始尺寸（未旋转），用于有 transform rotate 的元素
 */
declare function getOriginalSize(element: Element, rotateDeg: number): {
    width: number;
    height: number;
};
declare function parseTransformComponents(transform: string): {
    translateX: number;
    translateY: number;
    scaleX: number;
    scaleY: number;
};
/**
 * 解析单个 CSS position 分量为 0~1 比例值。
 * 支持关键词（center/left/right/top/bottom）、百分比、px。
 */
declare function parsePositionRatio(value: string, containerSizePx: number): number;
interface BgFitResult {
    clip: ImageElementClip | null;
    leftPx: number;
    topPx: number;
    widthPx: number;
    heightPx: number;
}
/**
 * 根据 background-size (cover/contain) 和 background-position 计算
 * 背景图的裁剪区域或偏移，逻辑与 resolveImage 中 computeObjectFitAdjustment 对齐。
 */
declare function computeBgFitAdjustment(naturalW: number, naturalH: number, containerW: number, containerH: number, bgSize: string, bgPosition: string): BgFitResult | null;
/**
 * 解析 CSS transform-origin 为相对于元素左上角的 px 偏移。
 * 支持关键词（left/center/right/top/bottom）、百分比、px 值。
 * @param value transform-origin 计算值，如 "50% 50%"、"0px 0px"、"right top"
 * @param width 元素宽度 (px)
 * @param height 元素高度 (px)
 */
declare function parseTransformOrigin(value: string | undefined, width: number, height: number): {
    x: number;
    y: number;
};
/**
 * 当元素使用非中心 transform-origin 旋转时，计算等效于
 * 围绕中心旋转后所需的位置补偿 (delta left, delta top)。
 *
 * 原理：CSS 旋转围绕 origin 执行，PPT 旋转围绕中心执行。
 * 将元素中心围绕 origin 旋转得到新的中心位置，
 * 再减去 PPT 围绕中心旋转后的中心位置（不变），即为补偿量。
 */
declare function computeTransformOriginOffset(originX: number, originY: number, width: number, height: number, rotateDeg: number): {
    dx: number;
    dy: number;
};
export type { BgFitResult };
export { parseRotateFromTransform, parseFlipFromTransform, parseBoxShadowToElementShadow, getOriginalSize, parseTransformComponents, parsePositionRatio, computeBgFitAdjustment, parseTransformOrigin, computeTransformOriginOffset, };
