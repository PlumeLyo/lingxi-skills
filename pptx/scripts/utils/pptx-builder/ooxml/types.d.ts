import { Gradient, PPTElementOutline, PPTElementShadow, TextAlign } from '../../../types/slides';
interface XmlMediaRef {
    relId: string;
    target: string;
}
interface XmlHyperlinkRef {
    relId: string;
    target: string;
}
interface XmlChartRef {
    relId: string;
    chartFileName: string;
}
interface OoxmlSlideContext {
    allocShapeId: () => number;
    addImage: (source: string) => XmlMediaRef;
    addHyperlink: (url: string) => XmlHyperlinkRef;
    addChart: (chartFileName: string) => XmlChartRef;
}
interface XmlRenderable {
    toXml: (ctx: OoxmlSlideContext) => string;
}
interface OoxmlTextRun {
    text: string;
    fontFace?: string;
    fontSize?: number;
    charSpacing?: number;
    bold?: boolean;
    italic?: boolean;
    underline?: boolean;
    underlineColor?: string;
    strike?: boolean;
    color?: string;
    opacity?: number;
    gradient?: Gradient;
    /** 基线偏移（千分比），正值=上标，负值=下标。OOXML baseline 属性 */
    baseline?: number;
    /** 文字描边宽度（pt） */
    textStrokeWidth?: number;
    /** 文字描边颜色（hex） */
    textStrokeColor?: string;
    /** 文字描边颜色透明度 */
    textStrokeOpacity?: number;
}
interface OoxmlTextParagraph {
    runs: OoxmlTextRun[];
    align?: TextAlign;
    lineSpacingPct?: number;
    lineSpacingPt?: number;
    spaceAfterPt?: number;
    indentPt?: number;
}
interface OoxmlShapeStyle {
    fill?: string;
    fillOpacity?: number;
    gradient?: Gradient;
    outline?: PPTElementOutline;
    shadow?: PPTElementShadow;
}
export type { XmlRenderable, OoxmlSlideContext, XmlMediaRef, XmlHyperlinkRef, XmlChartRef, OoxmlTextRun, OoxmlTextParagraph, OoxmlShapeStyle, };
