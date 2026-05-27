import { PPTElement } from '../../types/slides';
import { ResolveContext, RootRect } from './types';
/**
 * 检测 CSS float 子元素并修正非浮动兄弟产出的 PPT 元素位置。
 *
 * 在浏览器中 float 通过文字环绕实现排版，但 PPT 中每个元素绝对定位，
 * 非浮动块级元素的 getBoundingClientRect 会延伸到浮动元素下方，
 * 导致转换后文本与浮动图标重叠。此函数检测该场景并平移受影响元素。
 */
export declare function adjustForFloatLayout(childNodes: ChildNode[], childChunks: PPTElement[][], ctx: ResolveContext): void;
interface ElementRect {
    left: number;
    top: number;
    width: number;
    height: number;
}
/**
 * 将元素坐标裁剪到根容器（幻灯片画布）范围内。
 * 若元素右/下边界超出画布，等比缩放使其完全可见并调整位置。
 * 返回修正后的 { left, top, width, height }。
 * 若无溢出则返回原值。
 */
export declare function clampToSlide(rect: ElementRect, rootRect: RootRect): ElementRect;
export {};
