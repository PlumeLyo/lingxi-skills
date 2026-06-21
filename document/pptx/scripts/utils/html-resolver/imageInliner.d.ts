/**
 * 外部图片内联器
 *
 * 将 HTML 字符串中的外部图片 URL 替换为 data URL，
 * 通过跨域 CDN iframe 代理绕过主页面 CSP 对外部域名的限制。
 *
 * 白名单域名（匹配主页面 CSP img-src）的图片不做处理，
 * 仅对非白名单域名的图片通过 iframe 代理获取。
 */
declare function inlineExternalImages(htmlStr: string): Promise<string>;
export { inlineExternalImages };
