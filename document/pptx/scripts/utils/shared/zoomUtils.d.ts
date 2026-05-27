/**
 * 从 devicePixelRatio 中分离出浏览器缩放比例。
 *
 * devicePixelRatio = OS缩放 × 浏览器缩放，直接使用会把系统 DPI 缩放
 * 也当作浏览器缩放来修正（如 150% 系统缩放时 dpr=1.5 但浏览器实际 100%）。
 *
 * 策略：
 *   1. 按当前操作系统获取对应的标准 OS DPI 值集合
 *   2. 若 dpr 精确匹配某个标准 OS DPI 值 → 浏览器缩放为 100%
 *   3. 否则遍历 "OS缩放 × 浏览器缩放" 所有组合，取误差最小的匹配
 *   4. 同等误差时优先选择更接近 1 的缩放值（减少误修正）
 */
export declare function detectBrowserZoom(): number;
/**
 * 补偿浏览器缩放对隐藏 iframe 的影响。
 *
 * 浏览器缩放（如 150%）会改变字体在物理像素级的光栅化方式，
 * 导致字符宽度因子像素舍入差异而不同，使原本一行的文本换行。
 *
 * 策略：
 *   1. 通过 detectBrowserZoom 分离出浏览器缩放（排除 OS DPI 缩放）
 *   2. 在 iframe 的 <html> 上设置 `zoom: 1/browserZoom`，使物理渲染
 *      倍率与 100% 浏览器缩放一致
 *   3. 对 `getBoundingClientRect` / `Range.getBoundingClientRect`
 *      的返回值乘以 browserZoom，还原到未缩放的 CSS 像素坐标
 */
export declare function applyZoomCorrection(iframe: HTMLIFrameElement): void;
