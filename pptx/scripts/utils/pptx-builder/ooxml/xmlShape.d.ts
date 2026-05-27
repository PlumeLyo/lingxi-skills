import { Gradient, PPTElementOutline, PPTElementShadow } from '../../../types/slides';
import { XmlRenderable } from './types';
interface XmlShapeInput {
    id: string;
    name?: string;
    x: number;
    y: number;
    w: number;
    h: number;
    rotation?: number;
    flipH?: boolean;
    flipV?: boolean;
    shapeType?: "ellipse" | "roundRect";
    customPath?: string;
    viewBox?: [number, number];
    roundRectRadiusPt?: number;
    fill?: string;
    fillOpacity?: number;
    gradient?: Gradient;
    outline?: PPTElementOutline;
    shadow?: PPTElementShadow;
    spreadOnlyGlowPt?: number;
}
declare function buildShapeSpPrXml(input: XmlShapeInput): string;
declare function createShapeRenderable(input: XmlShapeInput): XmlRenderable;
export type { XmlShapeInput };
export { buildShapeSpPrXml, createShapeRenderable };
