import { LineStyleType, TableCell } from '../../../types/slides';
import { XmlRenderable } from './types';
interface XmlTableInput {
    id: string;
    name?: string;
    x: number;
    y: number;
    w: number;
    h: number;
    rows: TableCell[][];
    colWidths: number[];
    rowHeights: number[];
    cellMinHeight: number;
    borderColor?: string;
    borderWidth?: number;
    borderStyle?: LineStyleType;
    borderOpacity?: number;
}
declare function createTableRenderable(input: XmlTableInput): XmlRenderable;
export { createTableRenderable };
