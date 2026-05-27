import { PPTTextElement } from '../../types/slides';
import { XmlRenderable } from './ooxml/types';
declare function createTextRenderable(el: PPTTextElement): XmlRenderable;
export { createTextRenderable };
