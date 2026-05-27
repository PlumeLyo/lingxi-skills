import { PPTElement } from '../../types/slides';
import { ResolveContext } from './types';
/**
 * 判断元素是否是仅由伪元素渲染的图标（无文本、无子元素）
 * @param element DOM 元素
 * @returns 是否为伪元素图标
 */
declare function isPseudoIconElement(element: Element): boolean;
/**
 * 解析伪元素图标为图片
 * 沿祖先链累积 opacity 和 rotate，截图为 image 元素。
 * 对绝对定位伪元素，通过临时 DOM 元素修正位置。
 * @param element 伪元素图标 DOM 元素
 * @param ctx 解析上下文
 * @returns PPT 元素（图片），无法解析时返回 null
 */
declare function resolvePseudoIcon(element: Element, ctx: ResolveContext): Promise<PPTElement | null>;
/**
 * 解析元素的 ::before / ::after 伪元素装饰为 shape 数组
 * 处理伪元素的绝对定位偏移和旋转变换，
 * 当伪元素 position:absolute 时，基于其实际 containing block 计算位置，
 * 而非一定基于元素自身（元素可能没有 position 属性）。
 * 当 containing block 有旋转时，在本地坐标系中计算偏移后再旋转到全局坐标。
 * @param element DOM 元素
 * @param ctx 解析上下文
 * @returns PPT 元素数组
 */
declare function resolvePseudoDecorations(element: Element, ctx: ResolveContext): Promise<PPTElement[]>;
/**
 * 将列表小圆点解析为矢量 shape，避免转成 image。
 * 处理两种来源：
 *  1. ::before/::after content 中的 bullet 字符（●、•、○ 等）
 *  2. 原生 list-style-type（disc/circle/square）渲染的 ::marker 伪元素
 * @param element 列表项 DOM 元素
 * @param ctx 解析上下文
 * @returns PPT 形状元素数组
 */
declare function resolvePseudoBulletShapes(element: Element, ctx: ResolveContext): PPTElement[];
/**
 * 判断元素是否是伪元素图标的行内包装器。
 * 典型场景：`<span class="icon-box"><i class="fas fa-xxx"></i></span>`，
 * 外层 span 本身不是伪元素图标，但唯一可见子元素是一个伪元素图标。
 * @param element DOM 元素
 * @returns 是否为伪元素图标的行内包装器
 */
declare function isWrappedPseudoIconElement(element: Element): boolean;
/**
 * 从包装器元素中提取最内层的伪元素图标元素。
 * @param element DOM 元素
 * @returns 最内层的伪元素图标元素
 */
declare function unwrapPseudoIconElement(element: Element): Element | null;
export { isPseudoIconElement, isWrappedPseudoIconElement, unwrapPseudoIconElement, resolvePseudoIcon, resolvePseudoDecorations, resolvePseudoBulletShapes, };
