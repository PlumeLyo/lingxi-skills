import { ChartGraphicText } from '../../../types/slides';
import { EChartsInstance, EChartsGraphicElement } from './types';
/**
 * 尝试从 ECharts 实例的内部模型中获取 graphic 配置。
 * 作为 getOption().graphic 的备用路径。
 * @param instance - ECharts 实例
 * @returns graphic 元素数组，无法获取时 undefined
 */
declare function getGraphicFromModel(instance: EChartsInstance): EChartsGraphicElement[] | undefined;
/**
 * 从 ECharts graphic 配置中提取文本元素。
 * 兼容 getOption() 返回的 [{ elements: [...] }] 以及原始 setOption 结构。
 * @param graphic - graphic 配置或元素列表
 * @param chartWidth - 图表宽度（像素）
 * @param chartHeight - 图表高度（像素）
 * @returns 文本元素数组，无有效文本时 undefined
 */
declare function extractGraphicTexts(graphic: EChartsGraphicElement | EChartsGraphicElement[] | undefined, chartWidth: number, chartHeight: number): ChartGraphicText[] | undefined;
export { getGraphicFromModel, extractGraphicTexts };
