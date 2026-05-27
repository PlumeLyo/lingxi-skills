"""
模板页型分析工具

读取用户上传的 PPTX 文件，遍历每页，分析页面角色和可编辑槽位，
输出 template_layouts.json 供大纲规划时引用。

用法:
    from analyze_template_layouts import analyze_template_layouts
    result = analyze_template_layouts("path/to/template.pptx")
    print(result)  # JSON 字符串
"""

from analyze_pptx import analyze_shape, emu_to_cm
import json
import os
import sys
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _emu_to_cm_precise(v) -> float:
    """高精度 EMU->cm，不在中间步骤提前四舍五入。"""
    return float(v) / float(Emu(360000))


def _get_text_direction(shape) -> str:
    """
    判断文本方向：horizontal / vertical / vertical-270 / unknown。
    基于 txBody 的 bodyPr@vert 属性。
    """
    if not shape.has_text_frame:
        return "unknown"
    try:
        body_pr = shape.text_frame._txBody.bodyPr
        vert = body_pr.get("vert")
        if not vert or vert in ("horz",):
            return "horizontal"
        if vert in ("vert", "eaVert", "mongolianVert", "wordArtVert"):
            return "vertical"
        if vert in ("vert270", "wordArtVertRtl"):
            return "vertical-270"
        return str(vert)
    except Exception:
        return "unknown"


# ──────────────────────────────────────────────────────────────────────
# 页面角色推断
# ──────────────────────────────────────────────────────────────────────

_COVER_KEYWORDS = ["封面", "cover", "标题页", "title slide"]
_TOC_KEYWORDS = ["目录", "toc", "contents", "agenda", "outline"]
_SECTION_KEYWORDS = ["章节", "section", "part", "篇章", "分隔"]
_CLOSING_KEYWORDS = ["结束", "感谢", "thank", "ending", "q&a", "谢谢"]
_CHART_KEYWORDS = ["图表", "chart", "数据", "data"]


