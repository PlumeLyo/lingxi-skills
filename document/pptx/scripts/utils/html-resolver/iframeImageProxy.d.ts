/**
 * 跨域 iframe 图片代理
 *
 * 利用 CDN 上的跨域 iframe 绕过主页面 CSP 限制，
 * 代理获取外部图片资源。
 *
 * 通信协议：
 * - 主页面 → iframe：{ type: 'fetchImage', id, url }
 * - iframe → 主页面：{ type: 'fetchImageResult', id, status, dataUrl/error }
 * - iframe 就绪通知：{ type: 'elementCaptureReady' }
 */
/**
 * 销毁 iframe 代理，清理所有待处理请求。
 * 通常在整个转换任务完成后调用。
 */
declare function destroyImageProxy(): void;
/**
 * 通过跨域 iframe 代理获取外部图片并转换为 DataURL。
 * 利用 CDN iframe 的独立源绕过主页面 CSP 对外部域名的限制。
 *
 * @param url 图片的外部 URL
 * @returns 图片 DataURL
 */
declare function fetchImageViaProxy(url: string): Promise<string>;
export { fetchImageViaProxy, destroyImageProxy };
