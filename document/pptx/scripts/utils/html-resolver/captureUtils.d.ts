import { PPTImageElement, PPTElementOutline, PPTElementShadow } from '../../types/slides';
import { ResolveContext } from './types';
import { TRANSPARENT_1X1_DATAURL } from '../shared/imageUtils';
/** 像素坐标矩形 */
interface PixelRect {
    left: number;
    top: number;
    width: number;
    height: number;
}
/** 截图图片的附加选项 */
interface CapturedImageOptions {
    rotate?: number;
    opacity?: number;
    radius?: number;
    outline?: PPTElementOutline;
    shadow?: PPTElementShadow;
}
/**
 * 从截图结果构建 PPTImageElement
 * @param ctx 解析上下文
 * @param rect 截图区域（像素坐标）
 * @param src 图片 DataURL
 * @param options 可选配置（旋转、透明度、圆角、边框、阴影）
 * @returns PPT 图片元素
 */
declare function buildCapturedImageElement(ctx: ResolveContext, rect: PixelRect, src: string, options?: CapturedImageOptions): PPTImageElement;
/**
 * 将 SVG data URL 背景通过 Image + Canvas 2D API 直接渲染为 DataURL。
 * 支持多层背景：每层 SVG url() 使用各自对应的
 * background-size、background-position、background-repeat 分别渲染后合成。
 * @param style 元素的计算样式
 * @param width 渲染宽度（像素）
 * @param height 渲染高度（像素）
 * @returns 成功时返回 DataURL，无法处理时返回 null
 */
declare function renderSvgBackgroundToDataURL(style: CSSStyleDeclaration, width: number, height: number): Promise<string | null>;
/**
 * 检测 radial-gradient 中是否含有亚像素（<1px）stop，
 * 如 `radial-gradient(#000 0.5px, transparent 0.5px)`。
 * Canvas 2D 无法精确渲染这类极小半径的圆点，需要走截图路径。
 */
declare function hasSubpixelRadialGradient(bgImage: string): boolean;
/**
 * 将 gradient + background-size 组合渲染为 Canvas DataURL。
 *
 * 对 radial/linear-gradient + 自定义 background-size 的平铺渲染处理，
 * 通过 Canvas 2D API 绘制单个渐变贴片后使用 createPattern 平铺。
 *
 * 支持多层背景：每层渐变使用各自对应的 background-size、
 * background-repeat、background-position 分别渲染后合成。
 *
 * @returns 成功时返回 DataURL，无法处理时返回 null
 */
declare function renderGradientPatternToDataURL(style: CSSStyleDeclaration, width: number, height: number): string | null;
/**
 * 将元素指定区域截图为 DataURL（支持 mask）
 * @param element 待截图的 DOM 元素
 * @param rect 截图区域
 * @param style 元素的计算样式
 * @returns 截图 DataURL
 */
declare function captureElementAsImage(element: Element, rect: DOMRect, style: CSSStyleDeclaration): Promise<string>;
/**
 * 将整个元素截图为 DataURL
 * @param element 待截图的 DOM 元素
 * @returns 截图 DataURL
 */
declare function captureFullElement(element: Element): Promise<string>;
/**
 * 解析 radial-gradient 描述中的中心位置（`at X% Y%` / `at Xpx Ypx`）
 * @param descriptor 渐变描述
 * @param w 宽度
 * @param h 高度
 * @returns 中心位置
 */
declare function parseRadialCenter(descriptor: string, w: number, h: number): {
    cx: number;
    cy: number;
};
/**
 * 将多层 background-image 渐变（radial/linear 混合）渲染为 Canvas DataURL。
 * PPT 无法原生表达多层渐变，本函数通过 Canvas 2D API 逐层渲染后合成，
 * 供伪元素装饰解析器作为降级路径。
 * @param bgImage 背景图片
 * @param bgColor 背景颜色
 * @param width 宽度
 * @param height 高度
 * @returns 成功时返回 DataURL，无法处理时返回 null
 */
declare function renderMultiLayerGradientToDataURL(bgImage: string, bgColor: string, width: number, height: number): string | null;
/**
 * 使用 Canvas 2D API 渲染 background-color + background-image(url) +
 * background-blend-mode 的混合效果。
 *
 * background-blend-mode 的 Canvas 模拟实现，通过
 * globalCompositeOperation 直接在 Canvas 上复现混合效果。
 *
 * @param imageUrl 背景图片 URL
 * @param style    元素的 computed style
 * @param width    渲染宽度（像素）
 * @param height   渲染高度（像素）
 * @returns 成功时返回合成后的 DataURL，无法处理时返回 null
 */
declare function renderBlendedBackgroundToDataURL(imageUrl: string, style: CSSStyleDeclaration, width: number, height: number): Promise<string | null>;
/**
 * 将 repeating-linear-gradient 背景渲染为 DataURL。
 * 创建临时 DOM 元素并通过 snapdom 截图，支持浏览器原生渲染的全部 CSS 渐变语法。
 */
declare function renderRepeatingGradientToDataURL(bgImage: string, bgColor: string | undefined, width: number, height: number): Promise<string | null>;
export type { PixelRect };
export { TRANSPARENT_1X1_DATAURL, buildCapturedImageElement, captureElementAsImage, captureFullElement, hasSubpixelRadialGradient, renderGradientPatternToDataURL, renderMultiLayerGradientToDataURL, renderSvgBackgroundToDataURL, renderBlendedBackgroundToDataURL, renderRepeatingGradientToDataURL, parseRadialCenter, };
