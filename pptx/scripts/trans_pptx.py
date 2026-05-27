"""
HTML 转 PPT 工具
将 HTML 字符串解析为结构化数据，提取样式、位置、字体等信息，并将图表转换为图片
"""

import json
import base64
import tempfile
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class ElementStyle:
    """元素样式信息"""
    # 位置和尺寸
    x: float
    y: float
    width: float
    height: float

    # 字体相关
    font_family: str = ""
    font_size: str = ""
    font_weight: str = ""
    font_style: str = ""
    line_height: str = ""
    letter_spacing: str = ""

    # 颜色
    color: str = ""
    background_color: str = ""
    border_color: str = ""

    # 边框
    border_width: str = ""
    border_style: str = ""
    border_radius: str = ""

    # 间距
    padding: str = ""
    margin: str = ""

    # 文本
    text_align: str = ""
    text_decoration: str = ""
    text_transform: str = ""

    # 显示
    display: str = ""
    opacity: str = ""
    z_index: str = ""

    # 其他
    box_shadow: str = ""
    transform: str = ""


@dataclass
class ElementInfo:
    """元素信息"""
    tag: str  # 标签名
    text: str  # 文本内容
    html: str  # 内部HTML
    classes: List[str]  # class列表
    attributes: Dict[str, str]  # 属性
    style: ElementStyle  # 计算后的样式
    children: List['ElementInfo']  # 子元素
    is_chart: bool = False  # 是否是图表
    chart_image: Optional[str] = None  # 图表的base64图片


@dataclass
class PageInfo:
    """页面信息"""
    background_color: str
    background_image: str
    width: float
    height: float
    elements: List[ElementInfo]


