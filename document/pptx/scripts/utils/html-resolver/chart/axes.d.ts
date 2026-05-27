import { ChartSeries, ChartValueAxis, ChartDataLabel } from '../../../types/slides';
import { EChartsOptionAxis, StackInfo } from './types';
/**
 * 计算合适的刻度间隔（对齐到 1/2/3/5 × 10^n，模拟 ECharts 行为）。
 * @param min - 数据最小值
 * @param max - 数据最大值
 * @param splitNumber - 期望的分割段数
 * @returns 对齐后的主刻度间隔
 */
declare function computeNiceInterval(min: number, max: number, splitNumber: number): number;
/**
 * 计算堆叠系列在指定轴上的数据范围（分组求和 + 非堆叠系列取极值）。
 * @param stackSeries - 堆叠信息列表
 * @param axisIndex - 数值轴索引
 * @returns 堆叠后的最小/最大值，无有效数据时返回 undefined
 */
declare function computeStackedRange(stackSeries: StackInfo[], axisIndex: number): {
    min: number;
    max: number;
} | undefined;
/**
 * 估算轴标题的宽高占图表容器的比例（0~1），含 CJK 字符宽度估算。
 * @param name - 轴标题文本
 * @param fontSize - 字号（px），缺省按 12
 * @param chartWidth - 图表宽度（px）
 * @param chartHeight - 图表高度（px）
 * @returns 相对宽高的比例对象，无效输入时返回 undefined
 */
declare function resolveAxisTitleSize(name: string | undefined, fontSize: number | undefined, chartWidth: number, chartHeight: number): {
    w: number;
    h: number;
} | undefined;
/**
 * 提取数值轴配置（支持单轴/多轴、堆叠范围、grid line 样式）。
 * @param yAxis - ECharts yAxis 单项或数组
 * @param barDir - 柱状图方向：纵向列图或横向条形图
 * @param chartWidth - 图表宽度
 * @param chartHeight - 图表高度
 * @param seriesData - 可选，系列数据（非堆叠时用于数据范围）
 * @param stackSeries - 可选，堆叠系列信息
 * @returns 幻灯片数值轴配置数组
 */
declare function extractValueAxes(yAxis: EChartsOptionAxis | EChartsOptionAxis[] | undefined, barDir: "col" | "bar", chartWidth: number, chartHeight: number, seriesData?: ChartSeries[], stackSeries?: StackInfo[]): ChartValueAxis[];
/**
 * 根据刻度间隔生成 Excel 数字格式（如 "#,##0" 或 "0.##"）。
 * @param majorUnit - 主刻度间隔；未传或 ≥1 时使用千分位整数格式
 * @returns Excel 数字格式字符串
 */
declare function computeBaseNumFmt(majorUnit?: number): string;
/**
 * 从 axisLabel.formatter（如 "{value}万"）提取 Excel 数字格式。
 * @param formatter - ECharts axisLabel formatter 字符串
 * @param majorUnit - 主刻度间隔，用于小数位数
 * @returns 组合的 Excel 格式，无法解析时返回 undefined
 */
declare function resolveAxisLabelFormat(formatter: string | undefined, majorUnit?: number): string | undefined;
/**
 * 从函数式 axisLabel.formatter 中推断 Excel 数字格式。
 * 通过传入正/负样本值调用 formatter，分析输出模式：
 * - 提取前缀/后缀（如 "%"）
 * - 检测是否对负值取绝对值（双向条形图常见）
 * 绝对值场景生成双段格式（如 `#,##0"%";#,##0"%"`），隐藏负号。
 */
declare function resolveFnAxisLabelFormat(formatter: (value: number | string, index?: number) => string, majorUnit?: number): string | undefined;
/**
 * 从数据标签 formatter（如 "{c}%"）提取 Excel 数字格式。
 * @param formatter - 数据标签 formatter（仅字符串会解析）
 * @returns Excel 格式字符串，不匹配时返回 undefined
 */
