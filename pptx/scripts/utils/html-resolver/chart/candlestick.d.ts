import { PPTChartElement } from '../../../types/slides';
import { EChartsOption, EChartsOptionSeries, EChartsInstance } from './types';
import { ResolveContext } from '../types';
/**
 * K 线图独立解析路径，含叠加均线（line）和成交量（bar）系列。
 * @param element - ECharts 容器 DOM 元素
 * @param ctx - 解析上下文（含 rootRect、generateId 等）
 * @param option - ECharts getOption() 返回值
 * @param effectiveSeries - 有数据的系列数组
 * @param instance - ECharts 实例
 * @returns PPTChartElement 或 null（无有效数据或尺寸无效时）
 */
declare function resolveCandlestickChart(element: Element, ctx: ResolveContext, option: EChartsOption, effectiveSeries: EChartsOptionSeries[], instance: EChartsInstance): PPTChartElement | null;
export { resolveCandlestickChart };
