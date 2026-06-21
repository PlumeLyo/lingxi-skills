import { Gradient, PPTElement, ImageElementClip } from '../../types/slides';
import { ResolveContext } from './types';
interface ClipPathGeometryResult {
    customPath: string;
    customViewBox: [number, number];
    clip?: ImageElementClip;
}
interface RootBackgroundResult {
    background?: string | Gradient;
    overlays: ({
        type: "shape";
        id: string;
        left: number;
        top: number;
        width: number;
        height: number;
        rotate: number;
        viewBox: [number, number];
        path: string;
        fixedRatio: boolean;
        fill: string;
        gradient: Gradient;
        opacity?: number;
    } | {
        type: "image";
        id: string;
        left: number;
        top: number;
        width: number;
        height: number;
        rotate: number;
        fixedRatio: boolean;
        src: string;
        opacity?: number;
    })[];
}
/**
 * 从 CSS background-image 值中提取第一个 url(...) 地址。
 * 多层背景时按 CSS 层序（从前到后）返回首个匹配的 URL，
 * 渐变层（如 linear-gradient）会被跳过。
 * @param backgroundImage 元素的 computed backgroundImage 字符串
 * @returns 提取到的 URL 字符串，无 url() 层时返回 null
 */
declare function extractFirstBackgroundImageUrl(backgroundImage: string): string | null;
/**
 * 将 background-image url 解析为可用的图片 src（data URL 或原始 URL）。
 * 处理策略：blend 混合 → 截图 → 原始 URL 降级。
 * @param element    含背景图的 DOM 元素
 * @param imageUrl   提取到的背景图 URL
 * @returns { src: 图片地址, blended: 是否经过 blend 混合 }
 */
declare function resolveBackgroundImageSrc(element: Element, imageUrl: string): Promise<{
    src: string;
    blended: boolean;
}>;
/**
 * 解析根元素的背景色与渐变，返回幻灯片背景及可能的渐变覆盖层形状。
 * - 平铺渐变（background-size ≠ auto）：复用 captureUtils 渲染为图片覆盖层。
 * - 单渐变：与 background-color 合成后作为幻灯片背景。
 * - 多渐变：幻灯片背景设为纯色，各渐变作为全尺寸矩形覆盖层。
 */
declare function resolveRootBackground(root: Element, widthPt: number, heightPt: number, idGen: () => string): Promise<RootBackgroundResult>;
/**
 * 为容器元素（非终端消费、有子节点）生成 background-image: url() 的图片层。
 * 仅处理含 url() 且非纯 gradient 的背景图；纯色/gradient 背景已由
 * isShapeElement → appendShapeBackgroundArtifacts 处理。
 * 同时将 outline-rect 边框和 box-shadow 附着到图片元素上。
 */
declare function resolveContainerBackgroundImage(element: Element, ctx: ResolveContext, results: PPTElement[]): Promise<void>;
/**
 * 检测元素是否有 clip-path: polygon() 并解析为自定义几何信息。
 * 同时处理 background-size: cover/contain 的 srcRect 计算。
 */
declare function resolveClipPathImageGeometry(style: CSSStyleDeclaration, imageUrl: string, widthPt: number, heightPt: number, containerW: number, containerH: number): Promise<ClipPathGeometryResult | null>;
export { resolveRootBackground, extractFirstBackgroundImageUrl, resolveBackgroundImageSrc, resolveContainerBackgroundImage, resolveClipPathImageGeometry, };
export type { RootBackgroundResult, ClipPathGeometryResult };
