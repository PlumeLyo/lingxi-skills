import { PPTChartElement } from '../../../types/slides';
import { XmlRenderable } from './types';
declare const DEFAULT_PALETTE: string[];
/**
 * 将列索引转为 Excel 列字母（0→A, 1→B, …, 25→Z, 26→AA）
 */
declare function colLetter(idx: number): string;
/**
 * 生成完整的 c:chartSpace XML
 */
declare function buildChartSpaceXml(element: PPTChartElement, excelRelId: string): string;
/**
 * 生成图表在 chart.xml.rels 中对 Excel 嵌入文件的关系 XML
 */
declare function buildChartRelsXml(excelRelId: string, excelTarget: string): string;
interface ChartFrameInput {
    name: string;
    x: number;
    y: number;
    w: number;
    h: number;
    chartFileName: string;
}
declare function createChartFrameRenderable(input: ChartFrameInput): XmlRenderable;
export { buildChartSpaceXml, buildChartRelsXml, createChartFrameRenderable, colLetter, DEFAULT_PALETTE, };
