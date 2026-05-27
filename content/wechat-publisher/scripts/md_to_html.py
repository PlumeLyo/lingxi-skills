#!/usr/bin/env python3
"""
微信公众号 Markdown → 内联样式 HTML 转换脚本

支持的语法：

【块级元素】
  ## 标题          → 蓝色大标题
  ### 标题         → 橙色小标题
  !!整段橙色加粗!!  → 橙色加粗段落（独立行）
  - 列表项         → 无序列表（橙色圆点）
  1. 列表项        → 有序列表（橙色序号）
  > 引用内容       → 灰底蓝边引用块（支持 <br> 换行）
  ```lang 代码```   → 深色背景代码块（支持语法高亮）
  ---              → 分隔线
  ~~注释文字~~      → 小号灰色注释（独立行）
  普通段落         → 灰色正文

【行内元素】
  **词句**         → 橙色加粗
  `code`           → 行内代码（灰底等宽）
  ==文字==         → 橙色字（默认）
  ==🔴文字==       → 对应颜色字（🔴🟠🟡🟢🔵🟣⚫️⚪️）
  ==🟥文字==       → 对应颜色底（🟥🟧🟨🟩🟦🟪⬛⬜）
  ==🔴🟥文字==     → 字色+底色组合

【图片】
  ![alt](路径)     → 本地图片自动转 base64 内嵌；网络图片直接引用

【Web 端】
  输出 HTML 带一键复制按钮，点击后复制 section 内容到剪贴板

使用方法：
    python3 scripts/md_to_html.py "推文/xxx/初稿.md"

输出：同目录下 初稿_formatted.html
"""

import re
import sys
import base64
import html as html_module
from pathlib import Path
from urllib.parse import unquote

# ============================================================
# 配置加载（读取 template.yaml，找不到则用内置默认值）
# ============================================================

