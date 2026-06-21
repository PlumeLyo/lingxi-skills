import { OoxmlSlide } from './ooxml/xmlSlide';
import { Gradient } from '../../types/slides';
/** 幻灯片背景：纯色 HEX 字符串或 Gradient 渐变对象 */
type SlideBackground = string | Gradient;
interface OoxmlPresentationInit {
    title?: string;
    width: number;
    height: number;
}
declare class OoxmlPresentation {
    private readonly title;
    private readonly width;
    private readonly height;
    private readonly slides;
    private mediaCounter;
    private mediaByKey;
    private chartCounter;
    private overlayCounter;
    private readonly charts;
    constructor(init: OoxmlPresentationInit);
    addSlide(background?: SlideBackground): OoxmlSlide;
    addMedia(source: string): string;
    nextOverlayId(prefix: string): string;
    addChart(chartXml: string, excelBytes: Uint8Array): string;
    private sourceToMedia;
    toBlob(): Promise<Blob>;
    private indexOfSlide;
    private buildContentTypes;
}
export { OoxmlPresentation };
