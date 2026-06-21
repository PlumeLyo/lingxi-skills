import { OoxmlTextRun } from './ooxml/types';
/**
 * 富文本解析选项
 */
interface RichTextParseOptions {
    /** 默认字体名称 */
    defaultFontName: string;
    /** 默认颜色 */
    defaultColor: string;
    /** 默认颜色的透明度（来自 CSS color 的 alpha，仅影响使用默认颜色的 run） */
    defaultColorOpacity?: number;
    /** 默认字体大小 */
    defaultFontSize?: number;
    /** 是否加粗 */
    bold?: boolean;
    /** 是否斜体 */
    italic?: boolean;
}
/**
 * 转换为字符间距
 * @param value 字符间距值
 * @returns 限制在-256到256之间的值
 */
declare function toCharacterSpacing(value: number | undefined): number | undefined;
/**
 * 将HTML内容解析为PPTX文本片段
 * @param content HTML内容字符串
 * @param opts 富文本解析选项
 * @returns PPTX文本属性数组
 */
declare function parseHtmlToTextSegments(content: string, opts: RichTextParseOptions): OoxmlTextRun[];
export type { RichTextParseOptions };
export { toCharacterSpacing, parseHtmlToTextSegments };
