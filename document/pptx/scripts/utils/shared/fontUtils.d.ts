/**
 * 字体选择工具
 *
 * 从 CSS font-family 列表中过滤掉通用族名和浏览器伪字体，
 * 选取第一个 PPT 支持的具体字体名称。
 */
/** 默认字体（所有未匹配到具体字体时的回退） */
declare const DEFAULT_FONT_FAMILY = "Microsoft YaHei";
/** 从 CSS font-family 列表中选取第一个 PPT 支持的字体 */
declare function pickSupportedFontFamily(rawFontFamily: string | undefined, fallback?: string): string;
export { DEFAULT_FONT_FAMILY, pickSupportedFontFamily };
