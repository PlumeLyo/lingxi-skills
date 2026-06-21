# -*- coding: utf-8 -*-
"""
彳亍时刻公众号排版引擎 v2.3
四模板：光迹(glow) / 星光(starlight) / 光境(lumin) / 余温(warmth)
"""

import os, re, base64, io
from PIL import Image

LOGO_PATH = r"C:\Users\羽涅\Desktop\work\素材库\logo\logo无背景1.png"
SITE_NAME = "彳亍时刻"
FONT_FAMILY = "'PingFang SC','Helvetica Neue','Microsoft YaHei',sans-serif"
PRESETS = {
"glow": {
        "tag_cn": "光迹", "tag_en": "Stray Light",
        "subtitle_line": "Stray Moments · 光迹",
        "primary": "rgb(245,124,0)",
        "primary_light": "rgb(255,240,224)",
        "accent": "rgb(50,50,50)",
        "accent_deep": "rgb(33,33,33)",
        "quote_bg": "rgb(255,240,224)",
        "quote_border": "rgb(245,124,0)",
        "text_color": "rgb(50,50,50)",
        "text_dark": "rgb(33,33,33)",
        "h2_color": "rgb(245,124,0)",
        "bold_color": "rgb(245,124,0)",
        "font_size": "15px", "line_height": "1.8",
        "section_bg": "rgb(255,252,245)",
        "body_bg": "rgb(255,255,255)",
        "btn_bg": "rgb(245,124,0)", "btn_text": "#ffffff", "btn_border": "rgb(245,124,0)",
        "card_bg": "rgb(255,240,224)",
        "first_indent": False,
        "para_style_extra": "max-width:100%;word-break:break-all;",
        "use_logo": True, "use_button": True,
        "font_family": FONT_FAMILY,
        "style_type": "brand",
    },
    "starlight": {
        "tag_cn": "星光", "tag_en": "Starlight",
        "subtitle_line": "Stray Moments · 星光",
        "primary": "rgb(121,134,203)",
        "primary_light": "rgb(227,242,253)",
        "accent": "rgb(33,33,33)",
        "accent_deep": "rgb(33,33,33)",
        "quote_bg": "rgb(227,242,253)",
        "quote_border": "rgb(121,134,203)",
        "text_color": "rgb(50,50,50)",
        "text_dark": "rgb(33,33,33)",
        "h2_color": "rgb(121,134,203)",
        "bold_color": "rgb(121,134,203)",
        "font_size": "15px", "line_height": "2.0",
        "section_bg": "rgb(247,249,252)",
        "body_bg": "rgb(255,255,255)",
        "btn_bg": "rgb(121,134,203)", "btn_text": "#ffffff", "btn_border": "rgb(121,134,203)",
        "card_bg": "rgb(227,242,253)",
        "first_indent": False,
        "para_style_extra": "max-width:100%;word-break:break-all;",
        "use_logo": True, "use_button": True,
        "font_family": FONT_FAMILY,
        "style_type": "brand",
    },
    "lumin": {
        "tag_cn": "光境", "tag_en": "Lumin",
        "subtitle_line": "Stray Moments · 光境",
        "primary": "rgb(184,122,0)",
        "primary_light": "rgb(255,253,245)",
        "accent": "rgb(40,40,40)",
        "accent_deep": "rgb(33,33,33)",
        "quote_bg": "rgb(255,253,245)",
        "quote_border": "rgb(255,224,130)",
        "text_color": "rgb(50,50,50)",
        "text_dark": "rgb(40,40,40)",
        "h2_color": "rgb(184,122,0)",
        "bold_color": "rgb(184,122,0)",
        "font_size": "16px", "line_height": "2.2",
        "section_bg": "rgb(255,253,245)",
        "body_bg": "rgb(255,253,245)",
        "btn_bg": "rgb(184,122,0)", "btn_text": "#ffffff", "btn_border": "rgb(184,122,0)",
        "card_bg": "rgb(255,253,245)",
        "first_indent": True,
        "para_style_extra": "max-width:100%;word-break:break-all;",
        "use_logo": True, "use_button": True,
        "font_family": FONT_FAMILY,
        "style_type": "brand",
    },
    "warmth": {
        "tag_cn": "余温", "tag_en": "Stray Warmth",
        "subtitle_line": "· 彳亍时刻 ·",
        "primary": "#BFB5A4",
        "primary_light": "#FAF9F6",
        "accent": "#3D3832",
        "accent_deep": "#4A453E",
        "quote_bg": "#FAF9F6",
        "quote_border": "#BFB5A4",
        "text_color": "#4A453E",
        "text_dark": "#3D3832",
        "h2_color": "#3D3832",
        "bold_color": "#3D3832",
        "font_size": "15px", "line_height": "2.2",
        "section_bg": "#FAF9F6",
        "body_bg": "#FAF9F6",
        "btn_bg": "", "btn_text": "", "btn_border": "",
        "card_bg": "#FAF9F6",
        "first_indent": True,
        "para_style_extra": "max-width:100%;word-break:break-all;",
        "use_logo": False, "use_button": False,
        "font_family": "'Noto Serif SC',serif",
        "style_type": "prose",
    },
}

