import { PPTLatexElement } from '../../types/slides';
import { ResolveContext } from './types';
/**
 * 判断元素是否是 LaTeX 公式元素
 * 支持检测 MathJax、KaTeX 等常见公式渲染库
 * @param element 待检测的 DOM 元素
 * @returns 是否为 LaTeX 公式元素
 */
declare function isLatexElement(element: Element): boolean;
/**
 * 解析 LaTeX 公式元素为 PPTLatexElement 结构
 * @param element 待解析的 DOM 元素
 * @param ctx 解析上下文（含根元素边界、ID 生成器等）
 * @returns PPTLatexElement 或 null（无有效 LaTeX 源码时）
 */
declare function resolveLatexElement(element: Element, ctx: ResolveContext): PPTLatexElement | null;
export { isLatexElement, resolveLatexElement };
