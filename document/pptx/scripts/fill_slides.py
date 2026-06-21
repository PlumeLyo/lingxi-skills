"""
fill_slides - Step 4 脚本：基于大纲和模板页型，自动填充 PPTX 文本和替换图片

三个阶段分别对外暴露：
  build_edit_plan()  - 解析 outline + template_layouts → 生成编辑计划
  pick_image_size()  - 根据 shape 尺寸推算生图分辨率
  apply_edits()      - 逐页执行文本修改与图片替换

用法:
    import sys
    sys.path.insert(0, "skills/pptx/scripts")
    from fill_slides import build_edit_plan, apply_edits

    plan = build_edit_plan("workspace/xxx_outline.xml", "workspace/template_layouts.json")
    result = apply_edits("workspace/output/result.pptx", plan)
    print(result)
"""

import json
import math
import os
import re
from pathlib import Path

from pptx import Presentation

_MIN_PIXELS = 3_686_400


# ---------------------------------------------------------------------------
# Phase 1: 构建编辑计划
# ---------------------------------------------------------------------------


def _load_layouts(template_layouts_path: str) -> dict:
    """加载 template_layouts.json，返回 {layout_id: layout_dict} 映射。"""
    data = json.loads(Path(template_layouts_path).read_text(encoding="utf-8"))
    return {layout["layout_id"]: layout for layout in data.get("layouts", [])}


def build_edit_plan(outline_path: str, template_layouts_path: str) -> list[dict]:
    """
    解析 outline + template_layouts，生成逐页编辑计划。

    返回:
        [
            {
                "page_number": 1,
                "slide_index": 0,
                "text_edits": [{"shape_index": "2", "slot_id": "title_0", "content": "..."}],
                "picture_edits": [
                    {
                        "shape_index": "0",
                        "slot_id": "image_0",
                        "description": "...",
                        "gen_width": 1440,
                        "gen_height": 2560,
                        "image_path": None,
                    }
                ],
            },
            ...
        ]
    """
    content = Path(outline_path).read_text(encoding="utf-8")
    layouts_map = _load_layouts(template_layouts_path)

    page_pattern = r'<page\s+number="(\d+)">(.*?)</page>'
    pages = re.findall(page_pattern, content, re.DOTALL)
    if not pages:
        raise ValueError("outline 中未找到任何页面")

    element_pattern = (
        r'<element\s+type="([^"]+)"'
        r'(?:\s+slot_id="([^"]+)")?'
        r'(?:\s+chart_type="([^"]+)")?'
        r'\s*>(.*?)</element>'
    )

    edit_plan: list[dict] = []
    for page_num_str, page_content in pages:
        page_number = int(page_num_str)

        layout_id_match = re.search(
            r"<template_layout_id>(.*?)</template_layout_id>",
            page_content,
            re.DOTALL,
        )
        layout_id = layout_id_match.group(1).strip() if layout_id_match else None

        slot_info_map: dict[str, dict] = {}
        if layout_id and layout_id in layouts_map:
            for slot in layouts_map[layout_id].get("editable_slots", []):
                sid = slot.get("slot_id")
                if sid:
                    slot_info_map[sid] = slot

        text_edits: list[dict] = []
        picture_edits: list[dict] = []

        for m in re.finditer(element_pattern, page_content, re.DOTALL):
            elem_type = m.group(1).strip()
            slot_id = m.group(2).strip() if m.group(2) else None
            elem_content = m.group(4).strip()

            slot = slot_info_map.get(slot_id, {}) if slot_id else {}
            shape_index = slot.get("shape_index")

            if shape_index is None and slot_id:
                print(f"  ⚠ 第 {page_number} 页 slot_id={slot_id} 未找到 shape_index，跳过")
                continue

            if elem_type in ("textbox", "text"):
                text_edits.append({
                    "shape_index": shape_index,
                    "slot_id": slot_id,
                    "content": elem_content,
                })
            elif elem_type == "picture":
                position = slot.get("position", {})
                w_cm = position.get("width_cm", 10.0)
                h_cm = position.get("height_cm", 10.0)
                gen_w, gen_h = pick_image_size(w_cm, h_cm)
                picture_edits.append({
                    "shape_index": shape_index,
                    "slot_id": slot_id,
                    "description": elem_content,
                    "gen_width": gen_w,
                    "gen_height": gen_h,
                    "image_path": None,
                })

        edit_plan.append({
            "page_number": page_number,
            "slide_index": page_number - 1,
            "text_edits": text_edits,
            "picture_edits": picture_edits,
        })

    return edit_plan


