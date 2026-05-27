import { ChartGradientStop } from '../../../types/slides';
import { EChartsOptionSeries } from './types';
declare const TRANSPARENT_MARKER = "__transparent__";
/**
 * 判断颜色字符串是否为透明色。
 * @param color - CSS 颜色字符串
 * @returns 是否透明
 */
declare function isTransparentColorStr(color: string): boolean;
/**
 * 将 rgb/rgba/hex/transparent 等颜色值统一规范为 #rrggbb 格式。
 * @param color - 颜色值（字符串或其他类型）
 * @returns 规范化的 hex 字符串，非字符串输入返回 "#000000"
 */
declare function normalizeColorHex(color: unknown): string;
/**
 * 从 rgba/rgb 字符串中提取不透明度。
 * @param color - CSS 颜色字符串
 * @returns 不透明度 0~1，非 rgba 格式返回 1
 */
declare function parseRgbaOpacity(color: unknown): number;
/**
 * 类型守卫：判断颜色值是否为 ECharts 渐变对象。
 * @param color - 待检测的颜色值
 * @returns 是否为包含 colorStops 的渐变对象
 */
declare function isGradientColor(color: unknown): color is {
    type: string;
    colorStops: {
        offset: number;
        color: string;
    }[];
};
/**
 * 从 ECharts 渐变色 colorStops 中提取 OOXML 渐变停靠点。
 * @param color - 包含 colorStops 数组的渐变对象
 * @returns ChartGradientStop 数组
 */
declare function extractGradientStops(color: {
    colorStops: {
        offset: number;
        color: string;
    }[];
}): ChartGradientStop[];
/**
 * 从 ECharts 线性渐变向量计算 OOXML 旋转角度。
 * @param color - 渐变坐标对象 { x, y, x2, y2 }
 * @returns 角度值（EMU 单位，60000 分之一度）
 */
declare function extractGradientAngle(color: {
    x?: number;
    y?: number;
    x2?: number;
    y2?: number;
}): number;
/**
 * 从 series.itemStyle.color 提取整体渐变填充配置。
 * @param series - ECharts 系列对象
 * @returns 渐变停靠点和角度，非渐变返回 undefined
 */
declare function extractSeriesGradient(series: EChartsOptionSeries): {
    stops: ChartGradientStop[];
    angle: number;
} | undefined;
/**
 * 按优先级获取系列颜色原始值。
 * 优先级：lineStyle.color > itemStyle.color > gradient 首色 > palette
 * @param series - ECharts 系列对象
 * @param palette - 全局调色板
 * @param index - 系列在调色板中的索引
 * @returns 原始颜色字符串，未找到返回 undefined
 */
declare function getSeriesColor(series: EChartsOptionSeries, palette: unknown[] | undefined, index: number): string | undefined;
/**
 * 获取系列颜色并规范化为 hex 格式。
 * @param s - ECharts 系列对象
 * @param palette - 全局调色板
 * @param idx - 系列索引
 * @returns 规范化的 hex 颜色或 undefined
 */
declare function resolveSeriesColor(s: EChartsOptionSeries, palette: unknown[] | undefined, idx: number): string | undefined;
/**
 * 获取标记点颜色（不含 lineStyle.color）。
 * @param series - ECharts 系列对象
 * @param palette - 全局调色板
 * @param index - 系列索引
 * @returns 原始颜色字符串或 undefined
 */
declare function getMarkerColor(series: EChartsOptionSeries, palette: unknown[] | undefined, index: number): string | undefined;
/**
 * 解析 CSS 变量 var(--name)，从元素所在文档的计算样式中获取实际值。
 * @param value - 可能包含 var() 的字符串
 * @param element - DOM 元素（用于获取计算样式）
 * @returns 解析后的值，非字符串输入返回 undefined
 */
declare function resolveCssVar(value: unknown, element: Element): string | undefined;
/**
 * 提取图表容器的非透明、非白色背景色。
 * @param element - 图表容器 DOM 元素
 * @returns hex 背景色或 undefined
 */
declare function extractChartBackground(element: Element): string | undefined;
/**
 * 提取图表容器的圆角半径。
 * @param element - 图表容器 DOM 元素
 * @returns 圆角半径（pt），无圆角返回 undefined
 */
declare function extractChartBorderRadius(element: Element): number | undefined;
export { TRANSPARENT_MARKER, isTransparentColorStr, normalizeColorHex, parseRgbaOpacity, isGradientColor, extractGradientStops, extractGradientAngle, extractSeriesGradient, getSeriesColor, resolveSeriesColor, getMarkerColor, resolveCssVar, extractChartBackground, extractChartBorderRadius, };
