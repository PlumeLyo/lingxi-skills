/**
 * 跨域 iframe 截图代理
 *
 * 将 html2canvas 的执行委托给 CDN 上的跨域 iframe，
 * 利用浏览器的 Site Isolation 机制使截图在独立进程中执行，
 * 避免阻塞主页面的用户交互和渲染。
 *
 * 通信协议：
 * - 主页面 → iframe：{ type: 'elementCapture', id, html, width, height }
 * - iframe → 主页面：{ type: 'elementCaptureResult', id, status, dataUrl/error }
 * - iframe 就绪通知：{ type: 'elementCaptureReady' }
 */
/**
 * 通过跨域 iframe 执行 html2canvas 截图。
 *
 * @param html 要截图的 HTML 片段（含内联样式）
 * @param width 截图宽度（像素）
 * @param height 截图高度（像素）
 * @returns 截图 DataURL
 */
declare function captureInIframe(html: string, width: number, height: number): Promise<string>;
/**
 * 销毁 iframe 代理，清理所有待处理请求。
 * 通常在整个转换任务完成后调用。
 */
declare function destroyCaptureProxy(): void;
/**
 * 通过跨域 iframe 代理获取外部图片并转换为 DataURL。
 * 利用 CDN iframe 的独立源绕过主页面 CSP 对外部域名的限制。
 *
 * @param url 图片的外部 URL
 * @returns 图片 DataURL
 */
declare function fetchImageViaProxy(url: string): Promise<string>;
export { captureInIframe, fetchImageViaProxy, destroyCaptureProxy };
