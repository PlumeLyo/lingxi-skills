import { PPTLineElement } from '../../types/slides';
import { XmlRenderable } from './ooxml/types';
/**
 * 将 PPTLineElement 添加到幻灯片
 * @param slide 幻灯片实例
 * @param el 线条元素
 * @param pptx 导出器实例
 */
declare function createLineRenderableFromElement(el: PPTLineElement): XmlRenderable;
export { createLineRenderableFromElement };