def _text_contains(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _infer_page_role(slide, slide_index: int, total_slides: int) -> str:
    """
    根据页面内容和位置推断页面角色。

    返回值: cover / toc / section / content / chart / closing
    """
    texts = []
    has_chart = False
    has_table = False
    text_shape_count = 0
    picture_count = 0
    placeholder_types = []

    for shape in slide.shapes:
        if shape.has_text_frame and shape.text.strip():
            texts.append(shape.text.strip())
            text_shape_count += 1
        if shape.has_chart:
            has_chart = True
        if shape.has_table:
            has_table = True
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            picture_count += 1
            # print(f"  [PICTURE] name={shape.name!r}, left={round(shape.left/914400*2.54, 2)}cm, top={round(shape.top/914400*2.54, 2)}cm, w={round(shape.width/914400*2.54, 2)}cm, h={round(shape.height/914400*2.54, 2)}cm")
        if shape.is_placeholder:
            try:
                placeholder_types.append(str(shape.placeholder_format.type))
            except Exception:
                pass

    combined_text = " ".join(texts)

    # print(f"analyze_template_layouts.py row[72] combined_text: {combined_text}")
    # print(f"analyze_template_layouts.py row[73] text_shape_count: {text_shape_count}")
    # print(f"analyze_template_layouts.py row[74] has_chart: {has_chart}")
    # print(f"analyze_template_layouts.py row[75] has_table: {has_table}")
    # print(f"analyze_template_layouts.py row[76] picture_count: {picture_count}")
    # print(f"analyze_template_layouts.py row[77] placeholder_types: {placeholder_types}")

    if slide_index == 0 and text_shape_count <= 4:
        return "cover"

    if slide_index == total_slides - 1 and _text_contains(combined_text, _CLOSING_KEYWORDS):
        return "closing"

    if slide_index == total_slides - 1 and text_shape_count <= 3:
        return "closing"

    if _text_contains(combined_text, _COVER_KEYWORDS) and slide_index <= 1:
        return "cover"

    if _text_contains(combined_text, _CLOSING_KEYWORDS):
        return "closing"

    if _text_contains(combined_text, _TOC_KEYWORDS):
        return "toc"

    if _text_contains(combined_text, _SECTION_KEYWORDS) and text_shape_count <= 3:
        return "section"

    if has_chart:
        return "chart"

    if has_table:
        return "content"

    return "content"


# ──────────────────────────────────────────────────────────────────────
# 可编辑槽位提取
# ──────────────────────────────────────────────────────────────────────

def _classify_text_slot(shape, shape_index, page_role: str) -> dict | None:
    """将一个含文本的 shape 分类为 editable_slot。"""
    if not shape.has_text_frame:
        return None
    text = shape.text.strip()
    if not text:
        return None

    font_size_pt = None
    is_bold = False
    font_name = None
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            if run.font.size:
                font_size_pt = run.font.size.pt
            if run.font.bold:
                is_bold = True
            if run.font.name:
                font_name = run.font.name
            break
        if font_size_pt:
            break

    width_cm = _emu_to_cm_precise(shape.width)
    height_cm = _emu_to_cm_precise(shape.height)

    is_placeholder = shape.is_placeholder
    ph_type = None
    if is_placeholder:
        try:
            ph_type = str(shape.placeholder_format.type)
        except Exception:
            pass

    if ph_type and "TITLE" in str(ph_type).upper():
        slot_kind = "title"
    elif ph_type and "SUBTITLE" in str(ph_type).upper():
        slot_kind = "subtitle"
    elif ph_type and "BODY" in str(ph_type).upper():
        slot_kind = "body"
    elif font_size_pt and font_size_pt >= 28 and is_bold:
        slot_kind = "title"
    elif font_size_pt and font_size_pt >= 20 and is_bold:
        slot_kind = "subtitle"
    elif width_cm > 15 and height_cm > 5:
        slot_kind = "body"
    elif len(text) <= 30:
        slot_kind = "label"
    else:
        slot_kind = "body"

    z_order = _extract_z_order(shape_index)
    raw_width_cm_precise = _emu_to_cm_precise(shape.width)
    raw_height_cm_precise = _emu_to_cm_precise(shape.height)
    text_direction = _get_text_direction(shape)
    slot = {
        "kind": "text",
        "shape_id": shape.shape_id,
        "z_order": z_order,
        "position_cm": {
            "left": _emu_to_cm_precise(shape.left),
            "top": _emu_to_cm_precise(shape.top),
        },
        "size_cm": {
            "width": raw_width_cm_precise,
            "height": raw_height_cm_precise,
        },
        "font": {
            "size_pt": font_size_pt if font_size_pt is not None else None,
            "name": font_name,
            "bold": is_bold,
        },
        "text_direction": text_direction,
        "text_preview": text[:60] + ("..." if len(text) > 60 else ""),
    }
    if len(text) == 1:
        slot["editing_hint"] = "该元素偏装饰用途，建议仅填充单个字符。"
    return slot


def _is_picture_shape(shape) -> bool:
    """判断一个 shape 是否是图片（含 PICTURE 类型和图片占位符）。"""
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return True
    if shape.is_placeholder:
        try:
            ph_type = str(shape.placeholder_format.type).upper()
            if "PICTURE" in ph_type:
                return True
        except Exception:
            pass
    return False


def _extract_z_order(index_label: str) -> int:
    """从 index_label 中提取 z_order（使用最后一段索引）。"""
    try:
        return int(str(index_label).split(".")[-1])
    except (ValueError, TypeError):
        return 0


def _get_group_scale(group_shape) -> tuple[float, float]:
    """读取 group 的缩放系数: ext/chExt。读取失败时返回 (1.0, 1.0)。"""
    try:
        ns = {
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        }
        grp_sp_pr = group_shape._element.find(".//p:grpSpPr", ns)
        if grp_sp_pr is None:
            return 1.0, 1.0
        xfrm = grp_sp_pr.find(".//a:xfrm", ns)
        if xfrm is None:
            return 1.0, 1.0
        ext = xfrm.find("a:ext", ns)
        ch_ext = xfrm.find("a:chExt", ns)
        if ext is None or ch_ext is None:
            return 1.0, 1.0
        ext_cx = int(ext.get("cx", "0"))
        ext_cy = int(ext.get("cy", "0"))
        ch_cx = int(ch_ext.get("cx", "0"))
        ch_cy = int(ch_ext.get("cy", "0"))
        if ch_cx <= 0 or ch_cy <= 0:
            return 1.0, 1.0
        return ext_cx / ch_cx, ext_cy / ch_cy
    except Exception:
        return 1.0, 1.0


def _get_group_ch_off(group_shape) -> tuple[int, int]:
    """读取 group 的 chOff（子坐标系原点在 group 内部坐标系中的偏移）。读取失败返回 (0, 0)。"""
    try:
        ns = {
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        }
        grp_sp_pr = group_shape._element.find(".//p:grpSpPr", ns)
        if grp_sp_pr is None:
            return 0, 0
        xfrm = grp_sp_pr.find(".//a:xfrm", ns)
        if xfrm is None:
            return 0, 0
        ch_off = xfrm.find("a:chOff", ns)
        if ch_off is None:
            return 0, 0
        return int(ch_off.get("x", "0")), int(ch_off.get("y", "0"))
    except Exception:
        return 0, 0


def _apply_parent_offset_to_slot(slot: dict, parent_left: int, parent_top: int,
                                 parent_chOff_x: int = 0, parent_chOff_y: int = 0) -> dict:
    """
    将父级 group 偏移累加到 slot 的 position_cm（绝对定位）。

    Group 子元素的 shape.left/top 是在 group 子坐标系中的坐标（chOff 为原点），
    需要先减去 chOff 再加上 group 的绝对位置：
        absolute = parent_abs + (child_local - parent_chOff)
    """
    if not slot or "position_cm" not in slot:
        return slot
    pos = slot.get("position_cm", {})
    left_cm = pos.get("left")
    top_cm = pos.get("top")
    if left_cm is None or top_cm is None:
        return slot

    slot["position_cm"] = {
        "left": round(left_cm + emu_to_cm(parent_left - parent_chOff_x), 2),
        "top": round(top_cm + emu_to_cm(parent_top - parent_chOff_y), 2),
    }
    return slot


def _apply_parent_scale_to_slot_size(slot: dict, scale_x: float, scale_y: float) -> dict:
    """按父级 group 累积缩放修正 size_cm，并统一保留两位小数。"""
    if not slot or "size_cm" not in slot:
        return slot
    size = slot.get("size_cm", {})
    width_cm = size.get("width")
    height_cm = size.get("height")
    if width_cm is None or height_cm is None:
        return slot
    slot["size_cm"] = {
        "width": round(width_cm * scale_x, 2),
        "height": round(height_cm * scale_y, 2),
    }
    return slot


def _try_extract_slot(shape, index_label: str) -> dict | None:
    """尝试从单个 shape 提取 editable_slot，返回 None 表示不可编辑。"""
    if shape.has_text_frame and shape.text.strip():
        return _classify_text_slot(shape, index_label, "")

    if _is_picture_shape(shape):
        z_order = _extract_z_order(index_label)
        return {
            "kind": "image",
            "shape_id": shape.shape_id,
            "z_order": z_order,
            "position_cm": {
                "left": _emu_to_cm_precise(shape.left),
                "top": _emu_to_cm_precise(shape.top),
            },
            "size_cm": {
                "width": _emu_to_cm_precise(shape.width),
                "height": _emu_to_cm_precise(shape.height),
            },
        }

    if shape.has_chart:
        z_order = _extract_z_order(index_label)
        return {
            "kind": "chart",
            "shape_id": shape.shape_id,
            "z_order": z_order,
            "position_cm": {
                "left": _emu_to_cm_precise(shape.left),
                "top": _emu_to_cm_precise(shape.top),
            },
            "size_cm": {
                "width": _emu_to_cm_precise(shape.width),
                "height": _emu_to_cm_precise(shape.height),
            },
            "chart_type": str(shape.chart.chart_type),
        }

    if shape.has_table:
        table = shape.table
        z_order = _extract_z_order(index_label)
        return {
            "kind": "table",
            "shape_id": shape.shape_id,
            "z_order": z_order,
            "position_cm": {
                "left": _emu_to_cm_precise(shape.left),
                "top": _emu_to_cm_precise(shape.top),
            },
            "size_cm": {
                "width": _emu_to_cm_precise(shape.width),
                "height": _emu_to_cm_precise(shape.height),
            },
            "rows": len(table.rows),
            "columns": len(table.columns),
        }

    return None


def _extract_slots_recursive(
    shapes,
    prefix: str = "",
    parent_left: int = 0,
    parent_top: int = 0,
    parent_chOff_x: int = 0,
    parent_chOff_y: int = 0,
    parent_scale_x: float = 1.0,
    parent_scale_y: float = 1.0,
) -> list[dict]:
    """递归提取所有可编辑槽位，支持任意深度的 GROUP 嵌套。

    坐标转换公式:
        child_absolute = parent_absolute + (child_local - parent_chOff)
    其中:
        parent_absolute: 父 Group 在幻灯片坐标系中的绝对位置
        child_local:    子元素在 Group 子坐标系中的位置 (shape.left/top)
        parent_chOff:   父 Group 的 chOff（子坐标系原点偏移）
    """
    slots = []
    for idx, shape in enumerate(shapes):
        index_label = f"{prefix}{idx}" if not prefix else f"{prefix}.{idx}"
        if shape.shape_type == MSO_SHAPE_TYPE.FREEFORM:
            continue
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            group_scale_x, group_scale_y = _get_group_scale(shape)
            # 计算当前 Group 的绝对位置（与子元素同样的公式）
            group_abs_left = parent_left + (shape.left - parent_chOff_x)
            group_abs_top = parent_top + (shape.top - parent_chOff_y)
            # 获取当前 Group 的 chOff，传给子元素
            group_chOff_x, group_chOff_y = _get_group_ch_off(shape)
            slots.extend(
                _extract_slots_recursive(
                    shape.shapes,
                    index_label,
                    group_abs_left,
                    group_abs_top,
                    group_chOff_x,
                    group_chOff_y,
                    parent_scale_x * group_scale_x,
                    parent_scale_y * group_scale_y,
                )
            )
            continue
        slot = _try_extract_slot(shape, index_label)
        if slot:
            slot = _apply_parent_offset_to_slot(slot, parent_left, parent_top, parent_chOff_x, parent_chOff_y)
            slot = _apply_parent_scale_to_slot_size(slot, parent_scale_x, parent_scale_y)
            slots.append(slot)
    return slots


def _extract_editable_slots(slide) -> tuple[list[dict], list[dict]]:
    """提取一页中的可编辑/不可编辑槽位，递归展开 GROUP。"""
    all_slots = _extract_slots_recursive(slide.shapes)
    editable_slots = []
    uneditable_slots = []
    for slot in all_slots:
        if slot["kind"] == "image":
            uneditable_slots.append(slot)
        else:
            editable_slots.append(slot)
    return editable_slots, uneditable_slots


# ──────────────────────────────────────────────────────────────────────
# 布局 ID 生成
# ──────────────────────────────────────────────────────────────────────

def _generate_layout_id(page_role: str, slide_index: int, slots: list[dict]) -> str:
    """根据页面角色和槽位结构生成一个可读的 layout_id。"""
    text_count = sum(1 for s in slots if s["kind"] == "text")
    image_count = sum(1 for s in slots if s["kind"] == "image")
    chart_count = sum(1 for s in slots if s["kind"] == "chart")
    table_count = sum(1 for s in slots if s["kind"] == "table")

    parts = [page_role]
    if text_count:
        parts.append(f"{text_count}txt")
    if image_count:
        parts.append(f"{image_count}img")
    if chart_count:
        parts.append(f"{chart_count}chart")
    if table_count:
        parts.append(f"{table_count}tbl")

    # print(f"analyze_template_layouts.py row[246] parts: {parts}")

    return f"{'_'.join(parts)}_s{slide_index}"


# ──────────────────────────────────────────────────────────────────────
# 可复用性判断
# ──────────────────────────────────────────────────────────────────────

def _is_reusable(page_role: str, slots: list[dict]) -> bool:
    """判断一页是否适合作为可复用的母版页。"""
    if page_role in ("cover", "closing"):
        return False
    if not slots:
        return False
    return True


# ──────────────────────────────────────────────────────────────────────
# 约束推断
# ──────────────────────────────────────────────────────────────────────

def _infer_constraints(page_role: str, slots: list[dict]) -> list[str]:
    """推断页面使用约束。"""
    constraints = []
    text_slots = [s for s in slots if s["kind"] == "text"]
    body_slots = [
        s
        for s in slots
        if s["kind"] == "text"
        and s.get("size_cm", {}).get("width", 0) > 15
        and s.get("size_cm", {}).get("height", 0) > 5
    ]

    if page_role == "cover":
        constraints.append("仅适用于封面页，不建议复用")
    if page_role == "closing":
        constraints.append("仅适用于结尾页，不建议复用")
    if page_role == "toc":
        constraints.append("适用于目录页")

    if len(text_slots) > 6:
        constraints.append("文本元素较多，正文超长时容易溢出")
    if not body_slots and page_role == "content":
        constraints.append("缺少大面积正文区域，适合放简短内容")

    return constraints


# ──────────────────────────────────────────────────────────────────────
# 布局描述生成
# ──────────────────────────────────────────────────────────────────────

def _describe_layout(slide, slots: list[dict], slide_width_emu: int = 0) -> str:
    """根据槽位的空间分布生成布局描述。"""
    if not slots:
        return "空白页"

    mid_x = emu_to_cm(slide_width_emu) / 2 if slide_width_emu else 0

    left_slots = []
    right_slots = []
    for s in slots:
        position = s.get("position_cm", {})
        size = s.get("size_cm", {})
        if "left" not in position or "width" not in size:
            continue
        center_x = position["left"] + size["width"] / 2
        if center_x < mid_x:
            left_slots.append(s)
        else:
            right_slots.append(s)

    text_count = sum(1 for s in slots if s["kind"] == "text")
    image_count = sum(1 for s in slots if s["kind"] == "image")
    chart_count = sum(1 for s in slots if s["kind"] == "chart")

    parts = []
    if left_slots and right_slots:
        left_kinds = set(s["kind"] for s in left_slots)
        right_kinds = set(s["kind"] for s in right_slots)
        l_desc = "/".join(sorted(left_kinds))
        r_desc = "/".join(sorted(right_kinds))
        parts.append(f"左右双栏（左{l_desc}，右{r_desc}）")
    elif text_count and image_count:
        parts.append("图文混排")
    elif chart_count:
        parts.append("图表页")
    elif text_count > 4:
        parts.append("多文本块")
    elif text_count:
        parts.append("文本页")

    if not parts:
        parts.append("标准布局")

    return "，".join(parts)


# ──────────────────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────────────────

def analyze_template_layouts(pptx_path: str, output_path: str = "") -> str:
    """
    分析 PPTX 模板的页型结构，输出 template_layouts.json。

    Args:
        pptx_path: PPTX 文件路径
        output_path: 可选，JSON 输出路径。为空则仅返回 JSON 字符串。

    Returns:
        JSON 格式的模板页型分析结果
    """
    prs = Presentation(pptx_path)
    total_slides = len(prs.slides)
    slide_width_cm = emu_to_cm(prs.slide_width)
    slide_height_cm = emu_to_cm(prs.slide_height)

    layouts = []

    for slide_index, slide in enumerate(prs.slides):
        page_role = _infer_page_role(slide, slide_index, total_slides)
        editable_slots, uneditable_slots = _extract_editable_slots(slide)
        all_slots = editable_slots + uneditable_slots
        layout_id = _generate_layout_id(page_role, slide_index, all_slots)
        reusable = _is_reusable(page_role, all_slots)
        constraints = _infer_constraints(page_role, all_slots)
        layout_desc = _describe_layout(slide, all_slots, prs.slide_width)

        layout_entry = {
            "layout_id": layout_id,
            "source_slide_index": slide_index,
            "name": layout_desc,
            "page_role": page_role,
            "is_reusable_template": reusable,
            "editable_slots": editable_slots,
            "uneditable_slots": uneditable_slots,
        }
        if constraints:
            layout_entry["hard_constraints"] = constraints

        layouts.append(layout_entry)

    result = {
        "template_file": os.path.basename(pptx_path),
        "slide_count": total_slides,
        "slide_size": {
            "width_cm": slide_width_cm,
            "height_cm": slide_height_cm,
        },
        "layouts": layouts,
    }

    result_json = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result_json)
        print(f"模板页型分析结果已保存至: {output_path}")

        summary_path = output_path.replace(".json", "_summary.json")
        summary = _build_summary(result)
        summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_json)
        print(f"精简摘要已保存至: {summary_path}")

    return result_json


def _build_summary(full_result: dict) -> dict:
    """
    从完整的 template_layouts 生成精简摘要，
    只保留大纲规划所需的信息，大幅缩减上下文长度。
    """
    summary_layouts = []
    for layout in full_result["layouts"]:
        slots_brief = []
        for s in layout["editable_slots"]:
            shape_id = s.get("shape_id", "")
            slots_brief.append(f"{s['kind']}_{shape_id}({s['kind']})")

        entry = {
            "layout_id": layout["layout_id"],
            "source_slide_index": layout["source_slide_index"],
            "page_role": layout["page_role"],
            "reusable": layout.get("is_reusable_template", True),
            "slots": slots_brief,
        }
        if layout.get("hard_constraints"):
            entry["constraints"] = layout["hard_constraints"]
        summary_layouts.append(entry)

    return {
        "template_file": full_result["template_file"],
        "slide_count": full_result["slide_count"],
        "layouts": summary_layouts,
    }
