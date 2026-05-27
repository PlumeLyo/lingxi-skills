import { PPTChartElement } from '../../types/slides';
import { ResolveContext } from './types';
declare function isEChartsContainer(element: Element): boolean;
declare function resolveChartElement(element: Element, ctx: ResolveContext): PPTChartElement | null;
export { isEChartsContainer, resolveChartElement };
