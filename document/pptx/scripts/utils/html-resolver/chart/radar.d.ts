import { PPTChartElement } from '../../../types/slides';
import { EChartsOption, EChartsOptionSeries, EChartsInstance } from './types';
import { ResolveContext } from '../types';
/**
 * 雷达图独立解析路径，生成 radar 类型的 PPTChartElement。
 * @param element - ECharts 容器 DOM 元素
 * @param ctx - 解析上下文（含 rootRect、generateId 等）
 * @param option - ECharts getOption() 返回值
 * @param effectiveSeries - 有数据的系列数组
 * @param instance - ECharts 实例
 * @returns PPTChartElement 或 null（无指示器或无有效系列时）
 */
declare function resolveRadarChart(element: Element, ctx: ResolveContext, option: EChartsOption, effectiveSeries: EChartsOptionSeries[], instance: EChartsInstance): PPTChartElement | null;
export { resolveRadarChart };
