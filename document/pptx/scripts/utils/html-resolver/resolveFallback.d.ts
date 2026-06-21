import { PPTElement, PPTImageElement } from '../../types/slides';
import { ResolveContext } from './types';
/**
 * 解析含椭圆圆角的元素（截图降级）
 * 有纯色/渐变背景的元素跳过截图，交给 resolveShapeElement 用近似圆角矢量化处理。
 * @param element 待解析的 DOM 元素
 * @param ctx 解析上下文
 * @returns 截图后的 PPT 图片元素，若无法解析则返回 null
 */
declare function resolveIrregularBorderRadius(element: Element, ctx: ResolveContext): Promise<PPTImageElement | null>;
/**
 * 解析含斜切变换的元素
 * 简单纯色元素优先转为原生旋转矩形，否则截图降级
 */
declare function resolveSkewElement(element: Element, ctx: ResolveContext): Promise<PPTElement | null>;
export { resolveIrregularBorderRadius, resolveSkewElement };