# JavaScript 脚本：提取页面元素信息
EXTRACT_ELEMENTS_JS = """
() => {
    /**
     * 判断元素是否是图表
     */
    function isChart(element) {
        // 检查是否是 canvas
        if (element.tagName === 'CANVAS') {
            return true;
        }

        // 检查是否包含常见图表库的类名
        const chartClasses = ['chart', 'echarts', 'highcharts', 'chartjs', 'plotly', 'g2'];
        const classList = element.className.toLowerCase();
        for (const cls of chartClasses) {
            if (classList.includes(cls)) {
                return true;
            }
        }

        // 检查是否包含 SVG 图表
        if (element.tagName === 'SVG' || element.querySelector('svg')) {
            const svgContent = element.outerHTML.toLowerCase();
            if (svgContent.includes('chart') || svgContent.includes('graph') ||
                svgContent.includes('plot') || svgContent.includes('axis')) {
                return true;
            }
        }

        return false;
    }

    async function captureElementBackground(element) {
        try {
            const computed = window.getComputedStyle(element);
            const rect = element.getBoundingClientRect();

            const cssWidth  = Math.round(rect.width  || element.offsetWidth  || 1);
            const cssHeight = Math.round(rect.height || element.offsetHeight || 1);

            // ── 提取全部背景相关属性 ──────────────────────────────────────
            const bgProps = {
                backgroundColor:        computed.backgroundColor,
                backgroundImage:        computed.backgroundImage,
                backgroundSize:         computed.backgroundSize,
                backgroundPosition:     computed.backgroundPosition,
                backgroundRepeat:       computed.backgroundRepeat,
                backgroundOrigin:       computed.backgroundOrigin,
                backgroundClip:         computed.backgroundClip,
                backgroundAttachment:   computed.backgroundAttachment,
                borderRadius:           computed.borderRadius,
            };

            // ── 优先路径：html2canvas 镜像截图（支持渐变/图片/纯色）──────
            if (typeof html2canvas !== 'undefined') {
                // 创建镜像 div，仅含背景样式，无任何子节点
                const mirror = document.createElement('div');
                Object.assign(mirror.style, {
                    position:           'fixed',
                    left:               '-99999px',   // 移出可视区域，避免闪烁
                    top:                '0px',
                    width:              cssWidth  + 'px',
                    height:             cssHeight + 'px',
                    // 背景属性全量复制
                    backgroundColor:    bgProps.backgroundColor,
                    backgroundImage:    bgProps.backgroundImage,
                    backgroundSize:     bgProps.backgroundSize,
                    backgroundPosition: bgProps.backgroundPosition,
                    backgroundRepeat:   bgProps.backgroundRepeat,
                    backgroundOrigin:   bgProps.backgroundOrigin,
                    backgroundClip:     bgProps.backgroundClip,
                    backgroundAttachment: 'scroll',   // fixed 附着在截图容器内无意义
                    borderRadius:       bgProps.borderRadius,
                    // 确保不被其他样式污染
                    margin:   '0',
                    padding:  '0',
                    border:   'none',
                    boxShadow: 'none',
                    opacity:  '1',
                    overflow: 'hidden',
                    isolation: 'isolate',       // 独立堆叠上下文，避免混合
                    zIndex:   '-2147483648',    // 置于最底层
                });

                document.body.appendChild(mirror);
                try {
                    const snapshotCanvas = await html2canvas(mirror, {
                        backgroundColor: null,   // 不填充白色底色
                        scale: window.devicePixelRatio || 1,
                        useCORS: true,
                        allowTaint: false,
                        // 截图范围精确限定到镜像 div，不捕获其他元素
                        width:  cssWidth,
                        height: cssHeight,
                        x: 0,
                        y: 0,
                        scrollX: 0,
                        scrollY: 0,
                        ignoreElements: (el) => el !== mirror,
                    });
                    return snapshotCanvas.toDataURL('image/png');
                } finally {
                    // 无论成功/失败都立即清理，保证无副作用
                    document.body.removeChild(mirror);
                }
            }
        } catch (e) {
            console.error('Failed to capture element background:', e);
            return null;
        }
    }

    /**
     * 将元素转换为图片 (base64)
     */
    async function elementToImage(element) {
        try {
            // 如果是 canvas，直接获取 base64
            if (element.tagName === 'CANVAS') {
                return element.toDataURL('image/png');
            }

            // 对于其他元素，使用 html2canvas 或返回空
            // 注意：这里需要预先加载 html2canvas 库
            if (typeof html2canvas !== 'undefined') {
                const canvas = await html2canvas(element, {
                    backgroundColor: null,
                    scale: 2
                });
                return canvas.toDataURL('image/png');
            }

            return null;
        } catch (e) {
            console.error('Failed to convert element to image:', e);
            return null;
        }
    }

    /**
     * 获取元素的计算样式
     */
    async function getElementStyle(element) {
        const computed = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        let backgroundImage = 'none';
        if ( (computed.clipPath !== 'none') || (computed.backgroundImage && computed.backgroundImage !== 'none') ) {
            backgroundImage = await captureElementBackground(element);
        }

        return {
            // 位置和尺寸
            x: rect.left + window.scrollX,
            y: rect.top + window.scrollY,
            width: rect.width,
            height: rect.height,

            // 字体
            font_family: computed.fontFamily,
            font_size: computed.fontSize,
            font_weight: computed.fontWeight,
            font_style: computed.fontStyle,
            line_height: computed.lineHeight,
            letter_spacing: computed.letterSpacing,

            // 颜色
            color: computed.color,
            background_color: computed.backgroundColor,
            background_image: backgroundImage,
            border_color: computed.borderColor,

            // 边框
            border_width: computed.borderWidth,
            border_style: computed.borderStyle,
            border_radius: computed.borderRadius,

            // 间距
            padding: computed.padding,
            margin: computed.margin,

            // 文本
            text_align: computed.textAlign,
            text_decoration: computed.textDecoration,
            text_transform: computed.textTransform,

            // 显示
            display: computed.display,
            opacity: computed.opacity,
            z_index: computed.zIndex,

            // 其他
            box_shadow: computed.boxShadow,
            transform: computed.transform
        };
    }

    /**
     * 递归提取元素信息
     */
    async function extractElement(element, depth = 0, maxDepth = 10) {
        if (depth > maxDepth) {
            return null;
        }

        // 跳过 script、style、meta 等标签
        const skipTags = ['SCRIPT', 'STYLE', 'META', 'LINK', 'NOSCRIPT'];
        if (skipTags.includes(element.tagName)) {
            return null;
        }

        // 跳过不可见元素
        const computed = window.getComputedStyle(element);
        if (computed.display === 'none' || computed.visibility === 'hidden') {
            return null;
        }

        const isChartElement = isChart(element);

        // 提取基本信息
        const info = {
            tag: element.tagName.toLowerCase(),
            text: element.innerText || '',
            html: element.innerHTML,
            classes: Array.from(element.classList),
            attributes: {},
            style: await getElementStyle(element),
            children: [],
            is_chart: isChartElement,
            chart_image: null
        };

        // 提取属性
        for (const attr of element.attributes) {
            info.attributes[attr.name] = attr.value;
        }

        // 如果是图表，转换为图片
        if (isChartElement) {
            info.chart_image = await elementToImage(element);
            // 图表不再递归子元素
            return info;
        }

        // 递归处理子元素
        for (const child of element.children) {
            const childInfo = await extractElement(child, depth + 1, maxDepth);
            if (childInfo) {
                info.children.push(childInfo);
            }
        }

        return info;
    }

    /**
     * 提取页面信息
     */
    async function extractPageInfo() {
        const body = document.body;
        const html = document.documentElement;
        const bodyStyle = window.getComputedStyle(body);

        const pageInfo = {
            background_color: bodyStyle.backgroundColor,
            background_image: bodyStyle.backgroundImage,
            width: Math.max(
                body.scrollWidth,
                body.offsetWidth,
                html.clientWidth,
                html.scrollWidth,
                html.offsetWidth
            ),
            height: Math.max(
                body.scrollHeight,
                body.offsetHeight,
                html.clientHeight,
                html.scrollHeight,
                html.offsetHeight
            ),
            elements: []
        };

        // 提取所有直接子元素
        for (const child of body.children) {
            const elementInfo = await extractElement(child);
            if (elementInfo) {
                pageInfo.elements.push(elementInfo);
            }
        }

        // 后处理：如果存在背景图，清空 body 子元素后对 body 截图，获得真实的 background_image
        if (pageInfo.background_image && pageInfo.background_image !== 'none') {
            if (typeof html2canvas !== 'undefined') {
                // 移除所有子节点
                while (body.firstChild) {
                    body.removeChild(body.firstChild);
                }
                try {
                    const bgCanvas = await html2canvas(body, {
                        backgroundColor: null,
                        scale: window.devicePixelRatio || 1,
                        useCORS: true,
                        allowTaint: false,
                        width: pageInfo.width,
                        height: pageInfo.height,
                        scrollX: 0,
                        scrollY: 0,
                    });
                    pageInfo.background_image = bgCanvas.toDataURL('image/png');
                } catch (e) {
                    console.error('Failed to capture body background:', e);
                }
            }
        }

        return pageInfo;
    }

    // 执行提取
    return extractPageInfo();
}
"""


