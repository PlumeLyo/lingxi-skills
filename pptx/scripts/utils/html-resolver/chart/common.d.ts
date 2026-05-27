import { ChartSeries } from '../../../types/slides';
import { EChartsOption, EChartsOptionSeries } from './types';
declare function extractTitleInfo(option: EChartsOption): {
    title: string | undefined;
    titleFontSize: number | undefined;
    titleColor: string | undefined;
};
declare function extractPaletteColors(option: EChartsOption): string[] | undefined;
/**
 * 将顶层 option.label 合并到没有自定义 label 的系列上（就地修改）。
 */
declare function mergeGlobalLabels(option: EChartsOption, effectiveSeries: EChartsOptionSeries[]): void;
declare function buildConvertedSeries(element: Element, option: EChartsOption, effectiveSeries: EChartsOptionSeries[], isPie: boolean): ChartSeries[];
/**
 * 判断 ECharts fontWeight 值是否应映射为 OOXML bold (b="1")。
 * OOXML 仅支持 bold / 非 bold 二值，>= 600 (semi-bold) 视为 bold。
 */
declare function isBoldWeight(fontWeight: string | number | undefined | null): boolean;
export { extractTitleInfo, extractPaletteColors, mergeGlobalLabels, buildConvertedSeries, isBoldWeight, };
