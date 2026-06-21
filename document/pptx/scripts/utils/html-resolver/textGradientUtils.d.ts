import { Gradient } from '../../types/slides';
/**
 * 判断元素是否使用了 CSS 渐变文本效果
 * （background: gradient + background-clip: text + text-fill-color: transparent）
 */
declare function isGradientTextElement(element: Element): boolean;
/**
 * 从使用渐变文本效果的元素中提取渐变信息
 */
declare function resolveTextGradient(element: Element): Gradient | undefined;
export { isGradientTextElement, resolveTextGradient };
