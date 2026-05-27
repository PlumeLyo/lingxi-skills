"""
Excel 表格摘要生成模块

提供基于 token 预算的智能表格摘要生成功能，支持多种数据源。
采用头中尾三段式采样策略，自动分配 token 预算。
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # summary.py 是第一个加载的文件，无需引用其他 API 模块

# ============ ↓↓↓ 以下代码与沙箱一致，同步时复制 ↓↓↓ ============

# 标准库导入（所有 API 文件共享）
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from collections import Counter
import json
import time
import builtins as _builtins
import math

# ============ 数据模型 ============

@dataclass
class CellStyle:
    """单元格样式信息"""
    font_name: str | None = None
    font_size: float | None = None
    font_color: str | None = None
    bold: bool | None = None
    bg_color: str | None = None
    horizontal_align: str | None = None
    vertical_align: str | None = None
    has_border: bool | None = None


@dataclass
class CellData:
    """单元格数据"""
    address: str                  # 单元格地址，如 "A1" 或 "B2:C3"（合并单元格）
    value: str                    # 单元格值
    row_index: int                # 行索引（0-based）
    col_index: int                # 列索引（0-based）
    formula_text: str | None = None # 单元格公式文本
    is_pic: bool = False            # 是否是图片
    num_format: str | None = None # 单元格格式
    style: CellStyle | None = None


@dataclass
class SheetPreview:
    """Sheet预览结果"""
    name: str
    used_range: str
    rows_count: int
    columns_count: int
    preview: str              # 格式化后的文本预览
    preview_rows: int
    preview_columns: int
    budget_stats: dict | None = None  # 可选的预算统计信息
    num_formats: dict[int, str] | None = None  # num_format 列表: {id: format_str}
    styles: dict[int, str] | None = None  # 样式列表: {id: style_str}
    formulas: dict[int, str] | None = None  # 公式列表: {id: formula_str}


@dataclass
class Region:
    """区域信息（内部使用）"""
    row_from: int
    row_to: int
    rows: int
    range_addr: str
    token_budget: float


# ============ Protocol 定义 ============
@runtime_checkable
class SheetDataSource(Protocol):
    """Sheet 数据源协议"""

    @property
    def name(self) -> str:
        """Sheet名称"""
        ...

    @property
    def used_range(self) -> str:
        """使用范围，如 "A1:F100" """
        ...

    def get_cells(self, range_addr: str) -> list[list[CellData]]:
        """
        根据 range 地址获取单元格数据
        返回二维数组，外层是行，内层是列
        """
        ...

# ============ 工具函数 ============
def _et_core_execute(body: dict) -> dict:
    command = body.get('command', '')
    param = body.get('param', {})
    data = _call_core_execute(command, param)

    result = data.get('result')
    if result != 0 and result != "ok":
        raise Exception(f"{result}: {data.get('msg', '未知错误')}")
    return data


def base26_to_decimal(col_str: str) -> int:
    """列名转数字：A->1, B->2, ..., AA->27"""
    col_str = col_str.upper()
    col_num = 0
    for char in col_str:
        col_num = col_num * 26 + (ord(char) - ord('A') + 1)
    return col_num


def parse_range_address(range_addr: str) -> tuple[int, int, int, int]:
    """
    解析 range 地址 "A1:F100"

    Returns:
        (row_from, col_from, row_to, col_to) - 0-based 索引
    """
    import re

    range_addr = range_addr.replace(" ", "")

    if ":" in range_addr:
        # 范围地址
        parts = range_addr.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid range format: {range_addr}")

        start_match = re.match(r'^([A-Z]+)(\d+)$', parts[0].upper())
        end_match = re.match(r'^([A-Z]+)(\d+)$', parts[1].upper())

        if not start_match or not end_match:
            raise ValueError(f"Invalid range format: {range_addr}")

        col_from = base26_to_decimal(start_match.group(1)) - 1
        row_from = int(start_match.group(2)) - 1
        col_to = base26_to_decimal(end_match.group(1)) - 1
        row_to = int(end_match.group(2)) - 1

    else:
        # 单个单元格
        match = re.match(r'^([A-Z]+)(\d+)$', range_addr.upper())
        if not match:
            raise ValueError(f"Invalid cell address: {range_addr}")

        col_from = col_to = base26_to_decimal(match.group(1)) - 1
        row_from = row_to = int(match.group(2)) - 1

    return row_from, col_from, row_to, col_to


def decimal_to_base26(col_num: int) -> str:
    """数字转列名：1->A, 2->B, ..., 27->AA"""
    if col_num <= 0:
        raise ValueError("列号必须大于0")

    result = ""
    while col_num > 0:
        col_num, remainder = divmod(col_num - 1, 26)
        result = chr(65 + remainder) + result
    return result


def format_cell_address(row: int, col: int) -> str:
    """格式化单个单元格地址，如 "A1" (0-based索引)"""
    return f"{decimal_to_base26(col + 1)}{row + 1}"


def format_range_address(row_from: int, col_from: int, row_to: int, col_to: int) -> str:
    """格式化 range 地址为 "A1:F100" 格式 (0-based索引)"""
    return f"{format_cell_address(row_from, col_from)}:{format_cell_address(row_to, col_to)}"


def _font_size_dominant(cells_data: list[list[CellData]]) -> int | None:
    """
    查找主导字体大小
    如果某个字体大小比第二常见的多 50% 以上，返回它，否则返回 None
    """
    sizes = []
    for row in cells_data:
        for cell in row:
            if cell and cell.style and cell.style.font_size:
                sizes.append(cell.style.font_size)

    if len(sizes) == 0:
        return None
    if len(sizes) == 1:
        return sizes[0]

    counter = Counter(sizes)
    if len(counter) == 1:
        return sizes[0]

    most_common = counter.most_common(2)
    first, second = most_common[0], most_common[1]

    if first[1] > second[1] * 1.5:
        return first[0]

    return None


def calculate_token(content: str) -> int:
    """
    计算字符串的 token 数量
    ASCII 字符: 0.3 token
    非 ASCII 字符: 0.6 token
    """
    count = 0.0
    for c in content:
        if c.isascii():
            count += 0.3
        else:
            count += 0.6
    return int(math.ceil(count))


def _take_chars_within_budget(text: str, budget: int, from_start: bool = True) -> str:
    """
    在预算内尽可能多地获取字符

    Args:
        text: 源文本
        budget: token 预算
        from_start: True 从头开始，False 从尾开始

    Returns:
        截取的文本
    """
    if not text:
        return ''

    accumulated = 0
    result = []
    chars = text if from_start else reversed(text)

    for char in chars:
        token_cost = 0.3 if char.isascii() else 0.6
        if accumulated + token_cost > budget:
            break
        accumulated += token_cost
        result.append(char)

    return ''.join(result) if from_start else ''.join(reversed(result))


def _truncate_text(text: str, budget: int) -> str:
    """
    头尾采样截断文本
    头部占 60%，尾部占 30%，中间用 ... 连接
    """
    head_part = _take_chars_within_budget(text, int(budget * 0.6), from_start=True)
    tail_part = _take_chars_within_budget(text, int(budget * 0.3), from_start=False)
    return f"{head_part}...{tail_part}"



class SummaryBuilder:
    """表格摘要生成器"""

    def __init__(self,
                 token_budget: int = 30000,
                 max_rows: int = 1000,
                 max_columns: int = 100,
                 head_ratio: float = 0.5,
                 middle_ratio: float = 0.2,
                 tail_ratio: float = 0.3):
        """
        初始化摘要生成器

        Args:
            token_budget: 总 token 预算
            max_rows: 最大采样行数
            max_columns: 最大采样列数
            head_ratio: 头部区域比例
            middle_ratio: 中间区域比例
            tail_ratio: 尾部区域比例
        """
        self.token_budget = token_budget
        self.max_rows = max_rows
        self.max_columns = max_columns
        self.head_ratio = head_ratio
        self.middle_ratio = middle_ratio
        self.tail_ratio = tail_ratio


    def build_summary(self,
                     sheets: list[SheetDataSource],
                     active_sheet_name: str = "") -> str:
        """构建多个 sheets 的摘要

        Args:
            sheets: Sheet 数据源列表
            active_sheet_name: 活动 sheet 名称（可选）

        Returns:
            Markdown 格式的摘要文本
        """
        previews = []
        total_sheets_count = len(sheets)
        remaining_tokens = float(self.token_budget)
        pending_sheets = list(sheets)

        if active_sheet_name:
            active_token_budget = remaining_tokens / 2
            for i, sheet in enumerate(pending_sheets):
                if sheet.name != active_sheet_name:
                    continue
                try:
                    preview, tokens = self._process_sheet(sheet, int(active_token_budget))
                    previews.append(preview)
                    remaining_tokens -= tokens
                    pending_sheets = pending_sheets[:i] + pending_sheets[i+1:]
                except Exception as e:
                    print(f"Error processing active sheet {sheet.name}: {e}")
                break

        token_per_sheet = max(1, int(remaining_tokens / len(pending_sheets))) if pending_sheets else 0
        for sheet in pending_sheets:
            if remaining_tokens <= 0:
                previews.append(SheetPreview(
                    name=sheet.name, used_range=sheet.used_range,
                    rows_count=0, columns_count=0,
                    preview="", preview_rows=0, preview_columns=0,
                ))
                continue
            try:
                preview, used_tokens = self._process_sheet(sheet, token_per_sheet)
                previews.append(preview)
                remaining_tokens -= used_tokens
            except Exception as e:
                print(f"Error processing sheet {sheet.name}: {e}")

        return self._render_markdown(previews, total_sheets_count, active_sheet_name)

    def _render_markdown(self, previews, sheets_count, active_sheet_name=""):
        lines = [
            "# Document context",
            "## 表格文件预览",
            f"- **总工作表数:** {sheets_count}",
        ]
        if active_sheet_name:
            lines.append(f"- **当前活动工作表:** `{active_sheet_name}`")
        lines.append("---")

        for sheet in previews:
            lines.append(f"### 工作表名称: `{sheet.name}`")
            lines.append(f"- 工作表使用范围: {sheet.used_range} ({sheet.rows_count} rows × {sheet.columns_count} columns)")
            if sheet.preview:
                lines.append(f"- 文本预览 ({sheet.preview_rows} of {sheet.rows_count} rows, {sheet.preview_columns} of {sheet.columns_count} columns):")
                lines.append("```")
                lines.append(sheet.preview)
                lines.append("```")
                if sheet.num_formats:
                    lines.append(f"#### `{sheet.name}` 数字格式列表:")
                    for id, fmt in sheet.num_formats.items():
                        lines.append(f"- NUMFMT{id}: {fmt}")
                if sheet.styles:
                    lines.append(f"#### `{sheet.name}` 单元格样式列表:")
                    for id, style in sheet.styles.items():
                        lines.append(f"- STY{id}: {style}")
                if sheet.formulas:
                    lines.append(f"#### `{sheet.name}` 公式列表:")
                    for id, formula in sheet.formulas.items():
                        lines.append(f"- FMLA{id}: {formula}")
            lines.append("")
        return '\n'.join(lines)

    def build_range_summary(self, range_data: SheetDataSource) -> str:
        """
        构建单个 range 的简单摘要

        Args:
            range_data: Sheet 数据源

        Returns:
            str: 摘要文本
        """
        preview, _ = self._process_sheet(range_data, self.token_budget)
        lines = [
            f"# Sheet: {preview.name}",
            f"# Range: {preview.used_range}",
            f"# Size: {preview.rows_count} rows × {preview.columns_count} columns",
            f"# Preview: {preview.preview_rows} rows × {preview.preview_columns} columns",
            "",
            preview.preview,
        ]
        if preview.num_formats:
            lines.append(f"# Num Formats:")
            for id, fmt in preview.num_formats.items():
                lines.append(f"- NUMFMT{id}: {fmt}")
            lines.append("")
        if preview.styles:
            lines.append(f"# Styles:")
            for id, style in preview.styles.items():
                lines.append(f"- STY{id}: {style}")
            lines.append("")
        if preview.formulas:
            lines.append(f"# Formulas:")
            for id, formula in preview.formulas.items():
                lines.append(f"- FMLA{id}: {formula}")
        return '\n'.join(lines)

    def _process_sheet(self,
                       sheet: SheetDataSource,
                       token_budget: int) -> tuple[SheetPreview, int]:
        """
        处理单个 sheet

        Returns:
            (SheetPreview, used_tokens)
        """
        # 解析 used_range
        try:
            row_from, col_from, row_to, col_to = parse_range_address(sheet.used_range)
        except Exception as e:
            # 空 sheet 或无效 range
            return SheetPreview(
                name=sheet.name,
                used_range='N/A',
                rows_count=0,
                columns_count=0,
                preview='N/A',
                preview_rows=0,
                preview_columns=0,
                budget_stats={}
            ), 0

        total_rows = row_to - row_from + 1
        total_cols = col_to - col_from + 1

        all_rows = []
        total_tokens = 0
        preview_rows = 0
        preview_columns = 0

        # 初始化聚类字典
        num_formats_dict = {}  # {format_str: id}
        styles_dict = {}  # {style_str: id}
        formulas_dict = {}  # {formula_str: id}

        # 判断是否需要采样
        if total_rows <= self.max_rows:
            # 不需要采样，全部处理
            range_addr = sheet.used_range
            rows, tokens, num_cols = self._process_region(
                sheet, range_addr, token_budget,
                num_formats_dict, styles_dict, formulas_dict
            )
            all_rows = rows
            total_tokens = tokens
            preview_rows = len(rows)
            preview_columns = num_cols
            if preview_rows < total_rows:
                all_rows.append(f'| ... 省略 {total_rows - preview_rows} 行 (第{preview_rows+1}-{total_rows}行) ... |')
        else:
            # 需要采样：head/middle/tail
            regions = self._calculate_regions(row_from, row_to, col_from, col_to, token_budget)

            previous_remaining_tokens = 0
            region_stats = {}

            for i, region in enumerate(regions):
                budget = int(region.token_budget + previous_remaining_tokens)
                rows, tokens, num_cols = self._process_region(
                    sheet, region.range_addr, budget,
                    num_formats_dict, styles_dict, formulas_dict
                )
                all_rows.extend(rows)
                preview_rows += len(rows)
                preview_columns = max(preview_columns, num_cols)

                region_name = ['head', 'middle', 'tail'][i]
                region_stats[region_name] = {
                    'budget': budget,
                    'used': tokens,
                    'surplus': budget - tokens
                }

                total_tokens += tokens
                previous_remaining_tokens = max(0, budget - tokens)

                # 添加省略提示
                if i < len(regions) - 1:
                    next_region_row_from = regions[i + 1].row_from
                    curr_region_row_to = min(region.row_to, region.row_from + len(rows) - 1)
                    if next_region_row_from > curr_region_row_to + 1:
                        omitted_rows = next_region_row_from - curr_region_row_to - 1
                        omitted_start_row = curr_region_row_to + 2
                        omitted_end_row = next_region_row_from
                        all_rows.append(f'| ... 省略 {omitted_rows} 行 (第{omitted_start_row}-{omitted_end_row}行) ... |')
                # 最后一个区域，且 preview 行数小于区域总行数，需要省略提示
                elif len(rows) < region.rows:
                    omitted_rows = region.rows - len(rows)
                    omitted_start_row = region.row_from + len(rows) + 1
                    omitted_end_row = region.row_to + 1
                    all_rows.append(f'| ... 省略 {omitted_rows} 行 (第{omitted_start_row}-{omitted_end_row}行) ... |')

        # 反转字典: {id: content}
        num_formats = {v: k for k, v in num_formats_dict.items()} if num_formats_dict else None
        styles = {v: k for k, v in styles_dict.items()} if styles_dict else None
        formulas = {v: k for k, v in formulas_dict.items()} if formulas_dict else None

        return SheetPreview(
            name=sheet.name,
            used_range=sheet.used_range,
            rows_count=total_rows,
            columns_count=total_cols,
            preview='\n'.join(all_rows),
            preview_rows=preview_rows,
            preview_columns=preview_columns,
            budget_stats=region_stats if total_rows > self.max_rows else None,
            num_formats=num_formats,
            styles=styles,
            formulas=formulas
        ), total_tokens

    def _calculate_regions(self,
                          row_from: int,
                          row_to: int,
                          col_from: int,
                          col_to: int,
                          token_budget: int) -> list[Region]:
        """计算 head/middle/tail 三个区域"""
        total_rows = row_to - row_from + 1

        head_count = int(self.max_rows * self.head_ratio)
        middle_count = int(self.max_rows * self.middle_ratio)
        tail_count = self.max_rows - head_count - middle_count

        # 中间区域取数据的中心位置
        middle_start = row_from + head_count + (total_rows - tail_count - head_count) // 2
        middle_end = middle_start + middle_count - 1

        return [
            Region(
                row_from=row_from,
                row_to=row_from + head_count - 1,
                rows=head_count,
                range_addr=format_range_address(row_from, col_from, row_from + head_count - 1, col_to),
                token_budget=max(float(token_budget) * self.head_ratio, 100) # 至少 100 token
            ),
            Region(
                row_from=middle_start,
                row_to=middle_end,
                rows=middle_count,
                range_addr=format_range_address(middle_start, col_from, middle_end, col_to),
                token_budget=max(float(token_budget) * self.middle_ratio, 100) # 至少 100 token
            ),
            Region(
                row_from=row_to - tail_count + 1,
                row_to=row_to,
                rows=tail_count,
                range_addr=format_range_address(row_to - tail_count + 1, col_from, row_to, col_to),
                token_budget=max(float(token_budget) * self.tail_ratio, 100) # 至少 100 token
            )
        ]

    def _process_region(self,
                       sheet: SheetDataSource,
                       range_addr: str,
                       token_budget: int,
                       num_formats_dict: dict,
                       styles_dict: dict,
                       formulas_dict: dict) -> tuple[list[str], int, int]:
        """
        处理一个区域

        Returns:
            (rows_text, used_tokens, max_columns)
        """
        cells = sheet.get_cells(range_addr)

        rows = []
        total_tokens = 0
        max_columns = 0

        # 查找主导字体大小（用于过滤过于普遍的样式）
        font_size_dominant = _font_size_dominant(cells)

        remaining_rows = len(cells)
        for row_cells in cells:
            # 动态分配该行的 token 预算
            row_budget = (token_budget - total_tokens) / remaining_rows if remaining_rows > 0 else 0
            if row_budget <= 0:
                break

            # 如果列数太多，做列采样（取前半和后半）
            sampled_cells = row_cells
            if len(row_cells) > int(self.max_columns * 1.2):
                half = self.max_columns // 2
                sampled_cells = row_cells[:half] + row_cells[len(row_cells) - half:]

            row_text, row_tokens = self._process_cells(
                sampled_cells, int(row_budget), font_size_dominant,
                num_formats_dict, styles_dict, formulas_dict
            )
            if row_text:
                rows.append(row_text)
                total_tokens += row_tokens
                max_columns = max(max_columns, len(sampled_cells))

            remaining_rows -= 1

        return rows, total_tokens, max_columns

    def _process_cells(self,
                      cells: list[CellData],
                      token_budget: int,
                      font_size_dominant: int | None,
                      num_formats_dict: dict,
                      styles_dict: dict,
                      formulas_dict: dict) -> tuple[str, int]:
        """
        处理一行的多个单元格

        Returns:
            (formatted_row_text, used_tokens)
        """
        parts = []
        total_tokens = 0
        remaining_cells = len(cells)

        for cell in cells:
            # 动态分配该 cell 的 token 预算，至少 20
            cell_budget = max(20, (token_budget - total_tokens) // remaining_cells if remaining_cells > 0 else 20)

            cell_text, cell_tokens = self._process_cell(
                cell, cell_budget, font_size_dominant,
                num_formats_dict, styles_dict, formulas_dict
            )
            parts.append(f"{cell_text}")
            total_tokens += cell_tokens
            remaining_cells -= 1

        return '| ' + ' | '.join(parts) + ' |', total_tokens

    def _process_cell(self,
                     cell: CellData,
                     token_budget: int,
                     font_size_dominant: int | None,
                     num_formats_dict: dict,
                     styles_dict: dict,
                     formulas_dict: dict) -> tuple[str, int]:
        """
        处理单个单元格

        Returns:
            (formatted_cell_text, used_tokens)
        """
        # 格式化基本信息
        base_info = f"{cell.address}:{json.dumps(cell.value, ensure_ascii=False)[1:-1]}"

        # 收集样式信息并获取 ID
        meta_parts = []

        # 处理 num_format
        if cell.num_format and cell.num_format not in ['General', 'G/通用格式']:
            if cell.num_format not in num_formats_dict:
                num_formats_dict[cell.num_format] = len(num_formats_dict) + 1
            numfmt_id = num_formats_dict[cell.num_format]
            meta_parts.append(f"NUMFMT{numfmt_id}")

        # 处理样式
        style_str = ""
        if cell.style:
            style_items = []

            # 字体名称
            if cell.style.font_name:
                style_items.append(f"font:{cell.style.font_name}")

            # 太普遍的字体大小不显示
            if cell.style.font_size and (font_size_dominant is None or cell.style.font_size != font_size_dominant):
                style_items.append(f"size:{cell.style.font_size:.0f}")

            # 纯黑色的字体不显示
            if cell.style.font_color and cell.style.font_color != '#FF000000':
                # 去掉 Alpha 通道（Server API 返回的是 ARGB 格式，需要去掉前两位）
                color_str = cell.style.font_color
                if color_str.startswith('#') and len(color_str) == 9:
                    color_str = '#' + color_str[3:]
                style_items.append(f"color:{color_str}")

            if cell.style.bold:
                style_items.append("bold:true")

            if cell.style.bg_color:
                # Server API 返回的是 ARGB 格式，需要去掉前两位
                color_str = cell.style.bg_color
                if color_str.startswith('#') and len(color_str) == 9:
                    color_str = '#' + color_str[3:]
                style_items.append(f"bg:{color_str}")

            # 水平对齐
            if cell.style.horizontal_align:
                style_items.append(f"h-align:{cell.style.horizontal_align}")

            # 垂直对齐
            if cell.style.vertical_align:
                style_items.append(f"v-align:{cell.style.vertical_align}")

            # 边框
            if cell.style.has_border:
                style_items.append("border:true")

            if style_items:
                style_str = ",".join(style_items)
                if style_str not in styles_dict:
                    styles_dict[style_str] = len(styles_dict) + 1
                style_id = styles_dict[style_str]
                meta_parts.append(f"STY{style_id}")

        # 处理公式
        if cell.formula_text:
            if cell.formula_text not in formulas_dict:
                formulas_dict[cell.formula_text] = len(formulas_dict) + 1
            formula_id = formulas_dict[cell.formula_text]
            meta_parts.append(f"FMLA{formula_id}")

        # 组合元数据
        meta_info = ""
        if meta_parts:
            meta_info = ":<" + ":".join(meta_parts) + ">"

        full_content = base_info + meta_info
        actual_tokens = calculate_token(full_content)

        # 判断是否需要截断
        if actual_tokens <= token_budget:
            return full_content, actual_tokens
        elif actual_tokens <= token_budget * 1.5:
            # 轻度超标，容忍通过（避免过度截断损失信息）
            return full_content, actual_tokens
        else:
            # 严重超标，对值部分进行截断
            value_str = json.dumps(cell.value, ensure_ascii=False)[1:-1]
            truncated_value = _truncate_text(value_str, token_budget)
            truncated_content = f"{cell.address},{truncated_value}{meta_info}"
            return truncated_content, calculate_token(truncated_content)


class ServerAPISheetDataSource:
    """Server API 数据源"""

    def __init__(self,
                 sheet_id: int,
                 sheet_name: str,
                 used_range_str: str):
        """
        Args:
            sheet_id: Sheet ID
            sheet_name: Sheet 名称
            used_range_str: 使用范围，如 "A1:F100"
        """
        self._sheet_id = sheet_id
        self._sheet_name = sheet_name
        self._used_range_str = used_range_str

    @property
    def name(self) -> str:
        return self._sheet_name

    @property
    def used_range(self) -> str:
        return self._used_range_str

    def get_cells(self, range_addr: str) -> list[list[CellData]]:
        """获取指定范围的单元格数据"""
        row_from, col_from, row_to, col_to = parse_range_address(range_addr)

        # 从 API 获取数据
        range_data = self._fetch_from_api(row_from, col_from, row_to, col_to)

        # 构建二维数组
        rows_count = row_to - row_from + 1
        cols_count = col_to - col_from + 1
        result = [[None] * cols_count for _ in range(rows_count)]

        # 填充数据
        for cell_info in range_data:
            cell_row_from = cell_info['rowFrom']
            cell_col_from = cell_info['colFrom']
            cell_row_to = cell_info['rowTo']
            cell_col_to = cell_info['colTo']

            # 判断是否合并单元格
            is_merged = (cell_row_from != cell_row_to or cell_col_from != cell_col_to)

            if is_merged:
                address = format_range_address(cell_row_from, cell_col_from, cell_row_to, cell_col_to)
            else:
                address = format_cell_address(cell_row_from, cell_col_from)

            cell_data = CellData(
                address=address,
                value=cell_info.get('cellText', ''),
                row_index=cell_row_from,
                col_index=cell_col_from,
                formula_text=cell_info.get('fmlaText', None),
                is_pic=cell_info.get('isCellPic', False),
                num_format=cell_info.get('numFormat', None),
                style=CellStyle(
                    font_name=cell_info.get('fonts', {}).get('font_east_asia', None),
                    font_size=cell_info.get('fonts', {}).get('size', None),
                    font_color=cell_info.get('fonts', {}).get('color', None),
                    bold=False, # Server API 现在还不返回粗体
                    bg_color=cell_info.get('cell_background_color', None),
                    horizontal_align=cell_info.get('alignment', {}).get('horizontal', None),
                    vertical_align=cell_info.get('alignment', {}).get('vertical', None),
                    has_border=cell_info.get('hasBorder', False),
                )
            )

            # 只在第一个位置放置 CellData
            rel_row = cell_row_from - row_from
            rel_col = cell_col_from - col_from
            if 0 <= rel_row < rows_count and 0 <= rel_col < cols_count:
                result[rel_row][rel_col] = cell_data

        # 填充空单元格
        for i in range(rows_count):
            for j in range(cols_count):
                if result[i][j] is None:
                    result[i][j] = CellData(
                        address=format_cell_address(row_from + i, col_from + j),
                        value='',
                        row_index=row_from + i,
                        col_index=col_from + j,
                        style=None
                    )

        return result

    def _fetch_from_api(self,
                       row_from: int,
                       col_from: int,
                       row_to: int,
                       col_to: int,
                       retry: int = 3):
        """从 API 获取数据，支持重试"""
        req_body = {
            "command": "http.et.getRangeData",
            'param': {
                "sheetId": self._sheet_id,
                "range": {
                    "rowFrom": row_from,
                    "rowTo": row_to,
                    "colFrom": col_from,
                    "colTo": col_to
                }
            },
        }

        for attempt in range(retry):
            try:
                resp = _et_core_execute(req_body)
                if resp is None or resp.get('detail', {}).get('rangeData') is None:
                    return []
                return resp['detail']['rangeData']
            except Exception as e:
                if attempt == retry - 1:
                    raise e
                time.sleep(1)

        return []


def summarize_workbook(active_sheet: str = "", token_budget: int = 6144) -> str:
    """生成当前工作簿的多 sheet 摘要

    依赖 builtins.__core_execute 已通过 HTTPMockBuiltins 注入。

    Args:
        active_sheet: 当前活动工作表名称（会分配更多 token 预算）
        token_budget: 总 token 预算

    Returns:
        Markdown 格式的摘要文本
    """
    sheets_resp = _et_core_execute({
        "command": "http.et.getSheetsInfo",
        "param": {},
    })

    data_sources = []
    for info in sheets_resp.get('detail', {}).get('sheetsInfo', []):
        if not info.get('isVisible', False):
            continue

        sheet_id = info['sheetId']
        sheet_name = info['sheetName']
        row_from = info['rowFrom']
        row_to = info['rowTo']
        col_from = info['colFrom']
        col_to = info['colTo']

        if row_from > row_to or col_from > col_to:
            continue

        used_range_str = format_range_address(row_from, col_from, row_to, col_to)
        data_sources.append(ServerAPISheetDataSource(
            sheet_id=sheet_id,
            sheet_name=sheet_name,
            used_range_str=used_range_str,
        ))

    builder = SummaryBuilder(token_budget=token_budget, max_rows=1000, max_columns=200)
    return builder.build_summary(data_sources, active_sheet_name=active_sheet)
