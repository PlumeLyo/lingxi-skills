import { PPTElement } from '../../types/slides';
import { ResolveContext } from './types';
/**
 * 获取普通文档流元素应使用的 z-index
 * @param ctx 当前解析上下文
 */
declare function getFlowLayerZIndex(ctx: ResolveContext): number;
/**
 * 获取内联内容（文本）层级的 z-index。
 *
 * 文本必须始终高于同一元素的背景。背景的 zIndex 由 resolveNode
 * 的 assignZIndex 统一赋为 ctx.currentZIndex，因此文本层级取
 * 「固定内联波段」与「currentZIndex + 微量偏移」的较大值，
 * 保证无论元素处于普通流还是 positioned 层都不会被自身背景覆盖。
 *
 * @param ctx 当前解析上下文
 */
declare function getInlineContentLayerZIndex(ctx: ResolveContext): number;
/**
 * 获取已定位但 z-index: auto 的元素应使用的 z-index
 * @param ctx 当前解析上下文
 */
declare function getPositionedAutoLayerZIndex(ctx: ResolveContext): number;
/**
 * 为显式 z-index 元素派生新的层叠上下文。
 * 在父级波段中分配一段独立区间，子元素的 z-index 将限定在此区间内。
 * @param parentCtx 父解析上下文
 * @param zIndex 元素的 CSS z-index 值
 * @returns 新的子层叠上下文
 */
declare function deriveExplicitZIndexContext(parentCtx: ResolveContext, zIndex: number): ResolveContext;
/**
 * 判断子上下文是否创建了新的层叠上下文（base 或 size 发生了变化）
 * @param parentCtx 父上下文
 * @param childCtx 子上下文
 */
declare function isNewStackingContext(parentCtx: ResolveContext, childCtx: ResolveContext): boolean;
/**
 * 创建普通流子上下文，仅更新 currentZIndex 到流层级位置
 * @param ctx 父解析上下文
 */
declare function createChildFlowContext(ctx: ResolveContext): ResolveContext;
/**
 * 根据元素的 CSS position 和 z-index 推导子上下文。
 * - 已定位或 flex/grid 子项 + 显式 z-index → 创建全新层叠上下文
 * - 已定位 + auto → 提升到 positioned-auto 层级
 * - 其他（含 position:static 非 flex/grid 子项）→ 继承父上下文
 *
 * 注意：CSS 规范中 z-index 仅对定位元素和 flex/grid 子项生效，
 * position:static 的普通流元素即使声明了 z-index 也不会创建层叠上下文。
 * @param element DOM 元素
 * @param ctx 父解析上下文
 * @returns 派生后的子解析上下文
 */
declare function deriveChildContext(element: Element, ctx: ResolveContext): ResolveContext;
/**
 * 批量为新增的 PPT 元素分配 z-index（仅填充 undefined 的项）
 * @param results PPT 元素数组
 * @param startIdx 从此下标开始赋值
 * @param zIndex 要赋予的 z-index 值
 */
declare function assignZIndex(results: PPTElement[], startIdx: number, zIndex: number): void;
/**
 * 为伪元素产生的 PPT 元素应用其独立的 z-index。
 * 若伪元素声明了显式 z-index，则派生新层叠上下文并覆盖元素 z-index。
 * @param results PPT 元素数组
 * @param startIdx 伪元素产出元素的起始下标
 * @param ps 伪元素的计算样式
 * @param ctx 父解析上下文
 */
declare function applyPseudoZIndex(results: PPTElement[], startIdx: number, ps: CSSStyleDeclaration, ctx: ResolveContext): void;
export { applyPseudoZIndex, assignZIndex, deriveChildContext, getFlowLayerZIndex, getInlineContentLayerZIndex, getPositionedAutoLayerZIndex, deriveExplicitZIndexContext, isNewStackingContext, createChildFlowContext, };
