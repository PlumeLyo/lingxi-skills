import { PPTElement } from '../../types/slides';
import { RgbColor, ResolveContext } from './types';
interface BorderWidths {
    top: number;
    right: number;
    bottom: number;
    left: number;
}
interface BorderColors {
    top: RgbColor | null;
    right: RgbColor | null;
    bottom: RgbColor | null;
    left: RgbColor | null;
}
interface BorderTrapezoid {
    points: [number, number][];
    color: RgbColor;
}
declare function polygonBBox(points: [number, number][]): {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
};
/**
 * 将多边形顶点（px 坐标系）转换为 PPTElement shape
 */
declare function buildShapeFromPolygon(points: [number, number][], color: RgbColor, boxW: number, boxH: number, leftPx: number, topPx: number, ctx: ResolveContext): PPTElement;
/**
 * 完整管线：从边框参数 → PPTElement shape 数组
 *
 * 调用方只需准备边框宽度、内容尺寸、颜色和基准定位，
 * 本函数负责梯形生成、同色合并、异色分离和 shape 构建。
 */
declare function buildBorderTrapezoidShapes(bw: BorderWidths, contentW: number, contentH: number, colors: BorderColors, baseLeftPx: number, baseTopPx: number, ctx: ResolveContext): PPTElement[];
export type { BorderWidths, BorderColors, BorderTrapezoid };
export { buildBorderTrapezoidShapes, buildShapeFromPolygon, polygonBBox };
