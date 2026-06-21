import { PPTElement } from '../../types/slides';
import { ResolveContext } from './types';
/** 元素解析过程中的状态（当前标签名等） */
type ElementResolveState = {
    tagLower: string;
};
/**
 * 判断标签是否为直接图片类标签（img/canvas/svg/video/picture）
 * @param tagLower 小写标签名
 * @returns 是否为直接图片类标签
 */
declare function isDirectImageTag(tagLower: string): boolean;
/**
 * 按优先级队列依次尝试解析终端元素
 * @param element DOM 元素
 * @param ctx 解析上下文
 * @param results PPT 元素结果数组
 * @param state 元素解析状态（含标签名）
 * @returns 是否有解析器成功消费该元素
 */
declare function resolveTerminalElementByPriority(element: Element, ctx: ResolveContext, results: PPTElement[], state: ElementResolveState): Promise<boolean>;
/**
 * 解析单个终端元素（便捷入口，返回第一个匹配结果）
 * @param element DOM 元素
 * @param ctx 解析上下文
 * @returns 第一个匹配的 PPT 元素或 null
 */
declare function resolveSingleTerminalElement(element: Element, ctx: ResolveContext): Promise<PPTElement | null>;
/**
 * 追加容器元素的附属产物（背景图、边框线条、CSS outline、伪元素装饰）
 * @param element DOM 元素
 * @param ctx 解析上下文
 * @param results PPT 元素结果数组
 */
declare function appendElementArtifacts(element: Element, ctx: ResolveContext, results: PPTElement[]): Promise<void>;
export type { ElementResolveState };
export { isDirectImageTag, resolveTerminalElementByPriority, resolveSingleTerminalElement, appendElementArtifacts, };
