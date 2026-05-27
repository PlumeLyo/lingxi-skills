/** 将 CSS 长度值（px/rem/em/vw/vh/%）解析为像素数 */
declare function parseToPixels(value: string | number, element?: Element): number;
/** 像素转磅值（pt） */
declare function pxToPt(px: number | string): number;
/**
 * 测量指定字体和字号下单个 NBSP（\u00A0）的实际像素宽度。
 * 通过插入隐藏 span 批量测量后取平均值，结果按 font-family + font-size 缓存。
 */
declare function measureNbspWidth(fontFamily: string, fontSizePx: number): number;
export { parseToPixels, pxToPt, measureNbspWidth };
