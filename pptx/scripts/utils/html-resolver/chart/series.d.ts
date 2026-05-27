import { ChartSeries, ChartAreaFill, ChartMarkLineLabel } from '../../../types/slides';
import { EChartsOptionSeries, SeriesConvertContext, MarkLineStyleInfo } from './types';
/**
 * 从 ECharts series data 中提取数值数组，保留 null。
 * @param data - ECharts series 的 data 字段
 * @returns 数值数组；无法解析的项为 null
 */
declare function extractSeriesValues(data: EChartsOptionSeries["data"]): (number | null)[];
/**
 * 从 markPoint 配置中解析需要标注的数据点索引（min/max）。
 * @param markPoint - ECharts series 的 markPoint 配置
 * @param data - 与系列数据对齐的数值数组
 * @returns 需标注的数据点索引列表
 */
declare function extractMarkPointIndices(markPoint: EChartsOptionSeries["markPoint"], data: (number | null)[]): number[];
/**
 * 从 ECharts areaStyle 提取面积填充配置（渐变/纯色）。
 * @param areaStyle - ECharts series 的 areaStyle 配置
 * @param seriesColor - 无显式颜色时的系列颜色兜底
 * @returns 面积填充配置；无填充时返回 undefined
 */
declare function extractAreaFill(areaStyle: EChartsOptionSeries["areaStyle"], seriesColor: string | undefined): ChartAreaFill | undefined;
/**
 * 将单个 ECharts 系列转换为 ChartSeries。
 * 解析系列颜色（含 CSS 变量、渐变、函数）、构建数据点样式、
 * 数据标签配置、折线图样式。
 * @param s - 单个 ECharts 系列配置
 * @param idx - 系列在图表中的序号
 * @param ctx - DOM、调色板等转换上下文
 * @returns 对应的 ChartSeries 结构
 */
declare function convertEChartsSeries(s: EChartsOptionSeries, idx: number, ctx: SeriesConvertContext): ChartSeries;
/**
 * 反转系列数据以适配 inverse 类别轴。
 * 反转 data、pointStyles 数组顺序，并映射 dataLabel.indices 索引。
 * @param series - ChartSeries 数组（原地修改各系列的 data 等字段）
 * @returns 无返回值
 */
declare function reverseSeriesForInverse(series: ChartSeries[]): void;
/**
 * 从 ECharts markLine 配置中提取线样式信息。
 * @param markLine - ECharts series 的 markLine 配置
 * @returns 样式信息；markLine 无数据时返回 undefined
 */
declare function extractMarkLineStyle(markLine: EChartsOptionSeries["markLine"]): MarkLineStyleInfo | undefined;
/**
 * 从 markLine data item 及 series 级 markLine.label 中合并解析出 ChartMarkLineLabel。
 * @param markLine - ECharts series 的 markLine 配置（用于读取 series 级 label）
 * @param itemLabel - 单条参考线的 label 配置
 * @param value - 参考线的数值（用于替换 {c} 占位符）
 */
declare function resolveMarkLineLabel(markLine: EChartsOptionSeries["markLine"], itemLabel: {
    show?: boolean;
    position?: string;
    formatter?: string;
    color?: string;
    fontSize?: number;
    fontWeight?: string | number;
} | undefined, value: number): ChartMarkLineLabel | undefined;
export { extractSeriesValues, extractMarkPointIndices, extractAreaFill, convertEChartsSeries, reverseSeriesForInverse, extractMarkLineStyle, resolveMarkLineLabel, };
