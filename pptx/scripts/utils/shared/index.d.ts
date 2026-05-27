/**
 * 共享工具模块
 *
 * 提供颜色解析、字体选择、CSS 单位转换、样式解析等通用工具函数，
 * 供 html-parser 和 pptx-builder 两个模块共同使用。
 *
 * @module shared
 */
export { parseColor, rgbToHex, isTransparentColor, blendToWhite, } from './colorUtils';
export type { RgbColor } from './colorUtils';
export { pickSupportedFontFamily, DEFAULT_FONT_FAMILY } from './fontUtils';
export { parseToPixels, pxToPt } from './unitUtils';
export { parseRotateFromTransform, parseFlipFromTransform, parseBoxShadowToElementShadow, getOriginalSize, } from './styleParser';
export { TRANSPARENT_1X1_BASE64, TRANSPARENT_1X1_DATAURL, TRANSPARENT_1X1_PNG_BYTES, unescapeCssUrl, normalizeSvgDataUrl, } from './imageUtils';
