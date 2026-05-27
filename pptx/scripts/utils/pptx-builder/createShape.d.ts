import { PPTShapeElement } from '../../types/slides';
import { XmlRenderable } from './ooxml/types';
declare function createShapeRenderables(element: PPTShapeElement): XmlRenderable[];
export { createShapeRenderables };