def extract_html_structure(
    html_content: str,
    timeout: int = 30000,
    viewport_width: int = 1310,
    viewport_height: int = 880,
    load_html2canvas: bool = True
) -> Dict[str, Any]:
    """
    使用浏览器解析HTML并提取结构化信息

    Args:
        html_content: HTML字符串
        timeout: 页面加载超时时间（毫秒）
        viewport_width: 视口宽度
        viewport_height: 视口高度
        load_html2canvas: 是否加载 html2canvas 库用于图表转图片

    Returns:
        包含页面信息的字典
    """
    # 配置 Chrome 无头浏览器选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--window-size={viewport_width},{viewport_height}")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 设置页面加载超时（秒）
        driver.set_page_load_timeout(timeout / 1000)

        # 将 HTML 写入临时文件，通过 file:// 协议加载，保证脚本执行
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', delete=False, encoding='utf-8'
        ) as tmp:
            # 如果需要，在 HTML <head> 中注入 html2canvas 脚本标签
            if load_html2canvas:
                html2canvas_tag = (
                    '<script src="https://cdn.jsdelivr.net/npm/'
                    'html2canvas@1.4.1/dist/html2canvas.min.js"></script>'
                )
                # 注入到 <head> 或 <body> 之前
                if '<head>' in html_content:
                    patched = html_content.replace('<head>', f'<head>{html2canvas_tag}', 1)
                elif '<html>' in html_content:
                    patched = html_content.replace('<html>', f'<html><head>{html2canvas_tag}</head>', 1)
                else:
                    patched = html2canvas_tag + html_content
            else:
                patched = html_content

            tmp.write(patched)
            tmp_path = tmp.name

        try:
            driver.get(f'file:///{tmp_path.replace(os.sep, "/")}')

            # 等待页面稳定（networkidle 替代：等待 document.readyState == 'complete'）
            WebDriverWait(driver, timeout / 1000).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # 额外等待 1 秒确保动态内容渲染完成
            driver.implicitly_wait(1)

            # 执行 JavaScript 提取信息（async 脚本）
            driver.set_script_timeout(timeout / 1000)
            result = driver.execute_async_script(
                f"""
                var callback = arguments[arguments.length - 1];
                ({EXTRACT_ELEMENTS_JS})().then(callback).catch(function(e) {{
                    callback(null);
                }});
                """
            )
        finally:
            os.unlink(tmp_path)

        return result

    finally:
        driver.quit()

