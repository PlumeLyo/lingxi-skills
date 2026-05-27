"""
gen_script.py - PPT 构建通用工具函数库。

提供 python-pptx 常用操作的封装函数，供各页 build_slide_XX 调用，
减少重复代码，提升生成效率和代码可维护性。

使用方式：将本文件复制到构建目录，在各页代码中 from gen_script import ...
"""

from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree


# ---------------------------------------------------------------------------
# 文本相关
# ---------------------------------------------------------------------------

def add_textbox(slide, left, top, width, height, word_wrap=True):
    """创建文本框并返回 (textbox, text_frame)。

    Args:
        slide: python-pptx Slide 对象
        left, top, width, height: 位置和尺寸（支持 Inches/Pt/Emu/数值）
        word_wrap: 是否自动换行

    Returns:
        (textbox, text_frame) 元组
    """
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = word_wrap
    return txBox, tf


def add_paragraph(tf, text='', font_size=Pt(14), font_color=None,
                  bold=False, font_name='微软雅黑', alignment=PP_ALIGN.LEFT,
                  space_before=None, space_after=None, line_spacing=None):
    """向 text_frame 添加一个段落，返回 (paragraph, run)。

    如果 text 为空字符串，仍会创建 run（方便后续设置属性）。
    如果 text 不为空，会自动设置中文字体。

    Args:
        tf: TextFrame 对象
        text: 段落文字内容
        font_size: 字号，默认 Pt(14)
        font_color: 字体颜色 RGBColor，默认 None（黑色）
        bold: 是否加粗
        font_name: 字体名称，默认 '微软雅黑'
        alignment: 对齐方式，默认 PP_ALIGN.LEFT
        space_before: 段前间距 Pt 值
        space_after: 段后间距 Pt 值
        line_spacing: 行距，支持三种格式：
            - float (0.0-3.0): 倍数行距，如 1.5 表示 1.5 倍行距
            - Pt/Emu: 固定行距，如 Pt(20) 表示固定 20 磅行距
            - None: 使用默认行距

    Returns:
        (paragraph, run) 元组
    """
    # 判断是否是第一个段落
    if len(tf.paragraphs) == 1 and tf.paragraphs[0].text == '':
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()

    p.alignment = alignment
    if space_before is not None:
        p.space_before = space_before
    if space_after is not None:
        p.space_after = space_after

    # 设置行距
    if line_spacing is not None:
        if isinstance(line_spacing, (int, float)):
            # 倍数行距：1.0 = 100%, 1.5 = 150%
            p.line_spacing = line_spacing
        else:
            # 固定行距：Pt/Emu 值
            p.line_spacing = line_spacing

    run = p.add_run()
    if text:
        run.text = text
    run.font.size = font_size
    if font_color is not None:
        run.font.color.rgb = font_color
    run.font.bold = bold
    run.font.name = font_name
    # 设置中文字体
    rPr = run._r.get_or_add_rPr()
    rPr.set(qn('a:eastAsia'), font_name)

    return p, run


def set_run_style(run, text=None, font_size=None, font_color=None,
                  bold=None, font_name='微软雅黑'):
    """设置已有 run 的文字样式（支持部分更新）。

    如果传入了 text，会自动设置中文字体。
    如果 text 为 None，则不修改文字内容，也不设置中文字体（除非显式传 font_name）。

    Args:
        run: Run 对象
        text: 文字内容，None 表示不修改
        font_size: 字号 Pt 值，None 表示不修改
        font_color: 字体颜色 RGBColor，None 表示不修改
        bold: 是否加粗，None 表示不修改
        font_name: 字体名称，默认 '微软雅黑'

    Returns:
        run 对象
    """
    if text is not None:
        run.text = text
    if font_size is not None:
        run.font.size = font_size
    if font_color is not None:
        run.font.color.rgb = font_color
    if bold is not None:
        run.font.bold = bold
    if text is not None:
        run.font.name = font_name
        rPr = run._r.get_or_add_rPr()
        rPr.set(qn('a:eastAsia'), font_name)
    return run


