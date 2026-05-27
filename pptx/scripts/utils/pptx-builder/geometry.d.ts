import { PPTLineElement } from '../../types/slides';
/**
 * 磅值转英寸
 * @param pt 磅值
 * @returns 对应的英寸值
 */
declare function ptToInch(pt: number): number;
/** 矩形元素的 pt 坐标结构 */
type ElementRect = {
    left: number;
    top: number;
    width: number;
    height: number;
};
/** 幻灯片使用的英寸坐标边界 */
interface InchBounds {
    x: number;
    y: number;
    w: number;
    h: number;
}
/**
 * 将 pt 矩形转为英寸边界
 * @param element 含 left/top/width/height 的矩形元素
 * @returns 幻灯片使用的英寸坐标边界 { x, y, w, h }
 */
declare function toInchBounds(element: ElementRect): InchBounds;
/** 线条的英寸坐标边界（含起止点） */
interface LineFrameInch extends InchBounds {
    startX: number;
    startY: number;
    endX: number;
    endY: number;
    flipH: boolean;
    flipV: boolean;
}
type LineGeometry = Pick<PPTLineElement, "left" | "top" | "start" | "end">;
/**
 * 将线条的 pt 起止坐标转为英寸坐标框架
 * @param line 含 left/top/start/end 的线条几何数据
 * @returns 含起止点及外框的英寸坐标框架
 */
declare function toLineFrameInch(line: LineGeometry): LineFrameInch;
/**
 * 将 CSS opacity（0~1）转为 transparency（0~100），完全不透明时返回 undefined
 * @param opacity CSS 不透明度，0~1
 * @returns transparency 0~100，完全不透明时返回 undefined
 */
declare function opacityToTransparency(opacity: number | undefined): number | undefined;
export type { InchBounds, LineFrameInch };
export { ptToInch, toInchBounds, toLineFrameInch, opacityToTransparency };
