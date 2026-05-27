import { RgbColor } from './colorUtils';
/** 将 CSS opacity 字符串解析为 0~1 之间的数值 */
declare function parseCssOpacity(value: string | null | undefined): number | undefined;
/**
 * 沿 DOM 祖先链累积 opacity（不含自身，不超过 root 容器）。
 * CSS opacity 不被子元素继承到 computedStyle，但视觉上会层叠；
 * PPT 没有组级别 opacity，需手动相乘后写入每个元素。
 */
declare function getAncestorOpacity(element: Element, rootElement?: Element): number;
/** 将多个透明度相乘合并，结果为 1 时返回 undefined */
declare function combineOpacity(...values: Array<number | undefined>): number | undefined;
/**
 * 获取元素的完整视觉 opacity（自身 × 祖先链），返回 undefined 表示完全不透明。
 * 合并了 parseCssOpacity + getAncestorOpacity 的常见模式。
 */
declare function getElementOpacity(element: Element, rootElement?: Element): number | undefined;
/**
 * 拆分元素的 opacity 为自身和祖先两部分。
 */
declare function splitElementOpacity(element: Element, rootElement?: Element): {
    selfOpacity: number;
    ancestorOpacity: number;
};
/**
 * 沿 DOM 树向上查找第一个不透明的背景色。
 * 作为颜色预混合的目标背景色。
 */
declare function findAncestorOpaqueBackground(element: Element): RgbColor | null;
/**
 * 将祖先 opacity 预混合到颜色中。
 *
 * CSS opacity 对整个元素合成结果统一生效：同一 opacity 容器内的
 * 兄弟元素先不透明合成（互相遮挡），再整体降低透明度。
 * PPT 无组级 opacity，因此将祖先 opacity 预混合到颜色中，
 * 让形状保持不透明以维持正确的遮挡关系。
 *
 * 例外：当 opacity 容器的子元素互不重叠时，不存在遮挡问题，
 * 可跳过颜色预混合，直接将 ancestorOpacity 合并到元素 opacity 中，
 * 保持原始颜色不失真。
 *
 * @param element DOM 元素
 * @param hex 颜色 hex（不含 #）
 * @param colorAlpha 颜色自身的 alpha（0~1），默认 1
 * @returns 预混合后的颜色 hex、颜色 alpha（预混合后为 undefined）和仅含自身的 opacity
 */
declare function blendColorWithAncestorOpacity(element: Element, hex: string, colorAlpha?: number): {
    color: string;
    colorAlpha: number | undefined;
    opacity: number | undefined;
};
export { parseCssOpacity, combineOpacity, getAncestorOpacity, getElementOpacity, splitElementOpacity, findAncestorOpaqueBackground, blendColorWithAncestorOpacity, };