# ---------------------------------------------------------------------------
# 形状相关
# ---------------------------------------------------------------------------

def add_rect(slide, left, top, width, height, fill_color, line_visible=False,
             line_color=None, line_width=None):
    """创建填充矩形（无边框或可选边框）。

    Args:
        slide: Slide 对象
        left, top, width, height: 位置和尺寸
        fill_color: 填充颜色 RGBColor
        line_visible: 是否显示边框
        line_color: 边框颜色 RGBColor（line_visible=True 时生效）
        line_width: 边框宽度 Pt（line_visible=True 时生效）

    Returns:
        shape 对象
    """
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_visible:
        if line_color is not None:
            shape.line.color.rgb = line_color
        if line_width is not None:
            shape.line.width = line_width
    else:
        shape.line.fill.background()
    return shape


def add_rounded_rect(slide, left, top, width, height, fill_color,
                     corner_radius=8000, line_visible=False,
                     line_color=None, line_width=None):
    """创建圆角矩形卡片。

    Args:
        slide: Slide 对象
        left, top, width, height: 位置和尺寸
        fill_color: 填充颜色 RGBColor
        corner_radius: 圆角大小（0-50000），默认 8000
        line_visible: 是否显示边框
        line_color: 边框颜色 RGBColor
        line_width: 边框宽度 Pt

    Returns:
        shape 对象
    """
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_visible:
        if line_color is not None:
            shape.line.color.rgb = line_color
        if line_width is not None:
            shape.line.width = line_width
    else:
        shape.line.fill.background()

    # 设置圆角大小
    _set_corner_radius(shape, corner_radius)
    return shape


def set_shape_opacity(shape, opacity_percent):
    """设置形状填充透明度。

    Args:
        shape: Shape 对象（必须已设置 fill.solid + fore_color）
        opacity_percent: 不透明度百分比，0-100（100=完全不透明，0=完全透明）
    """
    val = int(opacity_percent * 1000)  # 转换为 0-100000 范围
    spPr = shape._element.spPr
    solidFill = spPr.find(qn('a:solidFill'))
    if solidFill is not None:
        srgbClr = solidFill.find(qn('a:srgbClr'))
        if srgbClr is not None:
            alpha = etree.SubElement(srgbClr, qn('a:alpha'))
            alpha.set('val', str(val))


# ---------------------------------------------------------------------------
# 图片相关
# ---------------------------------------------------------------------------

def add_picture(slide, image_path, left, top, width=None, height=None):
    """安全添加图片（自动 try/except，失败时静默跳过）。

    Args:
        slide: Slide 对象
        image_path: 图片绝对路径
        left, top: 位置
        width, height: 尺寸（可选，不传则使用图片原始尺寸）

    Returns:
        bool: 是否成功添加
    """
    try:
        if width is not None and height is not None:
            slide.shapes.add_picture(image_path, left, top, width, height)
        elif width is not None:
            slide.shapes.add_picture(image_path, left, top, width=width)
        elif height is not None:
            slide.shapes.add_picture(image_path, left, top, height=height)
        else:
            slide.shapes.add_picture(image_path, left, top)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------

def _set_corner_radius(shape, radius):
    """设置圆角矩形的圆角大小。

    Args:
        shape: Shape 对象（必须是 ROUNDED_RECTANGLE 类型）
        radius: 圆角大小（0-50000）
    """
    spPr = shape._element.spPr
    prstGeom = spPr.find(qn('a:prstGeom'))
    if prstGeom is not None:
        avLst = prstGeom.find(qn('a:avLst'))
        if avLst is None:
            avLst = etree.SubElement(prstGeom, qn('a:avLst'))
        else:
            for child in list(avLst):
                avLst.remove(child)
        gd = etree.SubElement(avLst, qn('a:gd'))
        gd.set('name', 'adj')
        gd.set('fmla', f'val {radius}')