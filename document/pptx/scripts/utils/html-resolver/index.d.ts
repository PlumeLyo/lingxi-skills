import { PPTElement, Gradient } from '../../types/slides';
import { RootRect } from './types';
/** HTML 解析结果 */
interface ResolveResult {
    elements: PPTElement[];
    rootWidthPt: number;
    rootHeightPt: number;
    /** 幻灯片背景：纯色 HEX 字符串或 Gradient 渐变对象 */
    background?: string | Gradient;
}
/**
 * 解析整个 DOM 根元素，返回 PPT 元素数组、根尺寸和背景色
 * @param root 根 DOM 元素
 * @returns 解析结果（元素数组、根尺寸、背景色）
 */
declare function resolveHtml(root: Element): Promise<ResolveResult>;
/**
 * 解析单个 DOM 元素为 PPT 元素
 * @param element 待解析的 DOM 元素
 * @param rootRect 根元素矩形信息
 * @returns 解析后的 PPT 元素，无法解析则返回 null
 */
declare function resolveSingleElement(element: Element, rootRect: RootRect): Promise<PPTElement | null>;
export type { ResolveResult };
export { resolveHtml, resolveSingleElement };
