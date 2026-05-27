import { PPTChartElement, ScatterDataPoint } from '../../../types/slides';
import { EChartsOption, EChartsOptionSeries, EChartsInstance } from './types';
import { ResolveContext } from '../types';
/**
 * 从 ECharts scatter series data 中提取 [x, y] 数据点对。
 * @param data - scatter 系列的 data 配置
 * @returns 合法的 [x, y] 点对列表
 */
declare function extractScatterDataPoints(data: EChartsOptionSeries["data"]): ScatterDataPoint[];
/**
 * 散点图独立解析路径，生成双数值轴 + scatter 系列的 PPTChartElement。
 * @param element - ECharts 容器 DOM 元素
 * @param ctx - 解析上下文（含 rootRect、generateId 等）
 * @param option - ECharts getOption() 返回值
 * @param effectiveSeries - 有数据的系列数组
 * @param instance - ECharts 实例
 * @returns PPTChartElement 或 null（无散点数据或尺寸无效时）
 */
declare function resolveScatterChart(element: Element, ctx: ResolveContext, option: EChartsOption, effectiveSeries: EChartsOptionSeries[], instance: EChartsInstance): PPTChartElement | null;
export { extractScatterDataPoints, resolveScatterChart };
