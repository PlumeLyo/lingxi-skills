/**
 * 颜色处理工具
 *
 * 提供 rgba/hex 颜色字符串解析、RGB 到十六进制转换、
 * 透明色检测、半透明色白底混合等功能。
 */
/** RGB(A) 颜色值 */
interface RgbColor {
    r: number;
    g: number;
    b: number;
    /** 透明度，0~1 */
    a?: number;
}
/** 解析 rgba 或 hex 颜色字符串为 RgbColor */
declare function parseColor(color: string | null | undefined): RgbColor | null;
/** RgbColor 转 #RRGGBB 十六进制字符串 */
declare function rgbToHex(color: RgbColor): string;
interface ColorHexOpacity {
    color: string;
    opacity?: number;
}
/** 解析颜色并提取 alpha，返回 #RRGGBB 和透明度 */
declare function resolveColorHexOpacity(color: string | null | undefined, fallback?: string): ColorHexOpacity;
/** 判断颜色是否为透明或接近透明 */
declare function isTransparentColor(color: string | null | undefined): boolean;
/** 将半透明颜色与白色混合，得到不透明等效色 */
declare function blendToWhite(color: RgbColor): RgbColor;
/**
 * 解析 CSS 颜色值，支持 var(--token)、命名色等 parseColor 无法直接处理的形式。
 * 先尝试直接解析，失败后通过 DOM 探针获取浏览器计算值再解析。
 */
declare function parseCssColorWithFallback(colorValue: string, ownerDoc: Document): RgbColor | null;
export type { RgbColor, ColorHexOpacity };
export { parseColor, rgbToHex, resolveColorHexOpacity, isTransparentColor, blendToWhite, parseCssColorWithFallback, };