# ---------------------------------------------------------------------------
# 图片尺寸计算
# ---------------------------------------------------------------------------


def pick_image_size(width_cm: float, height_cm: float) -> tuple[int, int]:
    """根据 shape 的实际宽高(cm)推算生图尺寸，确保总像素数不低于 _MIN_PIXELS。"""
    ratio = width_cm / height_cm
    w = math.sqrt(ratio * _MIN_PIXELS)
    h = w / ratio
    w, h = int(round(w)), int(round(h))
    while w * h < _MIN_PIXELS:
        if w >= h:
            w += 1
        else:
            h += 1
    return w, h


# ---------------------------------------------------------------------------
# Phase 3: 执行编辑
# ---------------------------------------------------------------------------


def _get_shape_by_index(slide, shape_index):
    """按索引定位 shape，支持多级索引（如 '1.2.0' 表示 GROUP 嵌套）。"""
    try:
        indices = [int(x) for x in str(shape_index).split(".")]
        shape = slide.shapes[indices[0]]
        for i in indices[1:]:
            shape = shape.shapes[i]
        return shape
    except (IndexError, AttributeError, ValueError, TypeError):
        return None


def _modify_text_keep_style(shape, new_text: str):
    """修改文本，保留原有字体样式。"""
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    if not tf.paragraphs:
        return
    first_para = tf.paragraphs[0]
    if first_para.runs:
        first_para.runs[0].text = new_text
        for run in first_para.runs[1:]:
            run.text = ""
    else:
        run = first_para.add_run()
        run.text = new_text
    for para in tf.paragraphs[1:]:
        for run in para.runs:
            run.text = ""


def _replace_picture_keep_position(slide, old_shape, new_image_path: str):
    """替换图片，保持位置、大小和 z-order。"""
    left, top, width, height = (
        old_shape.left,
        old_shape.top,
        old_shape.width,
        old_shape.height,
    )
    old_element = old_shape._element
    spTree = old_element.getparent()
    slide.shapes.add_picture(new_image_path, left, top, width, height)
    new_element = list(spTree)[-1]
    spTree.remove(new_element)
    old_element.addprevious(new_element)
    spTree.remove(old_element)


def apply_edits(
    pptx_path: str, edit_plan: list[dict], output_path: str = "",
) -> str:
    """
    逐页执行编辑计划：修改文本、替换图片。

    Args:
        pptx_path: Step 3 输出的 PPTX 文件路径
        edit_plan: build_edit_plan() 返回的编辑计划
        output_path: 另存路径（可选，默认覆盖原文件）

    Returns:
        JSON 格式的执行报告
    """
    prs = Presentation(pptx_path)
    text_count = 0
    pic_count = 0
    errors: list[str] = []

    for page_plan in edit_plan:
        slide_index = page_plan["slide_index"]
        page_number = page_plan["page_number"]

        if slide_index < 0 or slide_index >= len(prs.slides):
            errors.append(f"第 {page_number} 页: slide_index={slide_index} 超出范围")
            continue

        slide = prs.slides[slide_index]

        for text_edit in page_plan["text_edits"]:
            shape_index = text_edit["shape_index"]
            shape = _get_shape_by_index(slide, shape_index)
            if not shape:
                errors.append(
                    f"第 {page_number} 页: 未找到 shape index={shape_index}"
                )
                continue
            try:
                _modify_text_keep_style(shape, text_edit["content"])
                text_count += 1
            except Exception as e:
                errors.append(
                    f"第 {page_number} 页 index={shape_index} 文本修改失败: {e}"
                )

        for pic_edit in page_plan["picture_edits"]:
            image_path = pic_edit.get("image_path")
            if not image_path:
                continue
            shape_index = pic_edit["shape_index"]
            shape = _get_shape_by_index(slide, shape_index)
            if not shape:
                errors.append(
                    f"第 {page_number} 页: 未找到图片 shape index={shape_index}"
                )
                continue
            try:
                _replace_picture_keep_position(slide, shape, image_path)
                pic_count += 1
            except Exception as e:
                errors.append(
                    f"第 {page_number} 页 index={shape_index} 图片替换失败: {e}"
                )

    save_path = output_path or pptx_path
    prs.save(save_path)

    report = {
        "status": "success" if not errors else "partial",
        "output_path": save_path,
        "total_pages": len(edit_plan),
        "text_edits_applied": text_count,
        "images_replaced": pic_count,
        "errors": errors if errors else None,
    }

    report_json = json.dumps(report, ensure_ascii=False, indent=2)
    print(report_json)
    return report_json