_TAG_MAP = {
    "\u661f\u5149": "starlight",
    "\u5149\u8ff9": "glow",
    "\u5149\u5883": "lumin",
    "\u4f59\u6e29": "warmth",
}

_logo_b64_cache = None
def get_logo_base64(height=104):
    global _logo_b64_cache
    if _logo_b64_cache is not None:
        return _logo_b64_cache
    img = Image.open(LOGO_PATH).convert("RGBA")
    w, h = img.size
    new_w = int(w * height / h)
    img_resized = img.resize((new_w, height), Image.LANCZOS)
    buf = io.BytesIO()
    img_resized.save(buf, format="PNG", optimize=True)
    _logo_b64_cache = base64.b64encode(buf.getvalue()).decode()
    return _logo_b64_cache


def _brand_header(title, date_str, logo_b64, p):
    parts = []
    if p["use_logo"] and logo_b64:
        parts.append('<p style="text-align:center;margin:0 0 18px;"><img src="data:image/png;base64,' + logo_b64 + '" style="width:52px;height:auto;"></p>')
    parts.append('<p style="text-align:center;margin:0 0 6px;font-size:12px;color:' + p["primary"] + ';letter-spacing:1px;">' + p["subtitle_line"] + '</p>')
    parts.append('<p style="font-size:22px;font-weight:600;color:' + p["accent"] + ';text-align:center;margin:0 0 8px;letter-spacing:1px;">' + title + '</p>')
    parts.append('<p style="text-align:center;margin:0 0 20px;font-size:12px;color:' + p["text_dark"] + ';opacity:0.6;">' + date_str + '</p>')
    parts.append('<p style="border-top:1px solid ' + p["primary"] + ';opacity:0.3;margin:0 0 24px;"></p>')
    return '\n'.join(parts)


def _brand_footer(interactive_q, logo_b64, p):
    parts = []
    parts.append('<p style="border-top:1px solid ' + p["primary"] + ';opacity:0.3;margin:28px 0 20px;"></p>')
    if interactive_q:
        parts.append('<p style="font-size:14px;color:' + p["text_color"] + ';margin:0 0 16px;text-align:center;">' + interactive_q + '</p>')
    if p["use_button"]:
        parts.append('<p style="text-align:center;margin:0 0 20px;"><span style="display:inline-block;background:' + p["btn_bg"] + ';color:' + p["btn_text"] + ';border:1px solid ' + p["btn_border"] + ';border-radius:6px;padding:8px 24px;font-size:13px;">在看</span></p>')
    if p["use_logo"] and logo_b64:
        parts.append('<p style="text-align:center;margin:0 0 8px;"><img src="data:image/png;base64,' + logo_b64 + '" style="width:72px;height:auto;opacity:0.85;"></p>')
    parts.append('<p style="text-align:center;font-size:11px;color:' + p["text_dark"] + ';opacity:0.7;margin:0;">' + SITE_NAME + ' · ' + p["tag_en"] + '</p>')
    parts.append('<p style="text-align:center;font-size:10px;color:' + p["text_dark"] + ';opacity:0.4;margin:4px 0 0;">一个在人间收集散落时刻的人</p>')
    return '\n'.join(parts)