def _load_config() -> dict:
    """
    查找顺序：
    1. 脚本同目录下的 template.yaml
    2. 项目根目录 排版要求/template.yaml（向上查找直到找到或到根目录）
    3. 内置默认值
    """
    candidates = [
        Path(__file__).parent / "template.yaml",
    ]
    # 向上最多找 4 层
    p = Path(__file__).parent
    for _ in range(4):
        p = p.parent
        candidates.append(p / "排版要求" / "template.yaml")

    for path in candidates:
        if path.exists():
            try:
                import yaml
                with open(path, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                print(f"  ✓ 读取配置：{path}")
                return cfg
            except ImportError:
                # PyYAML 未安装，尝试极简解析
                print("  ⚠️  未安装 PyYAML，使用内置默认配置（pip install pyyaml 可启用配置文件）")
                break
            except Exception as e:
                print(f"  ⚠️  配置文件解析失败（{e}），使用内置默认配置")
                break
    return {}

_CFG = _load_config()

def _c(section: str, key: str, default):
    """从配置中取值，缺失时返回 default"""
    return _CFG.get(section, {}).get(key, default)

# ============================================================
# 样式定义（从配置读取，配置缺失时用内置默认值）
# ============================================================

FONT_FAMILY = _c("fonts", "body", "mp-quote, 'PingFang SC', -apple-system-font, BlinkMacSystemFont, 'Helvetica Neue', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif")
MONO_FAMILY = _c("fonts", "mono", "'Menlo', 'Monaco', 'Courier New', monospace")

COLOR_ORANGE  = _c("colors", "primary",    "rgb(255, 104, 39)")
COLOR_BLUE    = _c("colors", "accent",     "rgb(0, 128, 255)")
COLOR_GRAY    = _c("colors", "text",       "rgb(100, 106, 115)")
COLOR_LGRAY   = _c("colors", "text_light", "rgb(153, 153, 153)")
COLOR_BG_GRAY = _c("colors", "bg_block",   "rgb(245, 245, 245)")
COLOR_BORDER  = _c("colors", "border",     "rgb(230, 230, 230)")

_fs_body      = _c("font_size", "body",        16)
_fs_h2        = _c("font_size", "h2",          18)
_fs_h3        = _c("font_size", "h3",          16)
_fs_note      = _c("font_size", "note",        14)
_fs_code      = _c("font_size", "code",        13)
_fs_code_inline = _c("font_size", "code_inline", 13)

_lh_body      = _c("spacing", "line_height_body",  2.0)
_lh_head      = _c("spacing", "line_height_head",  1.6)
_lh_quote     = _c("spacing", "line_height_quote", 1.8)
_pg_gap       = _c("spacing", "paragraph_gap",     15)
_h2_mt        = _c("spacing", "h2_margin_top",     30)
_h3_mt        = _c("spacing", "h3_margin_top",     20)

_max_width    = _c("layout", "max_width", 677)
_padding      = _c("layout", "padding",   20)

FEATURE_COPY_BUTTON = _c("features", "copy_button", True)

STYLES = {
    "p":            f'style="margin: 0px 0px {_pg_gap}px 0px; padding: 0px; outline: 0px; max-width: 100%; clear: both; min-height: 20px; word-break: break-all; color: {COLOR_GRAY}; font-size: {_fs_body}px; line-height: {_lh_body};"',
    "span":         f'style="font-size: {_fs_body}px; color: {COLOR_GRAY}; font-family: {FONT_FAMILY}; white-space: pre-wrap;"',
    "bold_inline":  f'style="font-size: {_fs_body}px; font-weight: bold; color: {COLOR_ORANGE}; font-family: {FONT_FAMILY};"',
    "hb":           f'style="font-size: {_fs_body}px; font-weight: bold; color: {COLOR_ORANGE}; font-family: {FONT_FAMILY}; white-space: pre-wrap;"',
    "h2":           f'style="margin: {_h2_mt}px 0px 15px 0px; padding: 0px; font-size: {_fs_h2}px; font-weight: bold; color: {COLOR_BLUE}; line-height: {_lh_head};"',
    "h3":           f'style="margin: {_h3_mt}px 0px 10px 0px; padding: 0px; font-size: {_fs_h3}px; font-weight: bold; color: {COLOR_BLUE}; line-height: {_lh_head};"',
    "blockquote":   f'style="margin: 20px 0px; padding: 15px 20px; background-color: {COLOR_BG_GRAY}; border-left: 4px solid {COLOR_BLUE}; font-size: 15px; color: {COLOR_GRAY}; line-height: {_lh_quote};"',
    "blockquote_p": f'style="margin: 0px; padding: 0px; font-family: {FONT_FAMILY};"',
    "hr":           f'style="margin: 25px 0px; border: none; border-top: 1px solid {COLOR_BORDER};"',
    "note":         f'style="margin: 20px 0px 0px 0px; padding: 0px; font-size: {_fs_note}px; color: {COLOR_LGRAY}; line-height: {_lh_quote};"',
    "img":          'style="max-width: 100%; height: auto; display: block; margin: 15px 0;"',
    "section":      f'style="max-width: {_max_width}px; margin: 0 auto; background-color: #fff; padding: {_padding}px; font-family: {FONT_FAMILY};"',
    "body":         f'style="margin: 0; padding: {_padding}px; background-color: #f5f5f5;"',
    "table":        'style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 15px;"',
    "th":           f'style="padding: 10px 14px; background-color: {COLOR_BLUE}; color: #fff; font-weight: bold; text-align: center; border: 1px solid rgb(0, 100, 220);"',
    "td":           f'style="padding: 10px 14px; color: {COLOR_GRAY}; border: 1px solid rgb(210, 215, 220); vertical-align: top; line-height: 1.7;"',
    "td_alt":       f'style="padding: 10px 14px; color: {COLOR_GRAY}; border: 1px solid rgb(210, 215, 220); vertical-align: top; line-height: 1.7; background-color: rgb(248, 249, 250);"',
}

# ============================================================
# 颜色 emoji 映射
# ============================================================

FONT_COLORS = {
    "🔴": "rgb(194, 28, 19)",
    "🟠": "rgb(255, 104, 39)",
    "🟡": "rgb(209, 163, 0)",
    "🟢": "rgb(7, 134, 84)",
    "🔵": "rgb(0, 128, 255)",
    "🟣": "rgb(140, 60, 200)",
    "⚫": "rgb(60, 60, 60)",
    "⚫️": "rgb(60, 60, 60)",
    "⚪": "rgb(153, 153, 153)",
    "⚪️": "rgb(153, 153, 153)",
}

BG_COLORS = {
    "🟥": "rgb(255, 200, 200)",
    "🟧": "rgb(255, 228, 196)",
    "🟨": "rgb(255, 249, 180)",
    "🟩": "rgb(200, 240, 210)",
    "🟦": "rgb(200, 225, 255)",
    "🟪": "rgb(230, 210, 255)",
    "⬛": "rgb(60, 60, 60)",
    "⬜": "rgb(230, 230, 230)",
}

# ============================================================
# 代码语法高亮（轻量级，内联样式）
# ============================================================

# 各语言 token 颜色方案（浅色 GitHub 风格）
CODE_COLORS = {
    "keyword":  "rgb(207, 34, 46)",     # 红色：关键字
    "string":   "rgb(14, 118, 50)",     # 绿色：字符串
    "comment":  "rgb(140, 149, 159)",   # 灰色：注释
    "number":   "rgb(5, 80, 174)",      # 蓝色：数字
    "builtin":  "rgb(111, 66, 193)",    # 紫色：内置/类型
    "operator": "rgb(60, 80, 100)",     # 深灰：操作符
    "decorator":"rgb(207, 34, 46)",     # 红色：装饰器
    "default":  "rgb(36, 41, 47)",      # 默认文字色（深色）
}

# 语言 → token 规则（正则, 颜色key, 是否保留原文）
LANG_RULES = {
    "python": [
        (r'#[^\n]*',                                    "comment"),
        (r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'',        "string"),
        (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',     "string"),
        (r'@\w+',                                        "decorator"),
        (r'\b(def|class|import|from|return|if|elif|else|for|while|in|not|and|or|is|None|True|False|try|except|finally|with|as|pass|break|continue|raise|lambda|yield|async|await)\b', "keyword"),
        (r'\b(print|len|range|str|int|float|list|dict|set|tuple|bool|type|open|super|self|cls)\b', "builtin"),
        (r'\b\d+\.?\d*\b',                               "number"),
        (r'[+\-*/=<>!&|^~%]+',                          "operator"),
    ],
    "javascript": [
        (r'//[^\n]*',                                    "comment"),
        (r'/\*[\s\S]*?\*/',                              "comment"),
        (r'`(?:\\.|[^`\\])*`',                           "string"),
        (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',     "string"),
        (r'\b(const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|new|this|class|extends|import|export|default|from|async|await|try|catch|finally|throw|typeof|instanceof|in|of|null|undefined|true|false)\b', "keyword"),
        (r'\b(console|Math|Object|Array|String|Number|Boolean|Promise|fetch|setTimeout|setInterval|JSON|window|document)\b', "builtin"),
        (r'\b\d+\.?\d*\b',                               "number"),
        (r'[+\-*/=<>!&|^~%?:]+',                        "operator"),
    ],
    "typescript": [
        (r'//[^\n]*',                                    "comment"),
        (r'/\*[\s\S]*?\*/',                              "comment"),
        (r'`(?:\\.|[^`\\])*`',                           "string"),
        (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',     "string"),
        (r'\b(const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|new|this|class|extends|import|export|default|from|async|await|try|catch|finally|throw|typeof|instanceof|in|of|null|undefined|true|false|type|interface|enum|namespace|declare|abstract|implements|readonly|private|public|protected|as|keyof|typeof)\b', "keyword"),
        (r'\b(string|number|boolean|any|void|never|unknown|object|Array|Promise|Record|Partial|Required|Readonly)\b', "builtin"),
        (r'\b\d+\.?\d*\b',                               "number"),
        (r'[+\-*/=<>!&|^~%?:]+',                        "operator"),
    ],
    "bash": [
        (r'#[^\n]*',                                     "comment"),
        (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',     "string"),
        (r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|export|local|echo|exit|in|true|false)\b', "keyword"),
        (r'\$\{?[\w@#?*!]+\}?',                         "builtin"),
        (r'\b\d+\b',                                     "number"),
        (r'[|&;<>]+',                                    "operator"),
    ],
    "yaml": [
        (r'#[^\n]*',                                     "comment"),
        (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',     "string"),
        (r'^(\s*[\w\-]+)(?=\s*:)',                       "keyword"),
        (r'\b(true|false|null|yes|no)\b',                "builtin"),
        (r'\b\d+\.?\d*\b',                               "number"),
        (r'[:\-\[\]{}|>]+',                              "operator"),
    ],
    "json": [
        (r'"(?:\\.|[^"\\])*"(?=\s*:)',                   "keyword"),
        (r'"(?:\\.|[^"\\])*"',                           "string"),
        (r'\b(true|false|null)\b',                       "builtin"),
        (r'\b-?\d+\.?\d*(?:[eE][+-]?\d+)?\b',           "number"),
        (r'[{}\[\]:,]+',                                 "operator"),
    ],
    "css": [
        (r'/\*[\s\S]*?\*/',                              "comment"),
        (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',     "string"),
        (r'[.#]?[\w-]+(?=\s*\{)',                        "keyword"),
        (r'(?<=:\s)[\w-]+',                              "builtin"),
        (r'#[0-9a-fA-F]{3,8}\b',                        "string"),
        (r'\b\d+\.?\d*(?:px|em|rem|%|vh|vw|s|ms)?\b',  "number"),
        (r'[:;{}()]+',                                   "operator"),
    ],
    "html": [
        (r'<!--[\s\S]*?-->',                             "comment"),
        (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',     "string"),
        (r'</?\w[\w-]*',                                 "keyword"),
        (r'[\w-]+=',                                     "builtin"),
        (r'[<>/=]+',                                     "operator"),
    ],
}

# 无特定规则的语言用通用规则
LANG_RULES["sh"]   = LANG_RULES["bash"]
LANG_RULES["js"]   = LANG_RULES["javascript"]
LANG_RULES["ts"]   = LANG_RULES["typescript"]
LANG_RULES["py"]   = LANG_RULES["python"]


def highlight_code(code: str, lang: str) -> str:
    """对代码做语法高亮，返回带 span 的 HTML 字符串（已 escape）"""
    lang = lang.lower().strip()
    rules = LANG_RULES.get(lang)

    if not rules:
        # 无规则语言：直接 escape，不高亮
        return html_module.escape(code)

    # 标记哪些字符区间已被染色（避免重叠）
    length = len(code)
    colors = [None] * length  # 每个字符对应的颜色key

    for pattern, color_key in rules:
        for m in re.finditer(pattern, code, re.MULTILINE):
            start, end = m.start(), m.end()
            # 只染未被染色的区间
            if all(colors[j] is None for j in range(start, end)):
                for j in range(start, end):
                    colors[j] = color_key

    # 按颜色区间生成 HTML
    result = []
    i = 0
    while i < length:
        color_key = colors[i]
        j = i + 1
        while j < length and colors[j] == color_key:
            j += 1
        segment = html_module.escape(code[i:j])
        if color_key:
            color = CODE_COLORS[color_key]
            result.append(f'<span style="color: {color};">{segment}</span>')
        else:
            result.append(f'<span style="color: {CODE_COLORS["default"]};">{segment}</span>')
        i = j

    return ''.join(result)


# ============================================================
# 行内元素处理
# ============================================================

def process_inline(text: str) -> str:
    """处理行内元素：`code`、==高亮==、**加粗**"""

    # 行内代码 `code`（先处理，避免内部内容被其他规则误处理）
    def replace_inline_code(m):
        code = html_module.escape(m.group(1))
        style = (
            f'background-color: rgb(235, 236, 240); '
            f'color: rgb(80, 90, 105); '
            f'font-family: {MONO_FAMILY}; '
            f'font-size: {_fs_code_inline}px; '
            f'padding: 1px 5px; '
            f'border-radius: 3px; '
            f'white-space: nowrap;'
        )
        return f'<code style="{style}">{code}</code>'

    # 用占位符保护行内代码，避免被后续规则处理
    placeholders = {}
    placeholder_idx = [0]

    def protect_inline_code(m):
        key = f'\x00CODE{placeholder_idx[0]}\x00'
        placeholder_idx[0] += 1
        placeholders[key] = replace_inline_code(m)
        return key

    text = re.sub(r'`([^`]+)`', protect_inline_code, text)

    # ==高亮== 处理（支持颜色 emoji 前缀）
    def replace_highlight(m):
        inner = m.group(1)
        font_color = None
        bg_color = None

        i = 0
        while i < len(inner):
            matched = False
            for emoji_len in [2, 1]:
                candidate = inner[i:i+emoji_len]
                if candidate in FONT_COLORS and font_color is None:
                    font_color = FONT_COLORS[candidate]
                    i += emoji_len
                    matched = True
                    break
                elif candidate in BG_COLORS and bg_color is None:
                    bg_color = BG_COLORS[candidate]
                    i += emoji_len
                    matched = True
                    break
            if not matched:
                break

        content = inner[i:]
        style_parts = [f"color: {font_color or COLOR_ORANGE};"]
        if bg_color:
            style_parts.append(f"background-color: {bg_color}; padding: 0 2px; border-radius: 2px;")
        style = " ".join(style_parts)
        return f'<span style="{style}">{content}</span>'

    text = re.sub(r'==([\s\S]+?)==', replace_highlight, text)

    # **加粗** → 橙色加粗
    text = re.sub(
        r'\*\*(.+?)\*\*',
        lambda m: f'<span {STYLES["bold_inline"]}>{m.group(1)}</span>',
        text
    )

    # 还原行内代码占位符
    for key, val in placeholders.items():
        text = text.replace(key, val)

    # MD 链接 [文字](url) → 蓝色可点击链接
    text = re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        lambda m: f'<a href="{m.group(2)}" style="color: {COLOR_BLUE}; text-decoration: none;">{m.group(1)}</a>',
        text
    )

    return text


# ============================================================
# 块级元素渲染
# ============================================================

def render_p(text: str) -> str:
    return f'<p {STYLES["p"]}><span {STYLES["span"]}>{process_inline(text)}</span></p>'

def render_hb(text: str) -> str:
    return f'<p {STYLES["p"]}><span {STYLES["hb"]}>{process_inline(text)}</span></p>'

def render_bold_line(text: str) -> str:
    """整行橙色加粗段落（**整行** 语法）"""
    return f'<p {STYLES["p"]}><span {STYLES["bold_inline"]}>{process_inline(text)}</span></p>'

def render_h2(text: str) -> str:
    return f'<h2 {STYLES["h2"]}>{text}</h2>'

def render_h3(text: str) -> str:
    return f'<p {STYLES["p"]}><span {STYLES["h3"]}>{process_inline(text)}</span></p>'

def render_blockquote(text: str) -> str:
    inner = process_inline(text)
    return (
        f'<blockquote {STYLES["blockquote"]}>\n'
        f'    <p {STYLES["blockquote_p"]}>{inner}</p>\n'
        f'</blockquote>'
    )

def render_hr() -> str:
    return f'<hr {STYLES["hr"]}>'

def render_note(text: str) -> str:
    return f'<p {STYLES["note"]}><span style="font-family: {FONT_FAMILY};">{process_inline(text)}</span></p>'

def render_ul(items: list) -> str:
    parts = []
    for item in items:
        parts.append(
            f'<p {STYLES["p"]}><span {STYLES["span"]}>'
            f'<span style="color: {COLOR_ORANGE}; margin-right: 6px;">•</span>'
            f'{process_inline(item)}</span></p>'
        )
    return '\n'.join(parts)

def render_ol(items: list) -> str:
    parts = []
    for i, item in enumerate(items, 1):
        parts.append(
            f'<p {STYLES["p"]}><span {STYLES["span"]}>'
            f'<span style="color: {COLOR_ORANGE}; font-weight: bold; margin-right: 6px;">{i}.</span>'
            f'{process_inline(item)}</span></p>'
        )
    return '\n'.join(parts)

def render_codeblock(code: str, lang: str = "") -> str:
    """代码块：
    - 有语言标注 → 深色背景 + 等宽字体 + 语法高亮 + 语言标签
    - 无语言标注 → 灰色背景 + 普通字体（说明性文本块）
    """
    # 无语言标注：当作说明性文本框，普通字体渲染
    if not lang:
        lines = code.strip().split('\n')
        paras = []
        for ln in lines:
            escaped = html_module.escape(ln) if ln.strip() else '&nbsp;'
            paras.append(
                f'<p style="margin: 0 0 4px 0; padding: 0; '
                f'font-size: 15px; color: {COLOR_GRAY}; '
                f'font-family: {FONT_FAMILY}; line-height: 1.8;">'
                f'{process_inline(escaped)}</p>'
            )
        inner = '\n'.join(paras)
        return (
            f'<section style="margin: 16px 0px; padding: 16px 20px; '
            f'background-color: rgb(248, 249, 250); '
            f'border-radius: 6px; '
            f'border: 1px solid {COLOR_BORDER};">'
            f'{inner}'
            f'</section>'
        )

    # 有语言标注：浅色代码块（GitHub 风格）
    highlighted = highlight_code(code, lang)
    highlighted = highlighted.replace('\n', '<br>')
    highlighted = re.sub(r'  ', '&nbsp;&nbsp;', highlighted)

    lang_label = (
        f'<span style="'
        f'position: absolute; top: 8px; right: 12px; '
        f'font-size: 11px; color: rgb(130, 140, 150); '
        f'font-family: {MONO_FAMILY}; '
        f'text-transform: uppercase; letter-spacing: 0.5px;'
        f'">{html_module.escape(lang)}</span>'
    )

    pre_style = (
        f'margin: 0px; padding: 0px; '
        f'font-family: {MONO_FAMILY}; '
        f'font-size: {_fs_code}px; '
        f'line-height: 1.7; '
        f'white-space: pre; word-break: normal; overflow-wrap: normal;'
    )

    return (
        f'<section style="position: relative; margin: 16px 0px; padding: 16px 20px; '
        f'background-color: rgb(246, 248, 250); border-radius: 6px; overflow-x: auto; '
        f'border: 1px solid rgb(210, 215, 220);">'
        f'{lang_label}'
        f'<p style="{pre_style}">{highlighted}</p>'
        f'</section>'
    )

def render_img(src: str, input_dir: Path = None) -> str:
    """图片渲染：本地图片转 base64，网络图片直接引用"""
    if not src.startswith(('http://', 'https://', 'data:')):
        # 本地图片：尝试转 base64（先 URL decode，兼容 %20 等编码）
        src_decoded = unquote(src)
        img_path = Path(src_decoded) if Path(src_decoded).is_absolute() else (input_dir / src_decoded if input_dir else Path(src_decoded))
        if img_path.exists():
            suffix = img_path.suffix.lower()
            mime_map = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.webp': 'image/webp', '.svg': 'image/svg+xml',
            }
            mime = mime_map.get(suffix, 'image/png')
            with open(img_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            src = f'data:{mime};base64,{b64}'
        else:
            print(f"  ⚠️  图片不存在：{img_path}")

    return f'<img src="{src}" {STYLES["img"]}/>'

def render_table(rows: list) -> str:
    html = f'<table {STYLES["table"]}>\n'
    for row_idx, row in enumerate(rows):
        html += '  <tr>\n'
        for cell in row:
            cell = cell.strip()
            if row_idx == 0:
                html += f'    <th {STYLES["th"]}>{cell}</th>\n'
            else:
                style = STYLES["td_alt"] if row_idx % 2 == 0 else STYLES["td"]
                html += f'    <td {style}>{cell}</td>\n'
        html += '  </tr>\n'
    html += '</table>'
    return html


# ============================================================
# 主解析器
# ============================================================

def parse_md(md: str, input_dir: Path = None) -> str:
    lines = md.split('\n')
    result = []
    i = 0

    ul_items = []
    ol_items = []

    def flush_ul():
        if ul_items:
            result.append(render_ul(ul_items))
            ul_items.clear()

    def flush_ol():
        if ol_items:
            result.append(render_ol(ol_items))
            ol_items.clear()

    def flush_lists():
        flush_ul()
        flush_ol()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 空行
        if not stripped:
            flush_lists()
            i += 1
            continue

        # 代码块 ```lang...```
        if stripped.startswith('```'):
            flush_lists()
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            result.append(render_codeblock('\n'.join(code_lines), lang))
            i += 1
            continue

        # # 一级标题 → h2
        if stripped.startswith('# ') and not stripped.startswith('## '):
            flush_lists()
            result.append(render_h2(stripped[2:].strip()))
            i += 1
            continue

        # ## h2
        if stripped.startswith('## '):
            flush_lists()
            result.append(render_h2(stripped[3:].strip()))
            i += 1
            continue

        # ### h3
        if stripped.startswith('### '):
            flush_lists()
            result.append(render_h3(stripped[4:].strip()))
            i += 1
            continue

        # #### 及更深 → h3
        if re.match(r'^#{4,}\s', stripped):
            flush_lists()
            text = re.sub(r'^#{4,}\s+', '', stripped)
            result.append(render_h3(text))
            i += 1
            continue

        # !! 橙色加粗整段 !!
        if stripped.startswith('!!') and stripped.endswith('!!') and len(stripped) > 4:
            flush_lists()
            result.append(render_hb(stripped[2:-2]))
            i += 1
            continue

        # > 引用块（连续多行合并为一个块，用 <br> 分隔）
        if re.match(r'^>\s*\S', stripped) or stripped == '>':
            flush_lists()
            bq_lines = []
            while i < len(lines):
                s = lines[i].strip()
                if s.startswith('> '):
                    bq_lines.append(s[2:])
                    i += 1
                elif s == '>':
                    # 孤立 > 行：当空行处理，结束块
                    i += 1
                    break
                else:
                    break
            if bq_lines:
                result.append(render_blockquote('<br>'.join(bq_lines)))
            continue

        # 孤立的 ">" 行 → 跳过
        if stripped == '>':
            i += 1
            continue

        # --- 分隔线
        if re.match(r'^[-*_]{3,}$', stripped):
            flush_lists()
            result.append(render_hr())
            i += 1
            continue

        # ~~注释~~ 独立行
        if stripped.startswith('~~') and stripped.endswith('~~') and len(stripped) > 4:
            inner = stripped[2:-2]
            if '~~' not in inner:
                flush_lists()
                result.append(render_note(inner))
                i += 1
                continue

        # 无序列表
        ul_match = re.match(r'^[-*+]\s+(.+)$', stripped)
        if ul_match:
            flush_ol()
            ul_items.append(ul_match.group(1))
            i += 1
            continue

        # 有序列表
        ol_match = re.match(r'^\d+\.\s+(.+)$', stripped)
        if ol_match:
            flush_ul()
            ol_items.append(ol_match.group(1))
            i += 1
            continue

        # 表格
        if stripped.startswith('|'):
            flush_lists()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            rows = []
            for tl in table_lines:
                cells = [c for c in tl[1:-1].split('|')]
                if not all(set(c.strip()) <= set('-: ') for c in cells):
                    rows.append(cells)
            if rows:
                result.append(render_table(rows))
            continue

        # 图片 ![alt](src)
        img_match = re.match(r'^!\[.*?\]\((.+?)\)$', stripped)
        if img_match:
            flush_lists()
            result.append(render_img(img_match.group(1), input_dir))
            i += 1
            continue

        # YAML front matter（跳过）
        if stripped == '---' and i == 0:
            i += 1
            while i < len(lines) and lines[i].strip() != '---':
                i += 1
            i += 1
            continue

        # 目录链接行（跳过）
        if re.match(r'^-\s+\[.+?\]\(#.+?\)$', stripped):
            i += 1
            continue

        # **整行加粗** → 橙色加粗段落
        if stripped.startswith('**') and stripped.endswith('**') and len(stripped) > 4:
            inner = stripped[2:-2]
            if '**' not in inner:
                flush_lists()
                result.append(render_bold_line(inner))
                i += 1
                continue

        # 普通段落（去掉行首孤立冒号）
        flush_lists()
        if stripped.startswith(':') and not stripped.startswith('::'):
            stripped = stripped[1:].strip()
        result.append(render_p(stripped))
        i += 1

    flush_lists()
    return '\n\n'.join(result)


# ============================================================
# 一键复制按钮 JS
# ============================================================

COPY_BUTTON_HTML = """
<div id="copy-bar" style="position: fixed; bottom: 24px; right: 24px; z-index: 9999;">
  <button id="copy-btn" onclick="copyContent()" style="
    background: rgb(0, 128, 255);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-family: 'PingFang SC', sans-serif;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,128,255,0.35);
    transition: all 0.2s;
  ">复制内容</button>
</div>
<script>
function copyContent() {
  const section = document.getElementById('mp-section');
  const btn = document.getElementById('copy-btn');
  const range = document.createRange();
  range.selectNode(section);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  try {
    document.execCommand('copy');
    btn.textContent = '✓ 已复制';
    btn.style.background = 'rgb(7, 134, 84)';
    setTimeout(() => {
      btn.textContent = '复制内容';
      btn.style.background = 'rgb(0, 128, 255)';
    }, 2000);
  } catch(e) {
    btn.textContent = '复制失败，请手动选择';
    btn.style.background = 'rgb(194, 28, 19)';
  }
  sel.removeAllRanges();
}
</script>
"""


def convert_md_to_html(md: str, title: str = "微信公众号文章", input_dir: Path = None) -> str:
    content = parse_md(md, input_dir)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body {STYLES["body"]}>

<section id="mp-section" {STYLES["section"]}>

{content}

</section>

{COPY_BUTTON_HTML if FEATURE_COPY_BUTTON else ""}
</body>
</html>'''


TEMPLATE_MD = """\
# 文章大标题

## 一级小节标题

普通正文段落。可以用 **加粗词句** 强调，也可以用 ==高亮关键词==，或 ==🔴红色字==、==🟥红底== 组合。

### 二级小节标题

!!整段橙色加粗，适合核心论点或金句。!!

- 无序列表项一
- 无序列表项二
- 无序列表项三

1. 有序列表第一步
2. 有序列表第二步
3. 有序列表第三步

> 引用块：适合摘录观点、名言或补充说明。

---

## 代码示例

行内代码：`print("Hello")`，链接：[洛小山](https://example.com)

```python
def hello(name: str) -> str:
    return f"Hello, {name}!"
```

```
无语言标注的代码块，当作说明性文字框使用。
适合放非代码的补充说明或结构化文本。
```

~~注释：小号灰色文字，适合来源标注或补充说明~~
"""


def generate_template(output_path: Path):
    """生成可直接粘贴到公众号的空白排版模板"""
    html = convert_md_to_html(TEMPLATE_MD, "排版模板", input_dir=output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"模板已生成：{output_path}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("使用方法:")
        print("  转换文章:  python3 排版要求/md_to_html.py '推文/xxx/初稿.md'")
        print("  生成模板:  python3 排版要求/md_to_html.py --template")
        sys.exit(0 if sys.argv[1:] else 1)

    if sys.argv[1] == "--template":
        out = Path(__file__).parent / "template.html"
        generate_template(out)
        return

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"错误：文件不存在 → {input_path}")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        md = f.read()

    title = input_path.stem
    html = convert_md_to_html(md, title, input_dir=input_path.parent)

    output_path = input_path.parent / (input_path.stem + '_formatted.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"转换完成！")
    print(f"输入: {input_path}")
    print(f"输出: {output_path}")


if __name__ == '__main__':
    main()
