import { PPTElementOutline, PPTElementShadow } from '../../../types/slides';
import { XmlRenderable } from './types';
/**
 * 源矩形裁剪参数（对应 OOXML a:srcRect）
 * 各字段表示从原图对应边向内裁掉的百分比，值域 0~100。
 * 例如 left=10 表示裁掉原图左侧 10%。
 */
interface XmlImageSrcRect {
    left: number;
    top: number;
    right: number;
    bottom: number;
}
interface XmlImageInput {
    id: string;
    name?: string;
    x: number;
    y: number;
    w: number;
    h: number;
    rotation?: number;
    flipH?: boolean;
    flipV?: boolean;
    mediaFile: string;
    outline?: PPTElementOutline;
    shadow?: PPTElementShadow;
    opacity?: number;
    radius?: number;
    spreadOnlyGlowPt?: number;
    /** 源矩形裁剪，用于实现 object-fit: cover 等效果 */
    srcRect?: XmlImageSrcRect;
    /** 自定义几何裁剪路径（SVG path d），用于 clip-path polygon */
    customPath?: string;
    /** 自定义几何的 viewBox [width, height] */
    viewBox?: [number, number];
}
declare function createImageRenderable(input: XmlImageInput): XmlRenderable;
export type { XmlImageInput };
export { createImageRenderable };
