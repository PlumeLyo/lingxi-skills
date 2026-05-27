import { PPTElement, PPTTableElement } from '../../types/slides';
import { ResolveContext } from './types';
/**
 * 判断元素是否是表格元素
 * @param element DOM 元素
 * @returns 是否为表格元素
 */
declare function isTableElement(element: Element): boolean;
/**
 * 解析表格元素
 * @param element 表格 DOM 元素
 * @param ctx 解析上下文
 * @returns PPT 表格元素，无法解析时返回 null
 */
declare function resolveTableElement(element: Element, ctx: ResolveContext): Promise<PPTTableElement | null>;
/**
 * 收集并解析表格单元格中的伪元素图标，
 * 基于 PPTX 表格的单元格几何计算图标位置，修正 border-spacing 偏移。
 */
declare function resolveTableCellIcons(table: HTMLTableElement, tableEl: PPTTableElement, ctx: ResolveContext): Promise<PPTElement[]>;
/**
 * 收集并解析表格单元格中带背景色的内联元素（如 tag/badge），
 * 将其生成为独立的形状叠加层，同时清理对应单元格的文本以避免重叠。
 * @param table 表格 DOM 元素
 * @param tableEl PPT 表格元素
 * @param ctx 解析上下文
 * @returns PPT 元素数组
 */
declare function resolveTableCellInlineShapes(table: HTMLTableElement, tableEl: PPTTableElement, ctx: ResolveContext): PPTElement[];
export { isTableElement, resolveTableElement, resolveTableCellIcons, resolveTableCellInlineShapes, };
