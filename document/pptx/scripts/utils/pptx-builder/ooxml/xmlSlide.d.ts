import { Gradient } from '../../../types/slides';
import { XmlRenderable, XmlMediaRef, XmlHyperlinkRef, XmlChartRef } from './types';
interface OoxmlSlideInit {
    index: number;
    background?: string | Gradient;
}
declare class OoxmlSlide {
    private readonly index;
    private readonly background?;
    private readonly elements;
    private readonly relationships;
    private shapeIdCounter;
    private relCounter;
    constructor(init: OoxmlSlideInit);
    addElement(renderable: XmlRenderable): void;
    allocShapeId(): number;
    addImage(source: string): XmlMediaRef;
    addHyperlink(url: string): XmlHyperlinkRef;
    addChart(chartFileName: string): XmlChartRef;
    getSlidePath(): string;
    getSlideRelsPath(): string;
    getRelationshipsXml(): string;
    toXml(): string;
}
export { OoxmlSlide };
