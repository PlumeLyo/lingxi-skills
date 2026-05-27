# 依赖说明（拼接执行时已在命名空间中）：
# - json, Literal 等标准库来自 summary.py / _utils.py
# - _make_setattr_guard, _decimal_to_base26, _PX_TO_TWIP 来自 _utils.py

class Border:
    """边框配置，用于设置单元格边框样式。
    
    通过 `range.format.border` 获取实例。所有属性仅支持写入。
    
    Example:
        >>> range.format.border.style = 'double'
        >>> range.format.border.color = '#ff0000'
        >>> range.format.border.type = 'outer'
    """

    __setattr__ = _make_setattr_guard(
        frozenset(['_range', '_pending', 'type', 'style', 'color']),
        ['type', 'style', 'color']
    )
    
    def __init__(self, range_ref: 'Range'):
        self._range = range_ref
        self._pending = {}  # 记录待应用的属性

    @property
    def type(self) -> str:
        """[只写]边框类型: 'all'(全部) / 'outer'(外边框) / 'inner'(内边框)"""
        raise AttributeError("type 属性只支持写入")

    @type.setter
    def type(self, value: str):
        self._pending['type'] = value
        self._range._apply_border(self._pending)
        self._pending = {}

    @property
    def style(self) -> str:
        """[只写]线条样式: 'none' / 'thin' / 'dashed' / 'dotted' / 'double'"""
        raise AttributeError("style 属性只支持写入")

    @style.setter
    def style(self, value: str):
        self._pending['style'] = value
        self._range._apply_border(self._pending)
        self._pending = {}

    @property
    def color(self) -> str:
        """[只写]边框颜色，如 '#000000'"""
        raise AttributeError("color 属性只支持写入")

    @color.setter
    def color(self, value: str):
        self._pending['color'] = value
        self._range._apply_border(self._pending)
        self._pending = {}

class Font:
    """字体设置，用于设置单元格字体样式。
    
    通过 `range.format.font` 获取实例。所有属性仅支持写入。

    Example:
        >>> range.format.font.bold = True
        >>> range.format.font.color = '#ff0000'
        >>> range.format.font.size = 12
    """

    __setattr__ = _make_setattr_guard(
        frozenset(['_range', 'bold', 'italic', 'color', 'name', 'strikeout', 'size']),
        ['bold', 'italic', 'color', 'name', 'strikeout', 'size']
    )

    def __init__(self, range_ref: 'Range'):
        self._range = range_ref

    @property
    def bold(self) -> bool:
        """[只写]是否加粗"""
        raise AttributeError("bold 属性只支持写入")

    @bold.setter
    def bold(self, value: bool):
        """设置是否加粗"""
        self._range._apply_style({'font': {'bold': value}})

    @property
    def italic(self) -> bool:
        """[只写]是否斜体"""
        raise AttributeError("italic 属性只支持写入")

    @italic.setter
    def italic(self, value: bool):
        """设置是否斜体"""
        self._range._apply_style({'font': {'italic': value}})

    @property
    def color(self) -> str:
        """[只写]字体颜色，如 '#ff0000'"""
        raise AttributeError("color 属性只支持写入")

    @color.setter
    def color(self, value: str):
        """设置字体颜色，如 '#ff0000'"""
        self._range._apply_style({'font': {'color': value}})

    @property
    def name(self) -> str:
        """[只写]字体名称，如 '宋体'"""
        raise AttributeError("name 属性只支持写入")

    @name.setter
    def name(self, value: str):
        """设置字体名称，如 '宋体'"""
        self._range._apply_style({'font': {'name': value}})

    @property
    def strikeout(self) -> bool:
        """[只写]是否显示删除线"""
        raise AttributeError("strikeout 属性只支持写入")

    @strikeout.setter
    def strikeout(self, value: bool):
        """设置是否显示删除线"""
        self._range._apply_style({'font': {'strikeout': value}})

    @property
    def size(self) -> int:
        """字号大小，如 12。读取返回当前字号；设置如 font.size = 14"""
        code = f'''
let sheet = Sheets.Item({json.dumps(self._range._sheet_name, ensure_ascii=False)});
let targetRange = sheet.Range({json.dumps(self._range.address, ensure_ascii=False)});
let fontSize = targetRange.Font.Size;
return fontSize;'''
        res = self._range._ctx.evaluate_script_v2(code)
        if not res.get('success', True):
            error_msg = res.get('error', '未知错误')
            print(f"获取字体大小失败, {error_msg}")
            return 0

        if "data" in res:
            if 'result' in res['data']:
                return res['data']['result']
        print("获取字体大小失败, res:", res)
        return 0

    @size.setter
    def size(self, value: int) -> None:
        """设置字号大小，如 12、14、16"""
        code = f'''
let sheet = Sheets.Item({json.dumps(self._range._sheet_name, ensure_ascii=False)});
let range = sheet.Range({json.dumps(self._range.address, ensure_ascii=False)});
range.Font.Size = {value};
'''
        # 字体高度（单位Twip(缇)），1缇=1/20磅
        # self._range._apply_style({'font': {'dyHeight': value * 20}})
        log = f"字体大小已设置为 {value}"
        self._range._ctx.queue_script(code.strip(), log_message=log)

