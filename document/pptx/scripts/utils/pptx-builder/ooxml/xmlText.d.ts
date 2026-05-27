import { OoxmlTextParagraph, OoxmlTextRun, XmlRenderable } from './types';
import { XmlShapeInput } from './xmlShape';
declare function buildTextBodyXml(input: {
    paragraphs: OoxmlTextParagraph[];
    vertical?: boolean;
    valign?: "top" | "middle" | "bottom";
    noWrap?: boolean;
}): string;
interface XmlTextBoxInput extends XmlShapeInput {
    paragraphs: OoxmlTextParagraph[];
    vertical?: boolean;
    valign?: "top" | "middle" | "bottom";
    noWrap?: boolean;
}
declare function createTextBoxRenderable(input: XmlTextBoxInput): XmlRenderable;
declare function createSimpleParagraphFromText(text: string, style?: Partial<OoxmlTextRun>): OoxmlTextParagraph[];
export { buildTextBodyXml, createTextBoxRenderable, createSimpleParagraphFromText };