declare function resolveDataLabelFormat(formatter: string | Function | undefined): string | undefined;
/**
 * 将 ECharts position 字符串映射为 OOXML 数据标签位置枚举。
 * @param position - ECharts 数据标签位置字符串
 * @returns 幻灯片数据标签位置简写，未识别或未传时返回 undefined
 */
declare function resolveDataLabelPosition(position: string | undefined): ChartDataLabel["position"];
/**
 * 从分类轴 data 或合成默认名称中提取类别列表。
 * @param axis - 分类轴配置单项或数组
 * @param dataLength - 无 data 时用于生成占位类别名的长度
 * @returns 类别字符串数组
 */
declare function extractAxisCategories(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined, dataLength: number): string[];
/**
 * 检测分类轴是否设置了 inverse（反向）。
 * @param axis - 分类轴配置单项或数组
 * @returns 为 true 表示反向，否则 undefined
 */
declare function extractCatAxisInverse(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined): boolean | undefined;
/**
 * 提取轴标题文本。
 * @param axis - 轴配置单项或数组
 * @returns 轴名称，无则 undefined
 */
declare function extractAxisTitle(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined): string | undefined;
/**
 * 提取 boundaryGap：false → 数据点在刻度上，true → 在刻度之间。
 * @param axis - 分类轴配置单项或数组
 * @returns 边界间隙布尔值，未设置时 undefined
 */
declare function extractCatBoundaryGap(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined): boolean | undefined;
/**
 * 提取分类轴标签颜色（回退到轴线颜色）。
 * @param axis - 分类轴配置单项或数组
 * @returns 颜色字符串，无则 undefined
 */
declare function extractCatAxisLabelColor(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined): string | undefined;
/**
 * 提取分类轴标签是否粗体。
 * @param axis - 分类轴配置单项或数组
 * @returns 为粗体返回 true，否则 undefined
 */
declare function extractCatAxisLabelBold(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined): boolean | undefined;
/**
 * 提取分类轴标签字号（px → OOXML 百分之一磅）。
 * @param axis - 分类轴配置单项或数组
 * @returns 字号（百分之一磅），无则 undefined
 */
declare function extractCatAxisLabelFontSize(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined): number | undefined;
/**
 * 提取分类轴网格线配置（颜色、不透明度、虚线样式）。
 * @param axis - 分类轴配置单项或数组
 * @returns 网格线显示与样式字段；无有效 splitLine 时为空对象
 */
declare function extractCatAxisGridLines(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined): {
    showGridLines?: boolean;
    gridLineColor?: string;
    gridLineOpacity?: number;
    gridLineWidth?: number;
    gridLineDash?: "solid" | "dash" | "dot";
};
/**
 * 提取分类轴轴线颜色（已规范化为 HEX）。
 * @param axis - 分类轴配置单项或数组
 * @returns HEX 颜色字符串，无配置时 undefined
 */
declare function extractCatAxisLineColor(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined): string | undefined;
declare function extractCatAxisLineWidth(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined): number;
/**
 * 提取分类轴 axisLine/axisTick 的显示状态。
 * @param axis - 分类轴配置单项或数组
 * @param prop - 取 axisLine 或 axisTick
 * @returns 对应元素 show 非 false 时为 true；无轴配置时默认为 true
 */
declare function extractCatAxisProp(axis: EChartsOptionAxis | EChartsOptionAxis[] | undefined, prop: "axisLine" | "axisTick"): boolean;
export { computeNiceInterval, computeStackedRange, resolveAxisTitleSize, extractValueAxes, computeBaseNumFmt, resolveAxisLabelFormat, resolveFnAxisLabelFormat, resolveDataLabelFormat, resolveDataLabelPosition, extractAxisCategories, extractCatAxisInverse, extractAxisTitle, extractCatBoundaryGap, extractCatAxisLabelColor, extractCatAxisLabelBold, extractCatAxisLabelFontSize, extractCatAxisGridLines, extractCatAxisLineColor, extractCatAxisLineWidth, extractCatAxisProp, };
