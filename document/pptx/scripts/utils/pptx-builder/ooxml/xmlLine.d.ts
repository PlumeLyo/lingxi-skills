import { LineStyleType, PPTElementOutline } from '../../../types/slides';
import { buildNoFill } from './xmlColor';
declare function buildLineXml(outline: PPTElementOutline | undefined): string;
declare function buildArrowLineXml(input: {
    color: string;
    width: number;
    style?: LineStyleType;
    beginArrow?: "none" | "triangle" | "oval";
    endArrow?: "none" | "triangle" | "oval";
    opacity?: number;
}): string;
export { buildLineXml, buildArrowLineXml, buildNoFill };
