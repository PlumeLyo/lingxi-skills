import { PPTElement } from '../../types/slides';
import { ResolveContext } from './types';
/**
 * 解析 box-shadow 中用于"克隆"元素的无模糊/无扩展阴影，
 * 每个这样的 shadow 值生成一个与主体形状相同大小/圆角的副本 shape。
 */
declare function parseBoxShadowClones(boxShadow: string, basePxLeft: number, basePxTop: number, widthPx: number, heightPx: number, defaultFill: string, radiusInfo: {
    shapeType?: "ellipse" | "roundRect";
    keypoints?: number[];
}, rotate: number, ctx: ResolveContext): PPTElement[];
export { parseBoxShadowClones };
