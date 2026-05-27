import { PPTElement } from '../../types/slides';
import { ResolveContext } from './types';
/**
 * 尝试将伪元素图标解析为矢量 PPTShapeElement。
 * 成功时返回 shape，字体不可用或字形未找到时返回 null（调用方回退到截图）。
 */
declare function resolvePseudoIconAsShape(element: Element, ctx: ResolveContext): Promise<PPTElement | null>;
export { resolvePseudoIconAsShape };
