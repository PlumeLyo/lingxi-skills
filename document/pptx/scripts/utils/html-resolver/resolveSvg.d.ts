import { PPTElement } from '../../types/slides';
import { ResolveContext } from './types';
/**
 * 判断 SVG 是否包含可解析为矢量的可视子元素（含 text）
 */
declare function isSvgWithVisualChildren(element: Element): boolean;
/**
 * 将 <svg> 内部的可视子元素解析为 PPT 矢量元素数组。
 * 返回空数组表示无法矢量化（调用方应回退到栅格化）。
 */
declare function resolveSvgElement(element: Element, ctx: ResolveContext): PPTElement[];
export { isSvgWithVisualChildren, resolveSvgElement };
