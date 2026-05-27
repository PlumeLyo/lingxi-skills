import { PPTLatexElement } from '../../types/slides';
import { XmlRenderable } from './ooxml/types';
/**
 * 将 SVG path + viewBox 渲染为 dataURL
 * @param path SVG 路径字符串
 * @param viewBox viewBox 尺寸 [宽, 高]
 * @param color 填充与描边颜色
 * @param strokeWidth 描边宽度
 * @returns Base64 编码的 data URL 字符串，无效时返回空字符串
 */
declare function renderSvgToDataUrl(path: string, viewBox: [number, number], color: string, strokeWidth: number): string;
/**
 * 将 LaTeX 公式元素转换为 renderable，优先 SVG 图片，回退纯文本。
 */
declare function createLatexRenderable(el: PPTLatexElement, mediaFile?: string): XmlRenderable;
export { createLatexRenderable, renderSvgToDataUrl };