def _prose_header(title, date_str, logo_b64, p):
    spaced_title = " ".join(title)
    return '\n'.join([
        "<!-- 装饰线 -->",
        '<p style="border-top:1px solid ' + p["primary"] + ';width:1px;margin:0 auto 28px;"></p>',
        "",
        "<!-- 标题 -->",
        '<p style="font-family:' + p["font_family"] + ';font-size:22px;font-weight:400;color:' + p["accent"] + ';letter-spacing:6px;text-align:center;margin:0 0 14px;">' + spaced_title + '</p>',
        "",
        '<p style="border-top:1px solid ' + p["primary"] + ';width:5px;margin:0 auto 18px;"></p>',
        "",
        "<!-- 副标题 -->",
        '<p style="font-family:' + p["font_family"] + ';font-size:12px;color:' + p["primary"] + ';letter-spacing:2px;text-align:center;margin:0 0 32px;">' + date_str + '</p>',
    ])


def _prose_footer(interactive_question, logo_b64, p):
    return '\n'.join([
        "",
        "<!-- 底部 -->",
        '<p style="border-top:1px solid ' + p["primary"] + ';width:32px;margin:20px auto 16px;"></p>',
        '<p style="font-family:' + p["font_family"] + ';font-size:11px;color:' + p["primary"] + ';letter-spacing:2px;text-align:center;margin:0;">' + SITE_NAME + '</p>',
    ])


def _parse_bold(text, p):
    def _bold_repl(m):
        return '<span style="color:' + p["bold_color"] + ';font-weight:600;">' + m.group(1) + '</span>'
    return re.sub(r"\*\*(.+?)\*\*", _bold_repl, text)

def _parse_h2(line, p):
    text = re.sub(r"^##\s+", "", line).strip()
    text = _parse_bold(text, p)
    return '<p style="font-size:18px;font-weight:600;color:' + p["h2_color"] + ';margin:28px 0 16px;">' + text + '</p>'

def _parse_blockquote(line, p):
    text = re.sub(r"^\>\s?", "", line).strip()
    text = _parse_bold(text, p)
    return '<blockquote style="border-left:3px solid ' + p["quote_border"] + ';padding:10px 16px;margin:16px 0;background:' + p["quote_bg"] + ';color:' + p["text_color"] + ';font-size:' + p["font_size"] + ';">' + text + '</blockquote>'

def _parse_paragraph(line, p):
    text = line.strip()
    text = _parse_bold(text, p)
    indent = "text-indent:2em;" if p["first_indent"] else ""
    return '<p style="font-family:' + p["font_family"] + ';font-size:' + p["font_size"] + ';color:' + p["text_color"] + ';line-height:' + p["line_height"] + ';' + indent + p["para_style_extra"] + 'margin:0 0 20px;">' + text + '</p>'

def _parse_hr(p):
    return '<p style="border-top:1px solid ' + p["primary"] + ';opacity:0.3;margin:20px 0;"></p>'


def parse_markdown(md_text, p):
    body = []
    for line in md_text.split("\n"):
        l = line.strip()
        if not l:
            continue
        if re.match(r"^\>\s*\u2014\s*\u6734\u4e30", l):
            continue
        if re.match(r"^#\s", l) and not re.match(r"^##\s", l):
            continue
        if re.match(r"^##\s", l):
            body.append(_parse_h2(l, p))
            continue
        if re.match(r"^\>\s", l):
            body.append(_parse_blockquote(l, p))
            continue
        if re.match(r"^(---|\u00b7\u00b7\u00b7)", l):
            body.append(_parse_hr(p))
            continue
        body.append(_parse_paragraph(l, p))
    return "\n".join(body)


