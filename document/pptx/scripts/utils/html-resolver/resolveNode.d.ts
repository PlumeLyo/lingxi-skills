import { PPTElement } from '../../types/slides';
import { ResolveContext } from './types';
export { isDirectImageTag } from './resolveNodeTerminal';
/**
 * 递归解析 DOM 节点，将识别到的 PPT 元素推入 results
 * @param node 待解析的 DOM 子节点
 * @param ctx 解析上下文（含根元素边界、ID 生成器等）
 * @param results PPT 元素结果数组（解析结果会被追加到此数组）
 */
declare function resolveNode(node: ChildNode, ctx: ResolveContext, results: PPTElement[]): Promise<void>;
export { resolveNode };
