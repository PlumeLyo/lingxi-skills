import { PPTLineElement } from '../../types/slides';
import { ResolveContext } from './types';
import { BorderEdgeDetail } from './borderUtils';
/**
 * 判断元素是否应解析为线条
 * 线条的典型特征：单边边框、<hr> 标签、极细的矩形（宽或高 <= 6px）
 * @param element 待检测的 DOM 元素
 * @returns 是否为线条元素
 */
declare function isLineElement(element: Element): boolean;
/**
 * 从单边边框信息解析线条
 * @param element 带单边边框的 DOM 元素
 * @param ctx 解析上下文
 * @returns PPTLineElement 或 null（非单边线条时）
 */
declare function resolveBorderLine(element: Element, ctx: ResolveContext): PPTLineElement | null;
/**
 * 解析线条元素（统一入口，按类型分发到具体解析器）
 * @param element 待解析的 DOM 元素
 * @param ctx 解析上下文
 * @returns PPTLineElement 或 null（不可解析时）
 */
declare function resolveLineElement(element: Element, ctx: ResolveContext): PPTLineElement | null;
/**
 * 为四边不均匀边框中的"突出"边生成线条
 * 用于 outline-rect 主体边框之外的差异边（如 border-t-[4px] border-t-[#1A508B]）
 * @param element 带不均匀边框的 DOM 元素
 * @param accentEdges 突出边的详情数组
 * @param ctx 解析上下文
 * @returns PPTLineElement 数组
 */
declare function resolveAccentBorderLines(element: Element, accentEdges: BorderEdgeDetail[], ctx: ResolveContext): PPTLineElement[];
/**
 * 将每条可见边框各自转换为一条 PPTLineElement（容器 fallback）。
 * 用于 2~3 条可见边框且元素含子节点导致 resolveMultiBorderShapes 不可用的情况。
 */
declare function resolveVisibleBorderLines(element: Element, ctx: ResolveContext): PPTLineElement[];
export { isLineElement, resolveBorderLine, resolveLineElement, resolveAccentBorderLines, resolveVisibleBorderLines, };
