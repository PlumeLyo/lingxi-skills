import { PPTChartElement } from '../../types/slides';
/**
 * 生成嵌入 Excel .xlsx 的二进制数据
 */
declare function generateChartExcel(element: PPTChartElement): Promise<Uint8Array>;
export { generateChartExcel };
