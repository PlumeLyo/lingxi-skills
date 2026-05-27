import { PPTElementShadow } from '../../../types/slides';
interface XmlShadowConfig extends PPTElementShadow {
    type?: "outer" | "inner";
    sx?: number;
    sy?: number;
    kx?: number;
    ky?: number;
    align?: "tl" | "t" | "tr" | "l" | "ctr" | "r" | "bl" | "b" | "br";
}
interface XmlGlowConfig {
    radiusPt: number;
    color: string;
    opacity?: number;
}
declare function buildShadowXml(shadow: XmlShadowConfig | undefined, elementSizePt?: {
    wPt: number;
    hPt: number;
}): string;
declare function buildGlowXml(glow: XmlGlowConfig | undefined): string;
declare function buildEffectListXml(input: {
    shadow?: XmlShadowConfig;
    glow?: XmlGlowConfig;
    elementSizePt?: {
        wPt: number;
        hPt: number;
    };
}): string;
export type { XmlShadowConfig, XmlGlowConfig };
export { buildShadowXml, buildGlowXml, buildEffectListXml };
