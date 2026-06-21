import { PPTImageElement } from '../../types/slides';
import { ResolveContext } from './types';
declare const DIRECT_IMAGE_TAGS: Set<string>;
/**
 * 判断元素是否是图片类型
 * @param element 待判断的 DOM 元素
 * @returns 是否为图片类型（img/canvas/svg/video/picture 或含 background-image）
 */
declare function isImageElement(element: Element): boolean;
/**
 * 解析图片元素
 * @param element 待解析的 DOM 元素
 * @param ctx 解析上下文
 * @returns 解析后的 PPT 图片元素，若无法解析则返回 null
 */
declare function resolveImageElement(element: Element, ctx: ResolveContext): Promise<PPTImageElement | null>;
/**
 * 判断元素是否部分溢出根容器（完全在内或完全在外均返回 false）
 * @param element 待判断的 DOM 元素
 * @param ctx 解析上下文（含根容器矩形）
 * @returns 是否部分溢出根容器
 */
declare function isOverflowElement(element: Element, ctx: ResolveContext): boolean;
/**
 * 将部分溢出根容器的元素截取可见区域像素，返回裁剪后的 image 元素。
 * 调用前需先通过 isOverflowElement 确认元素确实溢出。
 * @param element 溢出的 DOM 元素
 * @param ctx 解析上下文
 * @returns 裁剪后的 PPT 图片元素，若截取失败则返回 null
 */
declare function resolveOverflowElement(element: Element, ctx: ResolveContext): Promise<PPTImageElement | null>;
export { DIRECT_IMAGE_TAGS, isImageElement, resolveImageElement, isOverflowElement, resolveOverflowElement, };
