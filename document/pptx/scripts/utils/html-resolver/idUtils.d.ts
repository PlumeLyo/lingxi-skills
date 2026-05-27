/**
 * 元素 ID 生成器
 *
 * 通过时间戳 + 递增计数器生成唯一元素 ID，
 * 每次调用 resolveHtml 前需 resetIdCounter 重置计数器。
 */
/**
 * 生成唯一 ID（时间戳 + 递增计数）
 * @returns 唯一 ID 字符串
 */
declare function generateId(): string;
/** 重置 ID 计数器 */
declare function resetIdCounter(): void;
export { generateId, resetIdCounter };