def xzsk_publish(md_path=None, output_path=None, date_str=None, section="starlight"):
    if section in _TAG_MAP:
        section = _TAG_MAP[section]
    if section not in PRESETS:
        section = "starlight"

    p = PRESETS[section]

    if md_path and os.path.isfile(md_path):
        with open(md_path, encoding="utf-8") as f:
            md_text = f.read()
    else:
        md_text = md_path or ""

    title = ""
    for line in md_text.split("\n"):
        m = re.match(r"^#\s+(.+)", line.strip())
        if m:
            title = m.group(1).strip()
            break

    body_content = parse_markdown(md_text, p)

    if not date_str:
        from datetime import date as _d
        today = _d.today()
        date_str = str(today.year) + "年" + str(today.month) + "月" + str(today.day) + "日"

    logo_b64 = None
    if p.get("use_logo") and os.path.isfile(LOGO_PATH):
        logo_b64 = get_logo_base64()

    if p["style_type"] == "prose":
        subtitle = ""
        title_idx = md_text.find("# ")
        if title_idx >= 0:
            rest = md_text[title_idx:].strip().split("\n")
            if len(rest) > 1:
                candidate = rest[1].strip()
                if candidate and not candidate.startswith("#") and len(candidate) < 50:
                    subtitle = candidate
        display_date = subtitle if subtitle else date_str
        header = _prose_header(title or SITE_NAME, display_date, logo_b64, p)
        footer = _prose_footer("", logo_b64, p)
    else:
        header = _brand_header(title or SITE_NAME, date_str, logo_b64, p)
        interactive_q = ""
        for line in reversed(md_text.strip().split("\n")):
            l = line.strip()
            if "\uff1f" in l and len(l) < 40 and not l.startswith("#") and not l.startswith(">"):
                interactive_q = l
                break
        if interactive_q:
            interactive_q = _parse_bold(interactive_q, p)
        footer = _brand_footer(interactive_q, logo_b64, p)


    if p["style_type"] == "prose":
        table_bg = '<table width="100%" cellpadding="0" cellspacing="0" bgcolor="#FAF9F6" style="background-color:#FAF9F6;"><tr><td><section style="padding:48px 28px 36px;">'
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "<title>" + (title or SITE_NAME) + "</title>",
            "</head>",
            '<body style="margin:0;padding:0;">',
            "",
            table_bg,
            "",
            header,
            "",
            "<!-- \u6b63\u6587 -->",
            body_content,
            "",
            footer,
            "",
            "</section>",
            "</td></tr></table>",
            "",
            "</body>",
            "</html>",
        ]
    else:
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "<title>" + (title or SITE_NAME) + "</title>",
            "</head>",
            '<body style="margin:0;padding:0;background-color:' + p["section_bg"] + ';">',
            "",
            '<section id="mp-section" style="max-width:677px;margin:0 auto;padding:14px 16px;font-family:' + FONT_FAMILY + ';background-color:' + p["body_bg"] + ';">',
            "",
            header,
            "",
            "<!-- \u6b63\u6587 -->",
            body_content,
            "",
            footer,
            "",
            "</section>",
            "",
            '<div id="copy-bar" style="position:fixed;bottom:24px;right:24px;z-index:9999;">',
            '<button id="copy-btn" onclick="copyContent()" style="background:' + p["btn_bg"] + ';color:#fff;border:none;border-radius:8px;padding:10px 20px;font-size:14px;cursor:pointer;box-shadow:0 4px 12px rgba(100,100,100,0.25);">\u590d\u5236\u5185\u5bb9</button>',
            "</div>",
            "<script>",
            "function copyContent() {",
            "  const section = document.getElementById('mp-section');",
            "  const btn = document.getElementById('copy-btn');",
            "  const range = document.createRange();",
            "  range.selectNode(section);",
            "  const sel = window.getSelection();",
            "  sel.removeAllRanges();",
            "  sel.addRange(range);",
            "  document.execCommand('copy');",
            "  btn.textContent = '\u5df2\u590d\u5236';",
            "  setTimeout(() => btn.textContent = '\u590d\u5236\u5185\u5bb9', 1500);",
            "}",
            "</script>",
            "",
            "</body>",
            "</html>",
        ]

    html = "\n".join(html_parts)

    if not output_path:
        out_dir = os.path.dirname(os.path.abspath(md_path)) if md_path else "."
        safe_name = title if title else "xzsk_output"
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", safe_name)
        output_path = os.path.join(out_dir, safe_name + "_" + p["tag_cn"] + "_公众号排版.html")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    sz_kb = os.path.getsize(output_path) / 1024
    return {
        "ok": True,
        "output_path": output_path,
        "message": "排版完成 [" + p["tag_cn"] + "] " + p["tag_en"] + "，文件大小 " + str(round(sz_kb, 1)) + " KB",
        "title": title,
        "section": section,
    }
