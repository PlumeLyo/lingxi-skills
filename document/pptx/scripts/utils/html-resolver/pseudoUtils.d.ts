/**
 * 伪元素检测与截图工具
 *
 * 检测 ::before/::after 是否有可见内容或装饰性背景，
 * 并将伪元素 content 文本渲染为 canvas 截图。
 */
/**
 * 判断 ::before/::after 是否有可见的 content
 * @param element 待检查的 DOM 元素
 * @returns 伪元素是否有可见 content
 */
declare function hasPseudoContent(element: Element): boolean;
/**
 * 判断伪元素是否有装饰性背景/尺寸（需单独渲染）
 * @param element 待检查的 DOM 元素
 * @returns 伪元素是否有装饰性背景或尺寸
 */
declare function hasPseudoDecoration(element: Element): boolean;
/**
 * 清除 counter 预计算缓存。
 * 应在每次 resolveHtml 调用前清除，避免跨页面缓存污染。
 */
declare function clearCounterCache(): void;
/**
 * 将 content 字符串解析为可渲染文本。
 * 当不含 counter()/counters()/attr() 时，仅做去引号和 unicode 转义。
 * 当包含函数调用时，需要传入 element 以计算实际值。
 * @param raw 原始 content 字符串
 * @param element 可选，含伪元素的 DOM 元素（用于 counter 计算）
 * @returns 解析后的可渲染文本
 */
declare function resolvePseudoContentToText(raw: string, element?: Element): string;
interface PseudoIconCapture {
    src: string;
    width: number;
    height: number;
}
/**
 * 将伪元素 content 文本渲染为图片并返回 DataURL 及尺寸
 * @param element 含伪元素 content 的 DOM 元素
 * @returns DataURL、宽度、高度，若无法渲染则返回 null
 */
declare function captureElementDirectly(element: Element): Promise<PseudoIconCapture | null>;
export type { PseudoIconCapture };
export { hasPseudoContent, hasPseudoDecoration, captureElementDirectly, resolvePseudoContentToText, clearCounterCache, };