class Fill:
    """填充设置，用于设置单元格填充样式。
    
    通过 `range.format.fill` 获取实例。
    
    Example:
        >>> range.format.fill.color = '#ffff00'
    """

    __setattr__ = _make_setattr_guard(
        frozenset(['_range', 'color']),
        ['color']
    )

    def __init__(self, range_ref: 'Range'):
        self._range = range_ref

    @property
    def color(self) -> str:
        """[只写]背景色，如 '#ffff00'"""
        raise AttributeError("color 属性只支持写入")

    @color.setter
    def color(self, value: str):
        """设置背景色，如 '#ffff00'"""
        self._range._apply_style({'fill': {'back': value}})


class Format:
    """样式容器，用于设置字体、填充、边框、对齐等格式。
    
    通过 `range.format` 获取实例。
    
    Example:
        >>> rng.format.font.bold = True
        >>> rng.format.fill.color = '#4472C4'
        >>> rng.format.v_align = 'center'
        >>> rng.format.wrap_text = True
        >>> rng.format.h_align = 'center'
        >>> rng.format.number_format = '0.00%'
        >>> rng.format.border.type = 'all'
    """

    __setattr__ = _make_setattr_guard(
        frozenset(['_range', '_font', '_fill', '_border', 'font', 'fill', 'border', 
                   'h_align', 'v_align', 'wrap_text', 'number_format', 'column_width', 'row_height']),
        ['font', 'fill', 'border', 'h_align', 'v_align', 'wrap_text', 'number_format', 'column_width', 'row_height']
    )

    def __init__(self, range_ref: 'Range'):
        self._range = range_ref
        self._font = Font(range_ref)
        self._fill = Fill(range_ref)
        self._border = Border(range_ref)

    @property
    def font(self) -> Font:
        """字体格式对象，通过 Font 对象的 font.bold / font.color 等属性设置。"""
        return self._font

    @property
    def fill(self) -> Fill:
        """填充格式对象，通过 Fill 对象的 fill.color 设置。"""
        return self._fill

    @property
    def border(self):
        """边框格式对象，通过 Border 对象的 border.type / border.style / border.color 设置。"""
        return self._border

    @property
    def h_align(self) -> str:
        """[只写]水平对齐，可选 'left'/'center'/'right'"""
        raise AttributeError("h_align 属性只支持写入")

    @h_align.setter
    def h_align(self, value: Literal['left', 'center', 'right']):
        """设置水平对齐：'left'/'center'/'right'。"""
        self._range._apply_style({'h_align': value})

    @property
    def v_align(self) -> str:
        """[只写]垂直对齐，可选 'top'/'center'/'bottom'"""
        raise AttributeError("v_align 属性只支持写入")

    @v_align.setter
    def v_align(self, value: Literal['top', 'center', 'bottom']):
        """设置垂直对齐：'top'/'center'/'bottom'。"""
        self._range._apply_style({'v_align': value})

    @property
    def wrap_text(self) -> bool:
        """[只写]是否自动换行"""
        raise AttributeError("wrap_text 属性只支持写入")

    @wrap_text.setter
    def wrap_text(self, value: bool):
        """设置是否自动换行。"""
        self._range._apply_style({'wrap': value})

    @property
    def number_format(self) -> str:
        """[只写]数字/日期显示格式代码。

        常用格式:
            数字: '0.00'(两位小数), '#,##0'(千分位), '0.0%'(百分比)
            日期: 'yyyy-mm-dd', 'dd/mm/yy', 'yyyy年m月d日'
            时间: 'hh:mm', 'hh:mm:ss', 'h:mm AM/PM'
            特殊: '@'(强制文本), '00000'(保留前导零)
        """
        raise AttributeError("number_format 属性只支持写入")

    @number_format.setter
    def number_format(self, value: str):
        """设置单元格的数字/日期显示格式。
       
        Args:
            value: 格式字符串，遵循 Excel 格式代码规范
        
        重要说明:
            当你将日期或数值写入单元格后，显示格式可能会改变。
            如果需要保持特定的显示格式，必须在写入后显式设置 number_format。
        
        常用日期格式:
            | 显示效果 | 格式代码 |
            |----------|----------|
            | 21/11/21 | dd/mm/yy |
            | 2021-11-21 | yyyy-mm-dd |
            | 11/21/21 | mm/dd/yy |
            | 21-Nov-2021 | dd-mmm-yyyy |
            | November 21, 2021 | mmmm dd, yyyy |
        
        常用时间格式:
            | 显示效果 | 格式代码 |
            |----------|----------|
            | 18:08 | hh:mm |
            | 18:08:00 | hh:mm:ss |
            | 6:08 PM | h:mm AM/PM |
        
        常用数字格式:
            | 显示效果 | 格式代码 |
            |----------|----------|
            | 1234.56 | 0.00 |
            | 1,234.56 | #,##0.00 |
            | 12.5% | 0.0% |
            | $1,234 | $#,##0 |
        
        特殊格式:
            | 用途 | 格式代码 |
            |------|----------|
            | 强制文本 | @ |
            | 保留前导零 | 00000 |
        
        Example:
            # 场景：原数据显示 21/11/21，写入后变成 2021-11-21
            # 解决：写入后设置 number_format 匹配原格式
            
            # 1. 写入日期数据
            sheet.range("A1:A10").value = date_list
            
            # 2. 设置显示格式
            sheet.range("A1:A10").format.number_format = "dd/mm/yy"
        """
        self._range._apply_style({'numfmt': value})

    @property
    def column_width(self) -> str:
        """获取/设置列宽（字符宽度单位，与 WPS/Excel 界面一致）。

        读取:
            返回 str，格式如 "A列 8.38字符, B列 12字符"
        设置:
            传入 int，如 format.column_width = 20

        Example:
            >>> sheet.range("A:C").format.column_width
            'A列 8.38字符, B列 12字符, C列 10字符'
            >>> sheet.range("A:A").format.column_width = 20
        """
        col_from = self._range._col_from + 1
        col_to = self._range._col_to + 1
        code = f'''
let sheet = Sheets.Item({json.dumps(self._range._sheet_name, ensure_ascii=False)});
let widths = [];
for (let c = {col_from}; c <= {col_to}; c++) {{
    widths.push(sheet.Columns(c).ColumnWidth);
}}
return JSON.stringify(widths);'''
        res = self._range._ctx.evaluate_script_v2(code)
        if not res.get('success', True):
            error_msg = res.get('error', '未知错误')
            print("获取列宽失败, error:", error_msg)
            return ""

        if "data" in res and "result" in res["data"]:
            widths = json.loads(res["data"]["result"])
            parts = [
                f"{_decimal_to_base26(c)}列 {w}字符"
                for c, w in enumerate(widths, start=col_from)
            ]
            return ", ".join(parts)
        print("获取列宽失败, res:", res)
        return ""

    @column_width.setter
    def column_width(self, width: int):
        """设置单元格区域列宽（单位：字符宽度，与 WPS/Excel 界面显示一致）。

        Example:
            >>> sheet.range("A:A").format.column_width = 20
        """
        self._range._ctx.flush()
        col_from = self._range._col_from + 1
        col_to = self._range._col_to + 1
        code = f'''
let sheet = Sheets.Item({json.dumps(self._range._sheet_name, ensure_ascii=False)});
for (let c = {col_from}; c <= {col_to}; c++) {{
    sheet.Columns(c).ColumnWidth = {width};
}}
return "ok";'''
        res = self._range._ctx.evaluate_script_v2(code)
        if not res.get('success', True):
            error_msg = res.get('error', '未知错误')
            print(f"设置列宽失败, error: {error_msg}")
            return


        col_from_letter = _decimal_to_base26(self._range._col_from + 1)
        col_to_letter = _decimal_to_base26(self._range._col_to + 1)
        if "data" in res and "result" in res.get("data", {}):
            print(f"设置列宽: {col_from_letter} 到 {col_to_letter} 列，宽度为 {width} 字符 成功")
        else:
            print(f"设置列宽失败, res: {res}")

    @property
    def row_height(self) -> str:
        """获取/设置行高（单位 pt，与 WPS/Excel 界面一致）。

        读取:
            返回 str，格式如 "第1行 15pt, 第2行 22.5pt"
        设置:
            传入 int（pt），如 format.row_height = 30

        Example:
            >>> sheet.range("1:3").format.row_height
            '第1行 15pt, 第2行 22.5pt, 第3行 15pt'
            >>> sheet.range("1:1").format.row_height = 30
        """
        row_from = self._range._row_from + 1
        row_to = self._range._row_to + 1
        code = f'''
let sheet = Sheets.Item({json.dumps(self._range._sheet_name, ensure_ascii=False)});
let parts = [];
for (let r = {row_from}; r <= {row_to}; r++) {{
    let h = sheet.Rows(r).RowHeight;
    parts.push("第" + r + "行 " + h + "pt");
}}
return parts.join(", ");'''
        res = self._range._ctx.evaluate_script_v2(code)
        if not res.get('success', True):
            error_msg = res.get('error', '未知错误')
            print("获取行高失败, error:", error_msg)
            return ""

        if "data" in res:
            if 'result' in res['data']:
                return res['data']['result']
        print("获取行高失败, res:", res)
        return ""

    @row_height.setter
    def row_height(self, height: int):
        """设置单元格区域行高（单位 pt，与 WPS/Excel 界面显示一致）。

        Example:
            >>> sheet.range("1:1").format.row_height = 30
        """
        self._range._ctx.flush()
        row_from = self._range._row_from + 1
        row_to = self._range._row_to + 1
        code = f'''
let sheet = Sheets.Item({json.dumps(self._range._sheet_name, ensure_ascii=False)});
for (let r = {row_from}; r <= {row_to}; r++) {{
    sheet.Rows(r).RowHeight = {height};
}}
return "ok";'''
        res = self._range._ctx.evaluate_script_v2(code)
        if not res.get('success', True):
            error_msg = res.get('error', '未知错误')
            print(f"设置行高失败, error: {error_msg}")


        if "data" in res and "result" in res.get("data", {}):
            print(f"设置行高: 第 {row_from} 到 {row_to} 行，高度为 {height} pt 成功")
        else:
            print(f"设置行高失败, res: {res}")
