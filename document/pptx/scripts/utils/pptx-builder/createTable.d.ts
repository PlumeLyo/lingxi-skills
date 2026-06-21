import { PPTTableElement } from '../../types/slides';
import { XmlRenderable } from './ooxml/types';
declare function createTableRenderableFromElement(el: PPTTableElement): XmlRenderable;
export { createTableRenderableFromElement };
