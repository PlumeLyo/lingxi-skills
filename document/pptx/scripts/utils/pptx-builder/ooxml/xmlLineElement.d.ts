import { LineStyleType, PPTElementShadow } from '../../../types/slides';
import { XmlRenderable } from './types';
interface XmlLineElementInput {
    id: string;
    name?: string;
    x: number;
    y: number;
    w: number;
    h: number;
    color: string;
    widthPt: number;
    style?: LineStyleType;
    beginArrow?: "none" | "triangle" | "oval";
    endArrow?: "none" | "triangle" | "oval";
    opacity?: number;
    shadow?: PPTElementShadow;
    flipH?: boolean;
    flipV?: boolean;
}
declare function createLineRenderable(input: XmlLineElementInput): XmlRenderable;
export { createLineRenderable };
