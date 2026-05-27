import { resolveHtml, ResolveResult } from './utils/html-resolver';
import { generatePptxFromElements, generatePptxMultiSlide, generatePptx, downloadPptx, GenerateOptions, SlideData } from './utils/pptx-builder';
interface HtmlToPptxOptions {
    /** iframe 宽度（像素），默认 1280 */
    width?: number;
    /** iframe 高度（像素），默认 720 */
    height?: number;
    /** PPTX 文件标题 */
    title?: string;
    /** 幻灯片宽度（英寸） */
    slideWidth?: number;
    /** 幻灯片高度（英寸） */
    slideHeight?: number;
    /** 所有 HTML 页面共享的全局 CSS 样式，会注入到每个 iframe 的 <head> 中 */
    globalStyles?: string;
}
/**
 * 在隐藏 iframe 中加载 HTML 并解析为 SlideData
 */
declare function resolveHtmlInHiddenIframe(htmlContent: string, width?: number, height?: number, globalStyles?: string): Promise<SlideData>;
/**
 * 将 HTML 字符串数组转换为多页 PPTX Blob
 *
 * @param htmlArray - HTML 字符串数组，每个元素对应一页幻灯片
 * @param options - 可选配置
 * @returns PPTX 文件 Blob
 */
declare function htmlArrayToPptxBlob(htmlArray: string[], options?: HtmlToPptxOptions): Promise<Blob>;
export type { ResolveResult, GenerateOptions, SlideData, HtmlToPptxOptions };
export { resolveHtml, generatePptxFromElements, generatePptxMultiSlide, generatePptx, downloadPptx, resolveHtmlInHiddenIframe, htmlArrayToPptxBlob, };
