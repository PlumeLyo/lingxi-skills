import { PPTImageElement } from '../../types/slides';
import { XmlRenderable } from './ooxml/types';
declare function createImageRenderableFromElement(el: PPTImageElement, mediaFile: string): XmlRenderable;
export { createImageRenderableFromElement };
