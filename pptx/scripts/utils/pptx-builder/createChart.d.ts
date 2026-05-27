import { PPTChartElement } from '../../types/slides';
import { OoxmlPresentation } from './ooxmlPackage';
import { XmlRenderable } from './ooxml/types';
/**
 * 创建图表渲染对象。
 *
 * Excel 生成是异步的（JSZip.generateAsync），
 * 在调用时预先生成好所有数据，toXml() 中同步引用 chartFileName。
 */
declare function createChartRenderables(element: PPTChartElement, presentation: OoxmlPresentation): Promise<XmlRenderable[]>;
export { createChartRenderables };
