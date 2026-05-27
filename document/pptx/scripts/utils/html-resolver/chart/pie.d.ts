import { PPTChartElement, ChartSeries, ChartCenterText } from '../../../types/slides';
import { EChartsOption, EChartsOptionSeries, EChartsInstance } from './types';
import { ResolveContext } from '../types';
/**
 * 从饼图 series.data 中提取类别名称数组。
 * @param data - ECharts series 的 data 数组
 * @returns 类别名称数组
 */
declare function extractPieCategories(data: EChartsOptionSeries["data"]): string[];
/**
 * 从饼图 series.radius 提取内孔百分比（用于圆环图）。
 * radius: ['40%', '70%'] → holeSize = round(40/70*100) ≈ 57
 * @param seriesList - ECharts 系列数组
 * @returns 圆环内孔相对外缘的百分比；无法解析时返回 undefined
 */
declare function extractPieHoleSize(seriesList: EChartsOptionSeries[]): number | undefined;
/**
 * 从单个 pie series 的 radius 计算 holeSize。
 * @param series - pie 类型的 ECharts series
 * @returns 内孔相对外圆的百分比（1–90）；不符合条件时返回 undefined
 */
declare function computeSeriesHoleSize(series: EChartsOptionSeries): number | undefined;
/**
 * 将 ECharts startAngle 转为 OOXML 兼容的首扇区角度。
 * @param seriesList - ECharts 系列数组
 * @returns 首扇区角度（度）；为默认值或未设置时返回 undefined
 */
declare function extractFirstSliceAng(seriesList: EChartsOptionSeries[]): number | undefined;
/**
 * 从饼图 labelLine 配置中提取引线颜色和不透明度。
 * @param isPie - 是否为饼图类型
 * @param seriesList - ECharts 系列数组
 * @returns 引线颜色与不透明度字段（可能为空对象）
 */
declare function extractLabelLineStyle(isPie: boolean, seriesList: EChartsOptionSeries[]): {
    labelLineColor?: string;
    labelLineOpacity?: number;
};
/**
 * 从饼图 series.itemStyle 提取扇区边框（用于白色间隔效果）。
 * @param isPie - 是否为饼图类型
 * @param seriesList - ECharts 系列数组
 * @returns 扇区边框颜色与线宽（可能为空对象）
 */
declare function extractPieBorder(isPie: boolean, seriesList: EChartsOptionSeries[]): {
    borderColor?: string;
    borderWidth?: number;
};
/**
 * 解析饼图 label formatter，提取数据标签显示选项。
 * 支持 ECharts 模板变量：{b}=类别名, {c}=数值, {d}=百分比
 * @param formatter - 字符串、函数或未定义的标签 formatter
 * @returns 是否使用 formatter 及类别名/数值/百分比等开关与格式信息
 */
declare function parsePieLabelFormatter(formatter: string | Function | undefined): {
    hasFormatter: boolean;
    showCatName?: boolean;
    showVal?: boolean;
    showPercent?: boolean;
    separator?: string;
    numFmt?: string;
};
/**
 * 从饼图/圆环图的 position:'center' 标签中提取中心富文本。
 * 支持函数 formatter、字符串 formatter（含模板变量）、emphasis.label 回退。
 * @param series - pie 类型的 ECharts series
 * @returns 居中富文本结构；无法解析时返回 undefined
 */
declare function extractPieCenterText(series: EChartsOptionSeries): ChartCenterText | undefined;
/**
 * 对齐嵌套饼图（多 series）的类别和数据。
 * 合并各 series 独立类别为统一列表，缺失类别填充 0，颜色跨 series 保持一致。
 * @param series - ChartSeries 数组（就地写入对齐后的 data/pointStyles 等）
 * @param effectiveSeries - 与 series 逐项对应的 ECharts option series
 * @param palette - 调色板 HEX 颜色列表
 * @returns 合并后的全局类别名称有序列表
 */
declare function alignNestedPieSeries(series: ChartSeries[], effectiveSeries: EChartsOptionSeries[], palette: string[]): string[];
/**
 * 过滤单饼图中零值/空值数据点，保持 categories 与 series 对齐。
 * @param categories - 与首条 series 数据等长的类别名列表
 * @param series - ChartSeries 列表（就地筛除对应索引的点）
 * @returns 保留非零下标后的类别名列表
 */
declare function filterZeroPieData(categories: string[], series: ChartSeries[]): string[];
declare function resolvePieChart(element: Element, ctx: ResolveContext, option: EChartsOption, effectiveSeries: EChartsOptionSeries[], centerTextSeries: EChartsOptionSeries[], instance: EChartsInstance): PPTChartElement | null;
export { extractPieCategories, extractPieHoleSize, computeSeriesHoleSize, extractFirstSliceAng, extractLabelLineStyle, extractPieBorder, parsePieLabelFormatter, extractPieCenterText, alignNestedPieSeries, filterZeroPieData, resolvePieChart, };
