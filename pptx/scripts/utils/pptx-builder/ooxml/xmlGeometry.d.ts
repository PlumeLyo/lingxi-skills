interface XmlGeometryInput {
    shapeType?: "ellipse" | "roundRect";
    customPath?: string;
    viewBox?: [number, number];
    roundRectRadiusPt?: number;
    wInch?: number;
    hInch?: number;
}
declare function buildGeometryXml(input: XmlGeometryInput): string;
export type { XmlGeometryInput };
export { buildGeometryXml };
