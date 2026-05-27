import { EChartsOptionAxis, EChartsOptionSeries, EChartsGrid, EChartsOption, ComputeGapWidthOption } from './types';
/**
 * 计算类别轴标签的跳过间隔。
 * 显式 interval → 直接使用；auto → 根据标签文字宽度与轴可用像素估算。
 * 返回 OOXML tickLblSkip 值（>=2 才有意义）。
 * @param axis - 坐标轴配置（可为数组）
 * @param categories - 类别标签数组
 * @param chartWidthPx - 图表宽度（像素）
 * @returns tickLblSkip，无需或未算出时 undefined
 */
declare function computeCatLabelSkip(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined, categories: string[], chartWidthPx: number): number | undefined;
/**
 * 将 ECharts 边距值（number/px/%）转为 0~1 的比例值
 * @param value - 边距值
 * @param containerSize - 容器尺寸（像素）
 * @param fallbackRatio - 无法解析时的回退比例
 * @returns 0~1 比例值
 */
declare function parseMarginRatio(value: number | string | undefined, containerSize: number, fallbackRatio: number): number;
/**
 * 将 ECharts grid 配置转为 OOXML 绘图区域（0~1 相对坐标）
 * @param grid - grid 配置（可为数组）
 * @param chartWidth - 图表宽度（像素）
 * @param chartHeight - 图表高度（像素）
 * @param horizontalBarCategories - 水平柱图类别轴标签（可选，用于 containLabel）
 * @param catLabelFontSize - 类别标签字号（百分之一磅，可选）
 * @returns 绘图区矩形，无 grid 时 undefined
 */
declare function resolveGridToPlotArea(grid: EChartsGrid | EChartsGrid[] | undefined, chartWidth: number, chartHeight: number, horizontalBarCategories?: string[], catLabelFontSize?: number): {
    x: number;
    y: number;
    w: number;
    h: number;
} | undefined;
/**
 * 从 barWidth 配置计算 OOXML gapWidth。
 * barWidth 百分比 → gapWidth = (100 - w) / w × 100；
 * barWidth 像素 → 根据绘图区尺寸和类别数反推。
 * 无显式 barWidth 时返回默认值 50。
 * @param seriesList - 系列配置列表
 * @param option - 尺寸与 grid 等辅助参数
 * @returns gapWidth，无柱系列时 undefined
 */
declare function computeGapWidth(seriesList: EChartsOptionSeries[], option?: ComputeGapWidthOption): number | undefined;
/**
 * 从 barGap 配置计算 OOXML overlap 值。
 * ECharts barGap='30%' → OOXML overlap=-20（负值=间距，正值=重叠）。
 * 堆叠模式下固定返回 100（完全重叠）。
 * @param seriesList - 系列配置列表
 * @param isStacked - 是否为堆叠柱图
 * @returns overlap，无柱系列时 undefined
 */
declare function computeOverlap(seriesList: EChartsOptionSeries[], isStacked?: boolean): number | undefined;
/**
 * 判断是否为水平柱状图（yAxis 为 category 或 xAxis 为 value）
 * @param option - ECharts 图表配置
 * @returns 是否为水平柱状图
 */
declare function isHorizontalBarChart(option: EChartsOption): boolean;
export { computeCatLabelSkip, parseMarginRatio, resolveGridToPlotArea, computeGapWidth, computeOverlap, isHorizontalBarChart, };
