declare function normalizeHexColor(input: string | undefined): string | undefined;
declare function buildSrgbClr(color: string, opacity?: number): string;
declare function buildSolidFill(color?: string, opacity?: number): string;
declare function buildNoFill(): string;
export { normalizeHexColor, buildSrgbClr, buildSolidFill, buildNoFill };
