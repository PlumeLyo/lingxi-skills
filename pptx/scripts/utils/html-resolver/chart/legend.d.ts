import { EChartsLegend, LegendPos } from './types';
/**
 * 判断图例是否应该显示。
 * - show 显式 false → 不显示
 * - show 显式 true → 始终显示
 * - show 未设置：饼图显示；单系列非饼图不显示
 * @param legend - ECharts legend 配置（可为数组）
 * @param seriesCount - 系列数量
 * @param isPie - 是否为饼图
 * @returns 是否显示图例
 */
declare function isLegendVisible(legend: EChartsLegend | EChartsLegend[] | undefined, seriesCount: number, isPie?: boolean): boolean;
/**
 * 解析图例位置 → OOXML 方位（t/b/l/r），默认底部
 * @param legend - ECharts legend 配置（可为数组）
 * @returns OOXML 图例方位
 */
declare function resolveLegendPosition(legend: EChartsLegend | EChartsLegend[] | undefined): LegendPos;
/**
 * 提取图例字号（px → OOXML 百分之一磅）
 * @param legend - ECharts legend 配置（可为数组）
 * @returns 百分之一磅字号，未设置时 undefined
 */
declare function resolveLegendFontSize(legend: EChartsLegend | EChartsLegend[] | undefined): number | undefined;
/**
 * 提取图例文本颜色
 * @param legend - ECharts legend 配置（可为数组）
 * @returns 颜色字符串，未设置时 undefined
 */
declare function resolveLegendFontColor(legend: EChartsLegend | EChartsLegend[] | undefined): string | undefined;
export { isLegendVisible, resolveLegendPosition, resolveLegendFontSize, resolveLegendFontColor, };
