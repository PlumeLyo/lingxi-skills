# 依赖说明（拼接执行时已在命名空间中）：
# - json, Literal, Any 等标准库来自 summary.py / _utils.py
# - _Context, _make_setattr_guard, ... 来自 _utils.py
# - Format 来自 formatting.py
# - ServerAPISheetDataSource, SummaryBuilder, format_range_address 来自 summary.py

# ============ Range ============

class Range:
    """单元格区域操作，用于读写数据和公式、设置字体/边框/填充等样式、合并单元格、添加条件格式。
    
    Note:
        通过 `sheet.range(addr)` 获取实例，addr 支持以下格式：
        - 单个单元格: "A1"
        - 区域: "A1:B10"
        - 整列: "A:A" 或 "A:C"
        - 整行: "1:1" 或 "1:10"

    Raises:
        Exception: 设置失败时抛出异常
    
    Example:
        # 获取区域并查看数据摘要
        rng = sheet.range("A1:D10")
        print(rng)  # 打印数据摘要
        
        # 读取数据
        data = rng.value  # 返回二维数组
        typed = rng.typed_value  # 返回二维数组：每格包含 value+type
        
        # 写入数据
        sheet.range("A1").value = "Hello"  # 单个值
        sheet.range("A1:B1").value = [["Name", "Age"]]  # 逐行写入
        sheet.range("C1:C2").value = [["Dept"], ["Tech"]]  # 逐列写入
        
        # 设置样式
        rng.format.font.bold = True
        rng.format.fill.color = '#4472C4'
        rng.format.h_align = 'center'
        
    """

    __setattr__ = _make_setattr_guard(
        frozenset(['_ctx', '_sheet_id', '_sheet_name', '_row_from', '_row_to',
                   '_col_from', '_col_to', '_format', '_values', 'value', 'formula']),
        ['_values', 'value', 'formula']
    )

    def __init__(self, ctx: _Context, sheet_id: int, sheet_name: str,
                 row_from: int, row_to: int, col_from: int, col_to: int):
        self._ctx = ctx
        self._sheet_id = sheet_id
        self._sheet_name = sheet_name
        self._row_from = row_from
        self._row_to = row_to
        self._col_from = col_from
        self._col_to = col_to
        self._format = Format(self)

    @property
    def address(self) -> str:
        """区域地址，如 'A1:B10'。可用于日志输出或传递给其他方法。"""
        return _format_address(self._row_from, self._row_to, self._col_from, self._col_to)

    @property
    def row_from(self) -> int:
        """起始行号（1-based），可用于构建公式引用。"""
        return self._row_from + 1

    @property
    def row_to(self) -> int:
        """结束行号（1-based），可用于构建公式引用。"""
        return self._row_to + 1

    @property
    def col_from(self) -> int:
        """起始列号（1-based，1=A, 2=B），可用于构建公式引用。"""
        return self._col_from + 1

    @property
    def col_to(self) -> int:
        """结束列号（1-based），可用于构建公式引用。"""
        return self._col_to + 1

    @property
    def col_from_letter(self) -> str:
        """起始列字母（如 'A'），可用于构建公式引用。"""
        return _decimal_to_base26(self._col_from + 1)

    @property
    def col_to_letter(self) -> str:
        """结束列字母（如 'C'），可用于构建公式引用。"""
        return _decimal_to_base26(self._col_to + 1)

    @property
    def rows_count(self) -> int:
        """区域包含的行数。"""
        return self._row_to - self._row_from + 1

    @property
    def columns_count(self) -> int:
        """区域包含的列数。"""
        return self._col_to - self._col_from + 1

    @property
    def format(self) -> Format:
        """样式属性，用于设置字体、填充、边框、对齐等。"""
        return self._format

    @property
    def value(self) -> list[list]:
        """读写数据，空单元格返回''，写入时外层=行内层=列。
        
        Returns:
            list[list]: 二维数组，每个子数组代表一行。
                - 文本 → str
                - 数字 → int 或 float
                - 日期 → datetime 对象
                - 空单元格 → ''（空字符串，不是 None）
                - 错误值 → str（如 '#N/A'）
        
        写入时支持以下格式:
            - 单个值: sheet.range("A1").value = "Hello" 或 sheet.range("A1").value = 123
            - 逐行写入: sheet.range("A1:C1").value = [["姓名", "年龄", "部门"]]
            - 逐列写入: sheet.range("A1:A3").value = [["姓名"], ["张三"], ["李四"]]
        
        Important:
            **禁止使用矩形区域一次性写入多行多列数据**，必须逐行或逐列写入。
            
            错误: sheet.range("A1:C3").value = [["a","b","c"], ["d","e","f"], ["g","h","i"]]
            正确: 分多次逐行写入
                sheet.range("A1:C1").value = [["a", "b", "c"]]
                sheet.range("A2:C2").value = [["d", "e", "f"]]
                sheet.range("A3:C3").value = [["g", "h", "i"]]
        
        Note:
            1. 不要写入 None，必须转换为 ""。否则会导致写入失败或显示异常。
            2. 从表格读取的文本原样使用，禁止 upper()/lower()/strip()。
            3. **写入区域有数据时会被终止写入，需删除已有数据再重新写入，注意非用户需求不得修改用户原始数据,删除前确保选择区域正确**
        """
        return self._values

    @property
    def _values(self) -> list[list]:
        """读取区域数据，返回二维数组。同 value 属性。
        
        Returns:
            list[list]: 二维数组，数据类型见 value 属性说明。
        """
        range_data = self._ctx.read_range(
            self._sheet_id,
            self._row_from, self._row_to,
            self._col_from, self._col_to
        )
        if not isinstance(range_data, list):
            print(f"区域: {self._sheet_name}!{self.address} 数据为空")
            return []

        rows_count = self.rows_count
        cols_count = self.columns_count
        result = [['' for _ in range(cols_count)] for _ in range(rows_count)]

        for cell in range_data:
            row_idx = cell['rowFrom'] - self._row_from
            col_idx = cell['colFrom'] - self._col_from
            if 0 <= row_idx < rows_count and 0 <= col_idx < cols_count:
                result[row_idx][col_idx] = cell.get('understandableType', {}).get('value', '')

        return result
    
    @property
    def typed_value(self) -> list[list[dict]]:
        """读取区域数据，返回二维数组，并保留每个单元格的 `type` 与 `value`。
        
        Returns:
            list[list[dict]]: 二维数组（外层=行，内层=列），每个元素形如：
                - {"type": <str>, "value": <Any>}
            
            type 可能的值：
                - "double": 数值（整数或浮点数）
                - "date": 日期时间
                - "string": 文本字符串
                - "": 空单元格
        
        Notes:
            - 与 `value` 不同：`value` 只返回值本身，不保留类型信息
            - 当需要根据单元格类型做不同处理时使用（如只对日期列做格式转换，跳过文本行）

        Example:
            >>> tv = sheet.range("B2:B10").typed_value
            >>> for row in tv:
            ...     cell = row[0]
            ...     if cell['type'] == 'date':
            ...         pass  # 处理日期单元格
            ...     elif cell['type'] == 'double':
            ...         pass  # 处理数值单元格
            ...     else:
            ...         pass  # 跳过文本/空值等
        """
        return self.typed_values

    @property
    def typed_values(self) -> list[list[dict]]:
        """读取区域属性，返回二维数组，并保留每个单元格的 `type` 与 `value`。同 typed_value 属性。

        Returns:
            list[list[dict]]: 二维数组，数据类型见 typed_value 属性说明。
        """
        range_data = self._ctx.read_range(
            self._sheet_id,
            self._row_from, self._row_to,
            self._col_from, self._col_to
        )
        if not isinstance(range_data, list):
            print(f"区域: {self._sheet_name}!{self.address} 数据为空")
            return []

        rows_count = self.rows_count
        cols_count = self.columns_count
        result: list[list[dict]] = [
            [{'type': '', 'value': ''} for _ in range(cols_count)]
            for _ in range(rows_count)
        ]

        for cell in range_data:
            row_idx = cell['rowFrom'] - self._row_from
            col_idx = cell['colFrom'] - self._col_from
            if 0 <= row_idx < rows_count and 0 <= col_idx < cols_count:
                ut = cell.get('understandableType', {}) or {}
                result[row_idx][col_idx] = {
                    'type': ut.get('type', '') or '',
                    'value': ut.get('value', '') if ut.get('value', None) is not None else ''
                }

        return result

    @property
    def formula(self) -> list[list]:
        """读写公式，写入须以'='开头。

        Returns:
            list[list]: 二维数组，每个元素是公式字符串或空字符串。

        写入时支持以下格式:
            - 公式必须以 '=' 开头，如 "=SUM(A1:A10)"
            - 支持单个公式或二维数组

        Important:
            禁止公式引用目标单元格自身！写入公式会立即覆盖原值：
            错误: sheet.range("A1").formula = "=MID(A1,1,3)"  # A1原值已被覆盖
            正确: 先用 value 读取原值，Python处理后写回

            一维列表默认按行写入：['=A1','=A2'] 写入一行两列。
            按列写入需用二维列表：[['=A1'],['=A2']]

        Note:
            公式中引用的单元格地址应与用户指令一致。
            如用户说"根据B列计算"，公式应引用B列。

        Example:
            >>> sheet.range("C1").formula = "=A1+B1"
        """
        range_data = self._ctx.read_range(
            self._sheet_id,
            self._row_from, self._row_to,
            self._col_from, self._col_to
        )
        if not isinstance(range_data, list):
            print(f"区域: {self._sheet_name}!{self.address} 数据为空")
            return []

        rows_count = self.rows_count
        cols_count = self.columns_count
        result = [['' for _ in range(cols_count)] for _ in range(rows_count)]

        for cell in range_data:
            row_idx = cell['rowFrom'] - self._row_from
            col_idx = cell['colFrom'] - self._col_from
            if 0 <= row_idx < rows_count and 0 <= col_idx < cols_count:
                result[row_idx][col_idx] = cell.get('fmlaText', '')

        return result

    @formula.setter
    def formula(self, data: str | list) -> None:
        """
        写入公式

        Note:
            - 使用list写入时，注意list维度必须匹配目标范围。
            - 写入公式时，公式必须以 '=' 开头；跨sheet引用时，格式为 '2025年6月'!D:D。
            - 写入一维列表 `['=A1+B1','=A2+B2']` 时，默认按**行**写入。如需按列写入，请使用二维列表 `[['=A1+B1'],['=A2+B2']]`。
            - 禁止公式引用目标单元格自身！写入公式会立即覆盖原值，导致：
                * `=MID(A1,...)` 写入 A1 → 原值丢失，公式引用的是新值（公式结果），不是原文本
                * 正确做法：先用 `range.value` 读取原值，Python 处理后写回；或用辅助列存放公式结果
            - 当表格有保护区域且权限为 visible 时，公式写入会自动降级为值写入（通过 value.setter)
            - **写入区域已有数据时会被终止写入，需删除已有数据再重新写入，注意非用户需求不得修改用户原始数据,删除前确保选择区域正确**
        """
        # 检查是否有公式写入权限，如果没有则降级为值写入
        if not self._ctx.can_write_formula:
            self.value = data
            return

        if isinstance(data, (str, float, int, bool, dict)):
            data = [[data]]

        code = f'''
let sheet = Sheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)});
sheet.Activate();
'''
        formula_operations = []
        for i, row in enumerate(data):
            if not isinstance(row, list):
                row = [row]
            for j, v in enumerate(row):

                tmpl = '''
let range{i}_{j} = sheet.Range({sheet_name_address});
range{i}_{j}.Formula2 = `{cell_value}`;
'''
                value = _to_cell_value(v)
                address = _format_address(self._row_from + i, self._row_from + i, self._col_from + j, self._col_from + j)
                code += tmpl.format(i=i, j=j, sheet_name_address=json.dumps(f"{address}", ensure_ascii=False), cell_value=value)

                # 记录公式位置信息（仅记录以 = 开头的公式）
                if str(value).strip().startswith('='):
                    formula_operations.append({
                        'rowFrom': self._row_from + i,
                        'rowTo': self._row_from + i,
                        'colFrom': self._col_from + j,
                        'colTo': self._col_from + j,
                        'formula': value,
                    })

        formula_info = None
        if formula_operations:
            formula_info = {
                'sheet_id': self._sheet_id,
                'operations': formula_operations,
            }
        self._ctx.queue_script(code.strip(), formula_info)

    @value.setter
    def value(self, data: str | list) -> None:
        """
        写入数据,插入图片需要通过insert_picture()方法

        Important:
            **禁止使用矩形区域一次性写入多行多列数据**，必须逐行或逐列写入:
            - 单个值: sheet.range("A1").value = "Hello"
            - 逐行写入: sheet.range("A1:C1").value = [["a", "b", "c"]]
            - 逐列写入: sheet.range("A1:A3").value = [["a"], ["b"], ["c"]]
        """
        self._values = data

    @_values.setter
    def _values(self, data: str | list) -> None:
        operations = []

        if isinstance(data, (str, float, int, bool, dict)):
            data = [[data]]
        if not isinstance(data, list):
            raise ValueError(f"不支持的数据类型: {type(data)}")

        # 检测是否是一维数组
        is_one_dimensional = False
        for row in data:
            if not isinstance(row, list):
                is_one_dimensional = True
                break
        if is_one_dimensional:
            # 如果 range 是单列（且不是单格），则按列写入（每个元素一行）
            # 否则按行写入（每个元素一列）
            is_single_column = self._col_from == self._col_to and self._row_to - self._row_from > 0
            if is_single_column:
                data = [[item] for item in data]
            else:
                data = [data]

        max_row = self._row_from
        max_col = self._col_from
        for i, row in enumerate(data):
            if not isinstance(row, list):
                row = [row]
            for j, v in enumerate(row):
                r = self._row_from + i
                c = self._col_from + j
                operations.append({
                    "opType": "formula",
                    "rowFrom": r, "rowTo": r,
                    "colFrom": c, "colTo": c,
                    "formula": _to_cell_value(v),
                })
                if r > max_row:
                    max_row = r
                if c > max_col:
                    max_col = c

        actual_addr = _format_address(self._row_from, max_row, self._col_from, max_col)
        range_addr = self.address
        if actual_addr != range_addr:
            exceeded = max_row > self._row_to or max_col > self._col_to
            hint = "数据超出了" if exceeded else "数据未填满"
            msg = (f"写入 {self._sheet_name}!{actual_addr} 数据成功"
                   f"（注意：{hint} range 指定范围 {range_addr}，实际写入范围为 {actual_addr}）")
        else:
            msg = f"写入 {self._sheet_name}!{actual_addr} 数据成功"
        self._ctx.buffer_write(self._sheet_id, operations, msg)

    def clear(self, contents: bool = True, formats: bool = True, comments: bool = True) -> str:
        """清空区域内容、格式和评论。
        
        ⚠️ 警告：这是破坏性操作，会永久删除数据，无法撤销！
        
        Args:
            contents: 是否清空内容（值、公式），默认 True
            formats: 是否清空格式（字体、颜色、边框等），默认 True
            comments: 是否清空批注/备注，默认 True
        
        使用前检查:
            1. 确认区域范围正确（打印 address 属性确认）
            2. 不要对 used_range 或整列/整行调用 clear()，除非确实需要
            3. 如果只需清空部分数据，指定精确的单元格范围
            4. 只清除用户明确要求的内容，未提及的参数应设为 False
        
        Example:
            >>> # 只清格式，保留内容和批注
            >>> sheet.range("A1").clear(contents=False, formats=True, comments=False)
            >>> 
            >>> # 只清内容，保留格式和批注
            >>> sheet.range("A1:C10").clear(contents=True, formats=False, comments=False)
            >>> 
            >>> # 清空单元格（内容+格式+批注）
            >>> sheet.range("A1:C10").clear()
        
        Returns:
            Any: 执行结果
        """
        code = f'''
let sheet = Sheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)});
sheet.Activate();
let range = sheet.Range({json.dumps(f"{self.address}", ensure_ascii=False)});
'''
        if contents:
            code += 'range.ClearContents();\n'
        if formats:
            code += 'range.ClearFormats();\n'
        if comments:
            code += 'range.ClearComments();\n'
        code = code.strip()
        res = self._ctx.evaluate_script_v2(code)
        if not res.get('success', True):
            error_msg = res.get('error', '未知错误')
            print(f"清空区域失败: {error_msg}")
            return res
        print(f"清空区域: {self._sheet_name}!{self.address} 成功")
        return res

    def _apply_style(self, style_dict: dict) -> None:
        """内部方法：应用样式字典到缓冲区。"""
        xf = _style_to_xf(style_dict)
        self._ctx.buffer_write(self._sheet_id, [{
            "opType": "format",
            "rowFrom": self._row_from,
            "rowTo": self._row_to,
            "colFrom": self._col_from,
            "colTo": self._col_to,
            "xf": xf,
        }], f"应用样式{json.dumps(style_dict, ensure_ascii=False)}到 {self._sheet_name}!{self.address} 成功")

    def _apply_border(self, border_props: dict) -> None:
        """内部方法：应用边框到缓冲区。"""
        style_map = {'none': 0, 'thin': 1, 'dashed': 4, 'dotted': 5, 'double': 6}
        
        # 获取边框类型，默认为 'all'
        border_type = border_props.get('type', 'all')
        
        xf = {}
        
        # 如果设置了样式，应用到相应的边框
        if 'style' in border_props:
            line_style = style_map.get(border_props['style'], 1)
            if border_type in ('all', 'outer'):
                xf.update({
                    'dgLeft': line_style, 'dgRight': line_style,
                    'dgTop': line_style, 'dgBottom': line_style,
                })
            if border_type in ('all', 'inner'):
                xf.update({
                    'dgInsideVert': line_style, 'dgInsideHorz': line_style,
                })
        
        # 如果设置了颜色，应用到相应的边框
        if 'color' in border_props:
            color_obj = {'tint': 0, 'type': 2, 'value': _color_to_argb(border_props['color'])}
            if border_type in ('all', 'outer'):
                xf.update({
                    'clrLeft': color_obj, 'clrRight': color_obj,
                    'clrTop': color_obj, 'clrBottom': color_obj,
                })
            if border_type in ('all', 'inner'):
                xf.update({
                    'clrInsideVert': color_obj, 'clrInsideHorz': color_obj,
                })

        self._ctx.buffer_write(self._sheet_id, [{
            "opType": "format",
            "rowFrom": self._row_from,
            "rowTo": self._row_to,
            "colFrom": self._col_from,
            "colTo": self._col_to,
            "xf": xf,
        }], f"应用边框属性 {list(border_props.keys())} 到 {self._sheet_name}!{self.address} 成功")

    def merge(self) -> None:
        """
        合并区域内单元格。
        """
        self._ctx.buffer_write(self._sheet_id, [{
            "opType": "merge",
            "rowFrom": self._row_from,
            "rowTo": self._row_to,
            "colFrom": self._col_from,
            "colTo": self._col_to,
            "type": "MergeCenter",
        }], f"合并单元格 {self._sheet_name}!{self.address} 成功")

    def insert_rows(self, count: int = 1) -> None:
        """在指定位置插入行，原有数据向下移动。
        
        Args:
            count: 插入行数
        """
        script = f'''
let sheet = Sheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)});
let range = sheet.Range({json.dumps(self.address, ensure_ascii=False)});
for (let i = 0; i < {count}; i++) {{
    range.EntireRow.Insert();
}}
'''
        res = self._ctx.evaluate_script_v2(script)
        if not res.get('success', True):
            error_msg = res.get('error', '未知错误')
            print(f"插入行失败: {error_msg}")
            return
        print(f"插入行: {self._sheet_name}!{self.address} 成功")

    def insert_columns(self, count: int = 1) -> None:
        """在指定位置插入列，原有数据向右移动。

        Args:
            count: 插入列数
        """
        script = f'''
let sheet = Sheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)});
let range = sheet.Range({json.dumps(self.address, ensure_ascii=False)});
for (let i = 0; i < {count}; i++) {{
    range.EntireColumn.Insert();
}}
'''
        res = self._ctx.evaluate_script_v2(script)
        if not res.get('success', True):
            error_msg = res.get('error', '未知错误')
            print(f"插入列失败: {error_msg}")
            return
        print(f"插入列: {self._sheet_name}!{self.address} 成功")

    def auto_fit(self, fit_type: Literal['columns', 'rows', 'auto'] = 'auto') -> None:
        """自适应列宽或行高，根据内容自动调整区域所在列的宽度或行的高度。

        Args:
            fit_type: 自适应类型
                - 'auto': 自动识别（默认）。整行区域（如 "1:10"）自动适应行高，
                  整列区域（如 "A:D"）或普通区域自动适应列宽
                - 'columns': 强制自适应列宽
                - 'rows': 强制自适应行高

        Note:
            此方法会对区域涉及的所有列或行执行自适应操作。

        Example:
            >>> # 整列区域，自动识别为列宽自适应
            >>> sheet.range("A:D").auto_fit()
            >>>
            >>> # 整行区域，自动识别为行高自适应
            >>> sheet.range("1:10").auto_fit()
            >>>
            >>> # 普通区域，默认自适应列宽
            >>> sheet.range("A1:H10").auto_fit()
            >>>
            >>> # 强制指定自适应行高
            >>> sheet.range("A1:H10").auto_fit('rows')
            >>>
            >>> # 强制指定自适应列宽
            >>> sheet.range("A1:H10").auto_fit('columns')
        """
        # 自动识别：整行区域（col_from == -1）自适应行高，否则自适应列宽
        if fit_type == 'auto':
            # 整行区域：如 "1:10"，col_from 和 col_to 都是 -1
            is_entire_row = self._col_from == -1
            fit_type = 'rows' if is_entire_row else 'columns'

        if fit_type == 'columns':
            script = f'''
let sheet = Sheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)});
sheet.Activate();
for (let col = {self._col_from + 1}; col <= {self._col_to + 1}; col++) {{
    sheet.Columns(col).AutoFit();
}}
'''
            self._ctx.queue_script(script.strip(), log_message=f"自适应列宽: {self._sheet_name}!{self.address} 成功")
        else:
            script = f'''
let sheet = Sheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)});
sheet.Activate();
for (let row = {self._row_from + 1}; row <= {self._row_to + 1}; row++) {{
    sheet.Rows(row).AutoFit();
}}
'''
            self._ctx.queue_script(script.strip(), log_message=f"自适应行高: {self._sheet_name}!{self.address} 成功")
        self._width_adjust(self._sheet_name, self._row_from, self._row_to, self._col_from, self._col_to)
        
    def delete(self, shift: Literal['up', 'left'] = 'up') -> None:
        """删除区域(shift='up'|'left')，删多行须从大行号往小行号倒序删除。
        
        Args:
            shift: 删除后单元格移动方向。
                - 'up': 下方单元格上移（默认，用于删除行）
                - 'left': 右侧单元格左移（用于删除列）
        
        Note:
            删除多行时必须从大行号往小行号倒序删除！
            否则删除第一行后，后续行号会偏移，导致删错行。
        
        Example:
            >>> # 删除单行
            >>> sheet.range("5:5").delete(shift='up')
            >>> 
            >>> # 删除多行（必须倒序！）
            >>> rows_to_delete = [3, 5, 7, 10]
            >>> for row in sorted(rows_to_delete, reverse=True):
            ...     sheet.range(f"{row}:{row}").delete(shift='up')
        """
        shift_val = 'etShiftUp' if shift == 'up' else 'etShiftToLeft'
        
        # 构建一个通用的日志
        log_msg = f"删除 {self._sheet_name} 表区域 {self.address} 成功"

        self._ctx.queue_delete(
            self._sheet_id,
            self._row_from, self._row_to,
            self._col_from, self._col_to,
            shift_val,
            log_msg
        )
        print(f"删除区域: {self._sheet_name}!{self.address} 成功")

    def auto_fill(self, target: Union[str, 'Range']) -> Any:
        """
        用源区域的内容自动填充目标区域（常用于公式填充）,目标区域必须包含源区域。
        
        Args:
            target: 目标区域，支持字符串地址（如 "A1:A10"）或 Range 对象
        """
        # 处理 target 参数
        if isinstance(target, Range):
            target_addr = target.address
            target_range = target
        else:
            target_addr = target
            row_from, row_to, col_from, col_to = _parse_range(target_addr)
            target_range = Range(self._ctx, self._sheet_id, self._sheet_name, row_from, row_to, col_from, col_to)

        script = f'''
let sheet = Sheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)});
sheet.Activate();
let source_range = sheet.Range({json.dumps(self.address, ensure_ascii=False)});
let target_range = sheet.Range({json.dumps(target_addr, ensure_ascii=False)});
source_range.AutoFill(target_range);
'''
        res = self._ctx.evaluate_script_v2(script)
        if not res.get('success', True):
            error_msg = res.get('error', '未知错误')
            print(f"自动填充失败: {error_msg}")
            return res
        # 轮询检查填充结果，最大重试5次
        max_retries = 5
        retry_count = 0
        poll_interval = 1  # 1秒间隔
        
        target_data = None
        while retry_count < max_retries:
            try:
                time.sleep(poll_interval)
                # 获取目标区域的数据
                target_data = target_range.value
                
                # 获取源区域的数据
                source_data = self.value
                
                # 检查目标区域中除去源区域后是否有新数据
                if target_data and source_data:
                    # 计算目标区域和源区域的有效数据单元格数
                    target_filled = sum(1 for row in target_data for cell in row if str(cell).strip())
                    source_filled = sum(1 for row in source_data for cell in row if str(cell).strip())
                    
                    # 如果目标区域的数据量大于源区域，说明填充成功
                    if target_filled > source_filled:
                        print(f"自动填充: {self.address} 到 {target_addr} 成功")
                        break
            except Exception as e:
                print(f"数据检测异常")
            
            retry_count += 1
        
        if retry_count >= max_retries:
            print(f"填充区域{self.address}数据为空，请检查是否符合预期")
            return res
        
        # 生成填充结果摘要
        if target_data:
            summary = self._generate_autofill_summary(target_range, target_data)
            print(f"自动填充结果摘要: {summary}")

        print(f"自动填充: {self.address} 到 {target_addr} 成功")
        return res

    def _generate_autofill_summary(self, target_range: 'Range', data: list[list]) -> str:
        """
        生成自动填充结果的摘要。
        
        包含：
        1. 填充成功提示
        2. 头尾值（防止数值错误）
        3. 公式报错信息（如果有）
        
        Args:
            target_range: 填充的目标区域
            
        Returns:
            结果摘要字符串
        """
        try:
            rows_count = len(data)
            cols_count = len(data[0]) if data else 0
            total_cells = rows_count * cols_count
            
            # 错误值列表
            error_values = ['#N/A', '#VALUE!', '#DIV/0!', '#REF!', '#NAME?', '#NUM!', '#NULL!', '#SPILL!']
            
            # 将二维数组展平为一维列表（按行优先）
            flat_data = []
            cell_addresses = []
            error_cells = []
            
            for i in range(rows_count):
                for j in range(cols_count):
                    value = data[i][j]
                    row_num = target_range.row_from + i
                    col_num = target_range.col_from + j
                    col_letter = _decimal_to_base26(col_num)
                    addr = f"{col_letter}{row_num}"
                    
                    flat_data.append(value)
                    cell_addresses.append(addr)
                    
                    # 检查是否是错误值
                    if value in error_values:
                        error_cells.append((addr, value))
            
            # 构建摘要
            summary_parts = []
            
            # 1. 基本信息
            summary_parts.append(f"填充结果 (共{total_cells}个单元格):")
            
            # 2. 头尾值（防止数值错误）
            if total_cells <= 5:
                # 少于等于5个单元格，显示全部
                value_items = [f"{addr}={val}" for addr, val in zip(cell_addresses, flat_data)]
                summary_parts.append("  值: " + ", ".join(value_items))
            else:
                # 多于5个单元格，显示前2个和后2个
                head_items = [f"{cell_addresses[i]}={flat_data[i]}" for i in range(2)]
                tail_items = [f"{cell_addresses[i]}={flat_data[i]}" for i in range(-2, 0)]
                summary_parts.append("  值: " + ", ".join(head_items) + " ... " + ", ".join(tail_items))
            
            # 3. 错误信息（如果有）
            if error_cells:
                error_count = len(error_cells)
                summary_parts.append(f"  ⚠️ 发现 {error_count} 个公式错误:")
                
                # 按错误类型分组统计
                error_types = {}
                for addr, err_val in error_cells:
                    error_types[err_val] = error_types.get(err_val, 0) + 1
                
                # 显示错误类型统计
                error_type_strs = [f"{err_type}({count}个)" for err_type, count in error_types.items()]
                summary_parts.append(f"    错误类型: {', '.join(error_type_strs)}")
                
                # 显示前3个错误位置
                error_examples = [f"{addr}={val}" for addr, val in error_cells[:3]]
                if len(error_cells) > 3:
                    error_examples.append(f"... 还有{len(error_cells)-3}个错误")
                summary_parts.append(f"    错误位置: {', '.join(error_examples)}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            return f"填充结果摘要生成失败: {str(e)}"

    def add_format_condition(self,
                            condition_type: Literal['cell_value', 'expression', 'top10',
                                                   'unique', 'duplicate', 'text', 'blanks', 'time_period',
                                                   'above_average', 'no_blanks', 'errors', 'no_errors'],
                            operator: Literal['between', 'not_between', 'equal', 'not_equal',
                                            'greater', 'less', 'greater_equal', 'less_equal',
                                            'string_conclude', 'string_exclude', 'string_begins_with',
                                            'string_ends_with', 'today', 'yesterday', 'last_7_days',
                                            'this_week', 'last_week', 'last_month', 'tomorrow',
                                            'next_week', 'next_month', 'this_month',
                                            'top10', 'top10_percent', 'last10', 'last10_percent',
                                            'above_average', 'below_average'] | None = None,
                            formula1: str | None = None,
                            formula2: str | None = None,
                            format_style: dict | None = None,
                            rank: str | None = None,
                            lastone: bool = False) -> bool:
        """添加条件格式，参数的必填与依赖关系说明如下——请严格按要求传参，否则会抛出 ValueError。

        Note:
            **参数逻辑依赖关系说明（必填参数/可选参数/忽略参数规则）**:
            **1. 数值与逻辑判断 (需 `operator` + `formula1`)**

            * **`condition_type="cell_value"`**
                * **必填**: `operator`, `formula1`
                * **可选**: `formula2` (仅当 `operator` 为 `"between"` 或 `"not_between"` 时必填)
                * **允许的 Operator**:
                    * `equal`, `not_equal` (等于/不等于)
                    * `greater`, `less`, `greater_equal`, `less_equal` (大于/小于等)
                    * `between`, `not_between` (介于/不介于)

            **2. 文本内容判断 (需 `operator` + `formula1`)**

            * **`condition_type="text"`**
                * **必填**: `operator`, `formula1` (即文本内容)
                * **允许的 Operator**:
                    * `string_conclude` (包含)
                    * `string_exclude` (不包含)
                    * `string_begins_with` (开头是)
                    * `string_ends_with` (结尾是)

            **3. 时间/日期判断 (需 `operator`)**

            * **`condition_type="time_period"`**
                * **必填**: `operator`
                * **忽略**: `formula1`, `formula2`
                * **允许的 Operator**:
                    * `today`, `yesterday`, `tomorrow`
                    * `this_week`, `last_week`, `next_week`
                    * `this_month`, `last_month`, `next_month`
                    * `last_7_days`

            **4. 排名与统计 (需 `operator` + `rank` 或仅 `operator`)**

            * **`condition_type="top10"`**
                * **必填**: `operator`, `rank` (例如 "10" 或 "5")
                * **允许的 Operator**:
                    * `top10` (前 N 个), `top10_percent` (前 N%)
                    * `last10` (后 N 个), `last10_percent` (后 N%)
            * **`condition_type="above_average"`**
                * **必填**: `operator`
                * **允许的 Operator**: `above_average` (高于平均), `below_average` (低于平均)

            **5. 状态与公式 (无需 Operator)**

            * **`condition_type="expression"`**: 自定义公式。必填 `formula1` (例如 `"=A1>5"`)。
            * **状态标记**: 以下类型**不需要** `operator`、`formula` 或 `rank`，仅需指定类型：
                * `"unique"` (唯一值), `"duplicate"` (重复值)
                * `"blanks"` (空值), `"no_blanks"` (非空值)
                * `"errors"` (错误值), `"no_errors"` (无错误值)

            #### 样式参数 (`format_style`)

            * 如果为 `None`，使用默认样式（浅红背景+深红文字）。
            * 自定义字典结构：
                ```python
                {
                    "interior": {"color": "#HEXCODE"}, # 背景色
                    "font": {
                    "color": "#HEXCODE"             # 字体色
                    "bls": True/False,             # 加粗
                    "italic": True/False,           # 斜体
                    "strikeout": True/False,        # 删除线
                    "uls": 0,                      # 下划线类型
                    "sss": 0,                      # 上下标类型
                    "themeFont": 2,                 # 字体类型
                    }    
                    
                }
                ```

            #### 优先级 (`lastone`)

            * 当工作表中存在多个条件格式规则时，优先级确定求值的顺序。
            * 默认新添加的条件格式优先级为最高，设置 `lastone` 为 `True` 则新添加的条件格式优先级为最低
        """
        type_map = {
            'cell_value': 'valueRange',
            'expression': 'expression',
            'text': 'containsValue',
            'unique': 'containsValue',
            'duplicate': 'containsValue',
            'blanks': 'containsValue',
            'no_blanks': 'containsValue',
            'errors': 'containsValue',
            'no_errors': 'containsValue',
            'time_period': 'timePeriod',
            'top10': 'rankAverage',
            'above_average': 'rankAverage',
        }

        # 运算符映射（下划线转驼峰）
        operator_map = {
            # cell_value 运算符
            'between': 'between',
            'not_between': 'notBetween',
            'equal': 'equal',
            'not_equal': 'notEqual',
            'greater': 'greater',
            'less': 'less',
            'greater_equal': 'greaterEqual',
            'less_equal': 'lessEqual',
            # text 运算符
            'string_conclude': 'stringConclude',
            'string_exclude': 'stringExclude',
            'string_begins_with': 'stringBeginsWith',
            'string_ends_with': 'stringEndsWith',
            # time_period 运算符
            'today': 'today',
            'yesterday': 'yesterday',
            'last_7_days': 'last7Days',
            'this_week': 'thisWeek',
            'last_week': 'lastWeek',
            'last_month': 'lastMonth',
            'tomorrow': 'tomorrow',
            'next_week': 'nextWeek',
            'next_month': 'nextMonth',
            'this_month': 'thisMonth',
            # rankAverage 运算符
            'top10': 'top10',
            'top10_percent': 'top10%',
            'last10': 'last10',
            'last10_percent': 'last10%',
            'above_average': 'aboveAverage',
            'below_average': 'belowAverage',
        }

        # 自动 operator 映射（对于某些 condition_type，operator 是固定的）
        auto_operator_map = {
            'unique': 'uniqueValues',
            'duplicate': 'duplicateValues',
            'blanks': 'blanksCondition',
            'no_blanks': 'noBlanksCondition',
            'errors': 'errors',
            'no_errors': 'noErrors',
        }

        # 获取 API 的 type 值
        api_type = type_map.get(condition_type)
        if not api_type:
            raise ValueError(f"不支持的条件类型: {condition_type}")

        # 构建 rule 字典
        rule = {
            "type": api_type,
            "ranges": [{
                "rowFrom": self._row_from,
                "rowTo": self._row_to,
                "colFrom": self._col_from,
                "colTo": self._col_to,
            }],
            "lastone": lastone,
        }

        # 处理 operator
        if condition_type in auto_operator_map:
            # 自动设置固定的 operator
            rule["operator"] = auto_operator_map[condition_type]
        elif condition_type == 'expression':
            # expression 类型不需要 operator 字段
            pass
        elif operator:
            # 使用用户提供的 operator
            api_operator = operator_map.get(operator)
            if not api_operator:
                raise ValueError(f"不支持的运算符: {operator}")
            rule["operator"] = api_operator
        else:
            raise ValueError(f"条件类型 '{condition_type}' 需要提供 operator 参数")

        # 处理 formula1
        if condition_type == 'top10':
            # rankAverage 类型不使用 formula1
            pass
        elif formula1 is not None:
            rule["formula1"] = formula1

        # 处理 formula2（仅 between/notBetween 需要）
        if operator in ('between', 'not_between') and formula2 is not None:
            rule["formula2"] = formula2

        # 处理 rank（仅 rankAverage 类型需要）
        if api_type == 'rankAverage':
            if rank is not None:
                rule["rank"] = rank
            elif formula1 is not None:
                # 兼容旧用法：如果用户传了 formula1，自动转为 rank
                rule["rank"] = formula1

        # 处理样式
        if format_style is None:
            # 使用默认样式：GitHub diff 风格
            format_style = {
                'interior': {'color': '#ffeef0'},  # 浅粉红背景
                'font': {'color': '#d1242f'}       # 深红字体
            }

        # 转换样式为 API 格式
        xf = {}

        if 'font' in format_style:
            font = format_style['font']
            font_xf = {}
            if 'color' in font:
                font_xf['color'] = {
                    'tint': 0,
                    'type': 2,
                    'value': _color_to_argb(font['color'])
                }
            # 新 API 已支持字体样式字段：bold/italic/strikeout/uls/sss/themeFont
            if 'bls' in font:
                font_xf['bls'] = bool(font['bls'])
            if 'italic' in font:
                font_xf['italic'] = bool(font['italic'])
            if 'strikeout' in font:
                font_xf['strikeout'] = bool(font['strikeout'])
            if 'uls' in font:
                font_xf['uls'] = int(font['uls'])
            if 'sss' in font:
                font_xf['sss'] = int(font['sss'])
            if 'themeFont' in font:
                font_xf['themeFont'] = int(font['themeFont'])
            if font_xf:
                xf['font'] = font_xf

        if 'interior' in format_style:
            interior = format_style['interior']
            xf['fill'] = {
                'type': 1,
                'back': {
                    'type': 2,
                    'value': _color_to_argb(interior['color'])
                },
                'fore': {
                    'type': 255
                }
            }

        rule["xf"] = xf

        # 执行 API 调用
        self._ctx._wait_for_rate_limit('createCFRule')
        res = self._ctx.execute({
            "command": "http.et.createCFRule",
            "param": {
                "sheetId": self._sheet_id,
                "rule": rule
            }
        })

        try:
            result = res.get('result', None)
            if result == 'ok':
                print(f"添加条件格式成功: {res}")
                return True
            else:
                error = res.get('error', '未知错误')
                print(f"添加条件格式失败: {error}")
                return False
        except Exception as e:
            print(f"添加条件格式异常: {str(e)}")
            return False

    def get_format_conditions(self) -> list[dict]:
        """获取条件格式，返回条件格式列表。如无条件格式，返回空列表。
        
        Returns:
            list[dict]: 条件格式列表
            Each dictionary contains:
                - `type`: 条件类型
                - `operator`: 运算符
                - `formula1`: 第一个公式或值
                - `formula2`: 第二个公式或值
                - `priority`: 优先级，值越小，优先级越高
                - `applies_to`: 应用范围
                - `number_format`: 数字格式
                - `rank`: 排名值
                - `percent`: 是否使用百分比
                - `top_bottom`: 前/后
                - `dupe_unique`: 唯一/重复
                - `above_below`: 高于/低于
                - `font`: 字体样式字典
                - `interior`: 填充样式字典
        """
        # Type 映射（API 格式 -> 用户友好格式）
        type_map = {
            'valueRange': 'cell_value',
            'expression': 'expression',
            'colorScale': 'color_scale',
            'dataBar': 'databar',
            'rankAverage': 'top10',
            'iconSet': 'icon_set',
            'containsValue': 'text',  # 也用于 unique, blanks, errors 等
            'timePeriod': 'time_period',
        }
        
        # Operator 映射（某些特殊 operator 需要映射为 type）
        operator_to_type_map = {
            'uniqueValues': 'unique',
            'duplicateValues': 'duplicate',
            'blanksCondition': 'blanks',
            'noBlanksCondition': 'no_blanks',
            'errors': 'errors',
            'noErrors': 'no_errors',
        }
        
        # Operator 映射
        operator_map = {
            # cell_value 运算符
            'between': 'between',
            'notBetween': 'not_between',
            'equal': 'equal',
            'notEqual': 'not_equal',
            'greater': 'greater',
            'less': 'less',
            'greaterEqual': 'greater_equal',
            'lessEqual': 'less_equal',
            # text 运算符
            'stringConclude': 'string_conclude',
            'stringExclude': 'string_exclude',
            'stringBeginsWith': 'string_begins_with',
            'stringEndsWith': 'string_ends_with',
            # time_period 运算符
            'today': 'today',
            'yesterday': 'yesterday',
            'last7Days': 'last_7_days',
            'thisWeek': 'this_week',
            'lastWeek': 'last_week',
            'lastMonth': 'last_month',
            'tomorrow': 'tomorrow',
            'nextWeek': 'next_week',
            'nextMonth': 'next_month',
            'thisMonth': 'this_month',
            # rankAverage 运算符
            'top10': 'top10',
            'top10%': 'top10_percent',
            'last10': 'last10',
            'last10%': 'last10_percent',
            'aboveAverage': 'above_average',
            'belowAverage': 'below_average',
        }
        
        self._ctx._wait_for_rate_limit('getCFRule')
        result = self._ctx.execute({
            "command": "http.et.getCFRule",
            "param": {
                "sheetId": self._sheet_id,
            }
        })
        if result['result'] != 'ok':
            return []
        
        rules = result['detail']['rules']
        if not rules:
            return []

        formatted_rules = []
        for rule in rules:
            formatted = {}
            
            # 转换 type
            raw_type = rule.get('type', '')
            raw_operator = rule.get('operator', '')
            
            # 某些 operator 实际上是 type
            if raw_operator in operator_to_type_map:
                formatted['type'] = operator_to_type_map[raw_operator]
            else:
                formatted['type'] = type_map.get(raw_type, raw_type)
            
            # operator（排除那些实际是 type 的 operator）
            if raw_operator and raw_operator not in operator_to_type_map:
                formatted['operator'] = operator_map.get(raw_operator, raw_operator)
            
            # formula1, formula2
            if rule.get('formula1'):
                formatted['formula1'] = rule['formula1']
            if rule.get('formula2'):
                formatted['formula2'] = rule['formula2']
            
            # priority
            if 'priority' in rule:
                formatted['priority'] = rule['priority']
            
            # applies_to
            if rule.get('ranges'):
                rng = rule['ranges'][0]
                formatted['applies_to'] = _format_address(
                    rng['rowFrom'], rng['rowTo'],
                    rng['colFrom'], rng['colTo']
                )
            
            # font 样式
            xf = rule.get('xf', {})
            if xf.get('font'):
                font_xf = xf['font']
                font = {}
                if font_xf.get('color') and font_xf['color'].get('rgbValue'):
                    font['color'] = font_xf['color']['rgbValue']
                if font_xf.get('bls'):
                    font['bold'] = font_xf['bls']
                if font_xf.get('italic'):
                    font['italic'] = font_xf['italic']
                if font_xf.get('strikeout'):
                    font['strikeout'] = font_xf['strikeout']
                if font_xf.get('uls'):
                    font['uls'] = font_xf['uls']
                if font_xf.get('sss'):
                    font['sss'] = font_xf['sss']
                if font_xf.get('themeFont'):
                    font['themeFont'] = font_xf['themeFont']
                if font:
                    formatted['font'] = font
            
            # interior 样式（fill）
            if xf.get('fill') and xf['fill'].get('back') and xf['fill']['back'].get('rgbValue'):
                formatted['interior'] = {'color': xf['fill']['back']['rgbValue']}
            
            # rank（用于 top10 类型）
            if rule.get('rank'):
                formatted['rank'] = rule['rank']
            
            formatted_rules.append(formatted)
        
        return formatted_rules

    def delete_format_condition(self, priority: int) -> bool:
        """根据优先级删除条件格式。

        Args:
            priority: 条件格式优先级（可通过 get_format_conditions 获取）

        Returns:
            bool: 是否删除成功
        """
        res = self._ctx.execute({
            "command": "http.et.clearCFRule",
            "param": {
                "sheetId": self._sheet_id,
                "rule": {"priority": priority}
            }
        })
        try:
            print(f"删除条件格式成功")
            return res.get('result') == 'ok'
        except Exception as e:
            print(f"删除条件格式异常: {str(e)}")
            return False

    def clear_format_conditions(self) -> bool:
        """清除所有条件格式。

        Returns:
            bool: 是否清除成功
        """
        res = self._ctx.execute({
            "command": "http.et.batchClearCFRule",
            "param": {
                "sheetId": self._sheet_id,
                "ranges": [{
                    "rowFrom": self._row_from,
                    "rowTo": self._row_to,
                    "colFrom": self._col_from,
                    "colTo": self._col_to,
                }]
            }
        })
        try:
            print(f"清除条件格式成功: {res}")
            return res.get('result') == 'ok'
        except Exception as e:
            print(f"清除条件格式异常: {str(e)}")
            return False

    def __repr__(self) -> str:
        """查看区域数据摘要 (推荐) -- `print(range_object)`
        Note:
            - **功能**: 打印区域的详细摘要，包括维度、行列数、以及带有样式/格式标记的文本预览。
            - **核心优势**: 相比 `range.value` 仅返回纯数据，`print(range)` 会返回包含**合并单元格状态**、**单元格样式标记**（如 `<STY>`）及**数字格式标记**（如 `<NUMFMT>`）的富文本摘要。
            - **使用场景**: 在“理解文档”阶段，**必须**优先使用此方式来同时检查数据内容和格式规则，避免因忽视格式（如日期显示格式、货币单位）而导致解析错误。
        """
        # 与 range.value 对齐：预览前先提交缓冲写入，避免看到旧快照。
        self._ctx.flush()
        used_range_str = format_range_address(
            self._row_from, self._col_from,
            self._row_to, self._col_to
        )
        range_data = ServerAPISheetDataSource(
            sheet_id=self._sheet_id,
            sheet_name=self._sheet_name,
            used_range_str=used_range_str,
        )
        builder = SummaryBuilder(token_budget=4096, max_rows=50)
        return builder.build_range_summary(range_data)

    def sort(
        self,
        key: str | int = 1,
        order: Literal['asc', 'desc'] = 'asc',
        key2: str | int | None = None,
        order2: Literal['asc', 'desc'] = 'asc',
        key3: str | int | None = None,
        order3: Literal['asc', 'desc'] = 'asc',
        header: bool = True,
        match_case: bool = False,
    ) -> None:
        """对区域进行原地排序，保留格式和公式。
        
        Args:
            key: 第一排序字段。可以是列号（1-based）或列字母（如 "A"）
            order: 第一字段排序方向，'asc' 升序，'desc' 降序
            key2: 第二排序字段（可选）
            order2: 第二字段排序方向
            key3: 第三排序字段（可选）
            order3: 第三字段排序方向
            header: 第一行是否为表头，默认 True
            match_case: 是否区分大小写，默认 False
        
        Note:
            - 原地排序会保留单元格格式（百分比、日期等）和公式
            - 比 DataFrame 排序更安全，不会丢失格式

        Example:
            >>> # 按 B 列降序排序（第一行是标题）
            >>> sheet.range("A1:D10").sort(key="B", order="desc", header=True)
            >>>
            >>> # 多字段排序：先按 A 列升序，再按 B 列降序
            >>> sheet.range("A1:D10").sort(key="A", order="asc", key2="B", order2="desc")
        """
        # 转换 order 参数
        order_map = {'asc': 'xlAscending', 'desc': 'xlDescending'}
        order1_val = order_map.get(order, 'xlAscending')
        order2_val = order_map.get(order2, 'xlAscending')
        order3_val = order_map.get(order3, 'xlAscending')
        
        # 转换 header 参数
        header_val = 'xlYes' if header else 'xlNo'
        
        # 转换 key 为 Range 引用（如果是数字，转为对应列的第一个单元格）
        def key_to_range(k):
            if k is None:
                return 'null'
            if isinstance(k, int):
                col_letter = _decimal_to_base26(k)
                return f'sheet.Range("{col_letter}{self._row_from + 1}")'
            else:
                # 假设是列字母
                return f'sheet.Range("{k}{self._row_from + 1}")'
        
        key1_ref = key_to_range(key)
        key2_ref = key_to_range(key2)
        key3_ref = key_to_range(key3)
        
        script = f'''
            let sheet = Sheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)});
            sheet.Activate();
            let range = sheet.Range({json.dumps(self.address, ensure_ascii=False)});
            range.Sort({key1_ref}, {order1_val}, {key2_ref}, null, {order2_val}, {key3_ref}, null, {header_val}, null, {str(match_case).lower()});
        '''
        self._ctx.queue_script(script.strip(), log_message=f"排序区域: {self._sheet_name}!{self.address} 成功")

    def insert_picture(self,
                       tag:Literal['local','attachment','url'],
                       path:str,
                       target_row_from: int,
                       target_row_to: int,
                       target_col_from: int,
                       target_col_to: int):
        """插入图片到指定单元格

        Args:
            tag: 图片来源类型，可选值为 'local'（本地文件）、'attachment'（文档附件）、'url'（网络 URL）
            path: 图片路径或 URL，根据 tag 类型不同而不同
            ("uploadId": "xxxxxxx",     // 本地文件专用
            "attachmentId": "xxxxxxxxx",    // 附件专用
            "url": "https://xxx.xxx.xxx/xxx.png"  // url专用)
            target_row_from: 目标插入起始行索引（从 0 开始）
            target_row_to: 目标插入结束行索引（从 0 开始）
            target_col_from: 目标插入起始列索引（从 0 开始）
            target_col_to: 目标插入结束列索引（从 0 开始）
        """
        cell_pic_info = {
            "width": -1,  # -1 表示自动适应
            "height": -1,  # -1 表示自动适应
            "tag": tag
        }
        
        if tag == "local":
            cell_pic_info["uploadId"] = path
        elif tag == "attachment":
            cell_pic_info["attachmentId"] = path
        elif tag == "url":
            cell_pic_info["url"] = path
        else:
            raise ValueError(f"不支持的图片来源类型: {tag}")
        
        operations = [{
            "opType": "picture",
            "rowFrom": target_row_from,
            "rowTo": target_row_to,
            "colFrom": target_col_from,
            "colTo": target_col_to,
            "cellPicInfo": cell_pic_info
        }]
        #attachmentid，这个附件是什么？能插入表格？
        # 没有单独的插入单元格图片的接口?我在updateRangedata找到相关的.然后通过.value设置我觉得逻辑上会造成混淆，我就没加.value设置图片的功能，添加图片只能走这个函数
        
        self._ctx.buffer_write(
            self._sheet_id, 
            operations, 
            f"在 {self._sheet_name}!{_format_address(target_row_from, target_row_to, target_col_from, target_col_to)} 插入图片成功"
        )

    def _width_adjust(self, sheet_name, row_from, row_to, col_from, col_to):
        """内部接口: 解决 AutoFit 调用后列宽、行高过大问题。"""
        self._ctx.flush()
        script = f'''
let sheet = Sheets.Item({json.dumps(sheet_name, ensure_ascii=False)});
sheet.Activate();
for (let c = {col_from + 1}; c <= {col_to + 1}; c++) {{
    let w = sheet.Columns(c).ColumnWidth;
    if (w > 60) sheet.Columns(c).ColumnWidth = 60;
}}
for (let r = {row_from + 1}; r <= {row_to + 1}; r++) {{
    let fontSize = sheet.Cells(r, {col_from + 1}).Font.Size;
    if (fontSize<5) fontSize = 11;
    sheet.Rows(r).RowHeight = fontSize * 2;
}}
return "ok";
'''
        #这里只取区域最左列的字号，理论上应该遍历该行取最大字号，结合性能，综合考虑只需要取区域内该行第一个单元格的字号
        res = self._ctx.evaluate_script_v2(script)
        if "data" not in res or "result" not in res.get("data", {}):
            print("列宽/行高调整失败, 脚本输出信息:", res)
