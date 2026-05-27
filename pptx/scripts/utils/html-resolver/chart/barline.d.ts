import { PPTChartElement } from '../../../types/slides';
import { EChartsOption, EChartsOptionSeries, EChartsInstance } from './types';
import { ResolveContext } from '../types';
declare function resolveBarLineChart(element: Element, ctx: ResolveContext, option: EChartsOption, effectiveSeries: EChartsOptionSeries[], instance: EChartsInstance): PPTChartElement | null;
export { resolveBarLineChart };
