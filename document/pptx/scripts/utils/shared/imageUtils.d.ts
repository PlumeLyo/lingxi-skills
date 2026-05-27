/**
 * 图片常量与工具
 *
 * 提供透明占位图常量和 SVG data URL 格式标准化等通用图片处理函数，
 * 供 html-resolver 和 pptx-builder 两个模块共同使用。
 */
/** 1x1 透明 PNG 的 base64 编码 */
declare const TRANSPARENT_1X1_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
/** 1x1 透明 PNG DataURL，用作截图/图片失败时的占位图 */
declare const TRANSPARENT_1X1_DATAURL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
/** 1x1 透明 PNG 的二进制字节，用作 PPTX 打包时的占位图 */
declare const TRANSPARENT_1X1_PNG_BYTES: Uint8Array<ArrayBuffer>;
/**
 * 从 CSS url() 的原始内容中提取实际 URL（剥离引号 + 反转义 CSS 转义序列）
 * @param raw url( 和 ) 之间的原始内容
 * @returns 干净的 URL 字符串
 */
declare function unescapeCssUrl(raw: string): string;
/**
 * 将非 base64 的 SVG data URL（utf8 / charset=utf-8）转为 base64 格式，
 * 非 SVG 或已为 base64 的 URL 原样返回
 * @param url 原始 data URL
 * @returns 标准化后的 data URL
 */
declare function normalizeSvgDataUrl(url: string): string;
/**
 * 加载图片并获取自然尺寸，超时 5s 后降级返回 null
 */
declare function loadImageNaturalSize(src: string): Promise<{
    width: number;
    height: number;
} | null>;
export { TRANSPARENT_1X1_BASE64, TRANSPARENT_1X1_DATAURL, TRANSPARENT_1X1_PNG_BYTES, unescapeCssUrl, normalizeSvgDataUrl, loadImageNaturalSize, };
