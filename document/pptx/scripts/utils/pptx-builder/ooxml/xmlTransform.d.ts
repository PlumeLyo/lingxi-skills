interface XmlTransformInput {
    x: number;
    y: number;
    w: number;
    h: number;
    rotation?: number;
    flipH?: boolean;
    flipV?: boolean;
}
declare function buildXfrmXml(input: XmlTransformInput): string;
export type { XmlTransformInput };
export { buildXfrmXml };
