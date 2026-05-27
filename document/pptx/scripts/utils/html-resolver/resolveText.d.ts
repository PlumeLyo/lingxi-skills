import { PPTTextElement, PPTLineElement } from '../../types/slides';
import { ResolveContext } from './types';
/**
 * 判断元素是否是文本容器（包含可见文本内容）
 * @param element DOM 元素
 * @returns 是否为文本元素
 */
declare function isTextElement(element: Element): boolean;
/**
 * 从文本节点（Text）解析文本元素
 * @param textNode 文本节点
 * @param ctx 解析上下文
 * @returns PPT 文本元素，无法解析时返回 null
 */
declare function resolveTextFromNode(textNode: Text, ctx: ResolveContext): PPTTextElement | null;
/**
 * 从容器元素解析文本元素（提取富文本 innerHTML）
 * @param element 文本容器 DOM 元素
 * @param ctx 解析上下文
 * @returns PPT 文本元素，无法解析时返回 null
 */
declare function resolveTextFromElement(element: Element, ctx: ResolveContext, excludeElements?: Set<Element>): PPTTextElement | null;
/** 从 CSS box-shadow 值解析阴影参数 */
/**
 * 扫描文本容器中带 text-decoration: overline 的子元素，
 * 为每个 overline 区域生成一条水平线条元素。
 *
 * OOXML 不支持 overline 文本装饰，因此用独立线条叠加在文字上方模拟。
 */
declare function resolveOverlineLines(element: Element, ctx: ResolveContext): PPTLineElement[];
export { isTextElement, resolveTextFromNode, resolveTextFromElement, resolveOverlineLines };
