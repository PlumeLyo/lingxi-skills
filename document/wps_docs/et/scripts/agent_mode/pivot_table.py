# 依赖说明（拼接执行时已在命名空间中）：
# - json, Literal, Any, Optional 等标准库来自 summary.py / _utils.py
# - _Context, _SheetMeta, _make_setattr_guard 来自 _utils.py
# - Sheet 来自 sheet.py

# ============ 枚举常量 ============

# XlPivotFieldOrientation
_ORIENTATION_MAP = {
    'hidden': 0,      # 隐藏
    'row': 1,         # 行字段
    'column': 2,      # 列字段
    'page': 3,        # 筛选字段
    'data': 4,        # 数据字段
}
_ORIENTATION_REVERSE = {v: k for k, v in _ORIENTATION_MAP.items()}

# 汇总函数
_FUNCTION_MAP = {
    'sum': -4157,       # 求和
    'count': -4112,     # 计数
    'average': -4106,   # 平均值
    'max': -4136,       # 最大值
    'min': -4139,       # 最小值
    'product': -4149,   # 乘积
    'count_nums': -4113,  # 数值计数
    'stdev': -4154,     # 标准差
    'var': -4164,       # 方差
}
_FUNCTION_REVERSE = {v: k for k, v in _FUNCTION_MAP.items()}

# 排序方向
_SORT_ORDER_MAP = {
    'ascending': 1,   # 升序
    'descending': 2,  # 降序
}

# 版式类型 (XlLayoutRowType)
_LAYOUT_MAP = {
    'compact': 0,   # 压缩形式
    'tabular': 1,   # 表格形式
    'outline': 2,   # 大纲形式
}

# 分类汇总位置
_SUBTOTAL_LOCATION_MAP = {
    'top': 1,      # 顶部
    'bottom': 2,   # 底部
}


# ============ PivotItem ============

class PivotItem:
    """数据透视表数据项，用于控制字段中单个数据项的可见性。

    Note:
        通过 `pivot_field.pivot_items()` 获取实例列表。

    Example:
        field = pivot_table.pivot_field("地区")
        for item in field.pivot_items():
            print(item.name, item.visible)
        # 只显示 "华北" 和 "华南"
        for item in field.pivot_items():
            item.visible = item.name in ["华北", "华南"]
    """

    __setattr__ = _make_setattr_guard(
        frozenset(['_ctx', '_sheet_name', '_table_name', '_field_name',
                   '_name', '_position', '_visible', 'visible']),
        ['visible']
    )

    def __init__(self, ctx: _Context, sheet_name: str, table_name: str,
                 field_name: str, name: str, position: int, visible: bool):
        self._ctx = ctx
        self._sheet_name = sheet_name
        self._table_name = table_name
        self._field_name = field_name
        self._name = name
        self._position = position
        self._visible = visible

    @property
    def name(self) -> str:
        """数据项名称"""
        return self._name

    @property
    def position(self) -> int:
        """数据项位置"""
        return self._position

    @property
    def visible(self) -> bool:
        """数据项是否可见"""
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        code = (
            f'let sheet = Application.Worksheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)});\n'
            f'let pvt = sheet.PivotTables({json.dumps(self._table_name, ensure_ascii=False)});\n'
            f'pvt.PivotFields({json.dumps(self._field_name, ensure_ascii=False)})'
            f'.PivotItems({json.dumps(self._name, ensure_ascii=False)})'
            f'.Visible = {str(value).lower()};\n'
            f'return "ok";'
        )
        res = self._ctx.evaluate_script_v2(code)
        if res is not None and not res.get('success', True):
            print(f"设置可见性失败: {res.get('error', '未知错误')}")
            return
        self._visible = value
        print(f"设置数据项 {self._field_name}.{self._name} 可见性: {value}")

    def __repr__(self) -> str:
        return f"PivotItem(name={self._name!r}, visible={self._visible})"


# ============ PivotField ============

class PivotField:
    """数据透视表字段，用于控制字段的方向、汇总函数、排序和筛选。

    Note:
        通过 `pivot_table.pivot_field(name)` 或 `pivot_table.pivot_fields()` 获取实例。

    Example:
        field = pivot_table.pivot_field("销售额")
        field.orientation = "row"
        field.position = 1
        field.auto_sort("descending", "销售额")
    """

    __setattr__ = _make_setattr_guard(
        frozenset(['_ctx', '_sheet_name', '_table_name', '_name',
                   '_orientation', '_position', '_function', '_caption',
                   '_source_name', '_number_format',
                   'orientation', 'position', 'function', 'caption', 'number_format']),
        ['orientation', 'position', 'function', 'caption', 'number_format']
    )

    def __init__(self, ctx: _Context, sheet_name: str, table_name: str,
                 name: str, orientation: int = 0, position: int = 0,
                 function: int = 0, caption: str = '', source_name: str = '',
                 number_format: str = ''):
        self._ctx = ctx
        self._sheet_name = sheet_name
        self._table_name = table_name
        self._name = name
        self._orientation = orientation
        self._position = position
        self._function = function
        self._caption = caption
        self._source_name = source_name
        self._number_format = number_format

    def _field_js_ref(self) -> str:
        """生成访问当前字段的 JSA 代码片段"""
        return (
            f'Application.Worksheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)})'
            f'.PivotTables({json.dumps(self._table_name, ensure_ascii=False)})'
            f'.PivotFields({json.dumps(self._name, ensure_ascii=False)})'
        )

    @property
    def name(self) -> str:
        """字段名称"""
        return self._name

    @property
    def source_name(self) -> str:
        """原始数据源中的字段名称"""
        return self._source_name

    @property
    def orientation(self) -> str:
        """字段方向: 'hidden', 'row', 'column', 'page', 'data'"""
        return _ORIENTATION_REVERSE.get(self._orientation, 'hidden')

    @orientation.setter
    def orientation(self, value: str):
        if value not in _ORIENTATION_MAP:
            raise ValueError(
                f"不支持的字段方向: {value}，"
                f"支持的方向: {', '.join(_ORIENTATION_MAP.keys())}"
            )
        xl_value = _ORIENTATION_MAP[value]
        code = f'{self._field_js_ref()}.Orientation = {xl_value};'
        self._ctx.queue_script(
            code,
            log_message=f"设置字段 {self._name} 方向: {value}"
        )
        self._orientation = xl_value

    @property
    def position(self) -> int:
        """字段在行/列中的位置"""
        return self._position

    @position.setter
    def position(self, value: int):
        if value < 1:
            raise ValueError(f"位置必须大于 0，当前值: {value}")
        code = f'{self._field_js_ref()}.Position = {value};'
        self._ctx.queue_script(
            code,
            log_message=f"设置字段 {self._name} 位置: {value}"
        )
        self._position = value

    @property
    def function(self) -> str:
        """汇总函数: 'sum'(求和), 'count'(计数), 'average'(平均), 'max'(最大), 'min'(最小), 'product'(乘积), 'count_nums'(数值计数), 'stdev'(标准差), 'var'(方差)"""
        return _FUNCTION_REVERSE.get(self._function, 'sum')

    @function.setter
    def function(self, value: str):
        if value not in _FUNCTION_MAP:
            raise ValueError(
                f"不支持的汇总函数: {value}，"
                f"支持的函数: {', '.join(_FUNCTION_MAP.keys())}"
            )
        xl_value = _FUNCTION_MAP[value]
        # WPS 会在修改 Function 后自动重命名数据字段（如 "销售额求和" → "平均值项:销售额"），
        # 所以用同一段脚本先修改再读回新名称，确保后续操作用的是正确的字段引用。
        code = (
            f'let f = {self._field_js_ref()};\n'
            f'f.Function = {xl_value};\n'
            f'return {{ name: f.Name, caption: f.Caption }};'
        )
        res = self._ctx.evaluate_script_v2(code)
        if not res.get('success', True):
            print(f"设置汇总函数失败: {res.get('error', '未知错误')}")
            return
        info = _jsa_result(res)
        self._function = xl_value
        old_name = self._name
        if isinstance(info, dict):
            self._name = info.get("name", self._name)
            self._caption = info.get("caption", self._caption)
        print(f"设置字段 {old_name} 汇总函数: {value}")

    @property
    def caption(self) -> str:
        """字段标题"""
        return self._caption

    @caption.setter
    def caption(self, value: str):
        code = f'{self._field_js_ref()}.Caption = {json.dumps(value, ensure_ascii=False)}; return "ok";'
        res = self._ctx.evaluate_script_v2(code)
        if res is not None and not res.get('success', True):
            print(f"设置标题失败: {res.get('error', '未知错误')}")
            return
        self._caption = value
        print(f"设置字段 {self._name} 标题: {value}")

    @property
    def number_format(self) -> str:
        """数字格式代码"""
        return self._number_format

    @number_format.setter
    def number_format(self, value: str):
        code = f'{self._field_js_ref()}.NumberFormat = {json.dumps(value, ensure_ascii=False)};'
        self._ctx.queue_script(
            code,
            log_message=f"设置字段 {self._name} 数字格式: {value}"
        )
        self._number_format = value

    def auto_sort(self, order: str, field_name: str) -> None:
        """设置字段排序（同步执行，确保排序立即生效）

        Args:
            order: 排序方式，'ascending'(升序) 或 'descending'(降序)
            field_name: 排序依据的字段名称

        Example:
            >>> field.auto_sort("descending", "销售额")
        """
        if order not in _SORT_ORDER_MAP:
            raise ValueError(
                f"不支持的排序方式: {order}，"
                f"支持的方式: {', '.join(_SORT_ORDER_MAP.keys())}"
            )
        xl_order = _SORT_ORDER_MAP[order]
        code = f'{self._field_js_ref()}.AutoSort({xl_order}, {json.dumps(field_name, ensure_ascii=False)}); return "ok";'
        res = self._ctx.evaluate_script_v2(code)
        if res is not None and not res.get('success', True):
            print(f"排序失败: {res.get('error', '未知错误')}")
            return
        print(f"设置字段 {self._name} 排序: {order} by {field_name}")

    def clear_all_filters(self) -> None:
        """清除该字段的所有筛选"""
        code = f'{self._field_js_ref()}.ClearAllFilters();'
        self._ctx.queue_script(
            code,
            log_message=f"清除字段 {self._name} 所有筛选"
        )

    def clear_label_filters(self) -> None:
        """清除该字段的标签筛选"""
        code = f'{self._field_js_ref()}.ClearLabelFilters();'
        self._ctx.queue_script(
            code,
            log_message=f"清除字段 {self._name} 标签筛选"
        )

    def clear_value_filters(self) -> None:
        """清除该字段的值筛选"""
        code = f'{self._field_js_ref()}.ClearValueFilters();'
        self._ctx.queue_script(
            code,
            log_message=f"清除字段 {self._name} 值筛选"
        )

    def delete(self) -> None:
        """从透视表中删除该字段（同步执行，确保后续查询能立即看到结果）

        data 字段（值区域）不支持 JSA Delete()，自动改用 Orientation=hidden 实现移除。
        """
        if _ORIENTATION_REVERSE.get(self._orientation) == 'data':
            code = f'{self._field_js_ref()}.Orientation = {_ORIENTATION_MAP["hidden"]}; return "ok";'
        else:
            code = f'{self._field_js_ref()}.Delete(); return "ok";'
        res = self._ctx.evaluate_script_v2(code)
        if res is not None and not res.get('success', True):
            print(f"删除字段失败: {res.get('error', '未知错误')}")
            return
        self._orientation = _ORIENTATION_MAP['hidden']
        print(f"删除字段 {self._name}")

    def pivot_items(self) -> list['PivotItem']:
        """获取该字段的所有数据项

        Returns:
            list[PivotItem]: 数据项列表
        """
        script = f'''
let field = {self._field_js_ref()};
let items = [];
for (let i = 1; i <= field.PivotItems().Count; i++) {{
    let item = field.PivotItems(i);
    items.push({{
        name: item.Name,
        visible: item.Visible,
        position: item.Position
    }});
}}
return {{ items: items }};'''
        res = self._ctx.evaluate_script_v2(script.strip())
        if not res.get('success', True):
            print(f"获取字段 {self._name} 数据项失败: {res.get('error', '未知错误')}")
            return []
        info = _jsa_result(res)
        if not isinstance(info, dict):
            return []
        items_data = info.get("items", [])
        return [
            PivotItem(
                ctx=self._ctx,
                sheet_name=self._sheet_name,
                table_name=self._table_name,
                field_name=self._name,
                name=item.get("name", ""),
                position=item.get("position", 0),
                visible=item.get("visible", True),
            )
            for item in items_data
            if isinstance(item, dict)
        ]

    def __repr__(self) -> str:
        return (
            f"PivotField(name={self._name!r}, "
            f"orientation={self.orientation!r}, position={self._position})"
        )


# ============ PivotTable ============

class PivotTable:
    """数据透视表对象，用于管理透视表的字段布局、刷新、样式和删除。

    Note:
        通过 `sheet.pivot_table_wizard()` 创建，或通过 `sheet.pivot_table(name)` 获取实例。

    Example:
        # 创建透视表
        pvt = sheet.pivot_table_wizard("A1:E100", table_destination="G1", table_name="销售分析")
        # 配置字段
        pvt.pivot_field("产品").orientation = "row"
        pvt.pivot_field("地区").orientation = "column"
        pvt.add_data_field("金额", caption="金额求和", function="sum")
        # 刷新
        pvt.refresh()

    Raises:
        ValueError: 参数无效
        Exception: API 请求执行错误
    """

    __setattr__ = _make_setattr_guard(
        frozenset(['_ctx', '_sheet_name', '_table_name', 'source_data']),
        ['source_data']
    )

    def __init__(self, ctx: _Context, sheet_name: str, table_name: str):
        self._ctx = ctx
        self._sheet_name = sheet_name
        self._table_name = table_name

    def _table_js_ref(self) -> str:
        """生成访问当前透视表的 JSA 代码片段"""
        return (
            f'Application.Worksheets.Item({json.dumps(self._sheet_name, ensure_ascii=False)})'
            f'.PivotTables({json.dumps(self._table_name, ensure_ascii=False)})'
        )

    # ---------- 只读属性 ----------

    @property
    def name(self) -> str:
        """透视表名称"""
        return self._table_name

    def _get_property(self, prop_name: str) -> Any:
        """通用属性读取"""
        script = f'return {self._table_js_ref()}.{prop_name};'
        res = self._ctx.evaluate_script_v2(script)
        if not res.get('success', True):
            print(f"获取透视表属性 {prop_name} 失败: {res.get('error', '未知错误')}")
            return None
        return _jsa_result(res)

    @property
    def source_data(self) -> str:
        """数据源引用，A1 格式，如 'Sheet1!A1:B14'"""
        raw = self._get_property("SourceData") or ""
        return _r1c1_to_a1(raw) if raw else ""

    @source_data.setter
    def source_data(self, value: str):
        ref = self._table_js_ref()
        code = (
            f'{ref}.SourceData = {json.dumps(value, ensure_ascii=False)};\n'
            f'{ref}.RefreshTable();\n'
            f'return "ok";'
        )
        res = self._ctx.evaluate_script_v2(code)
        if res is not None and not res.get('success', True):
            raise Exception(f"设置数据源失败: {res.get('error', '未知错误')}")
        print(f"透视表 {self._table_name} 数据源已更新为: {value}")

    @property
    def location(self) -> str:
        """透视表左上角单元格地址"""
        script = f'return {self._table_js_ref()}.TableRange2.Cells(1, 1).Address();'
        res = self._ctx.evaluate_script_v2(script)
        if not res.get('success', True):
            print(f"获取透视表位置失败: {res.get('error', '未知错误')}")
            return ""
        return _jsa_result(res) or ""

    @property
    def row_grand(self) -> bool:
        """是否显示行总计"""
        val = self._get_property("RowGrand")
        return bool(val) if val is not None else True

    @property
    def column_grand(self) -> bool:
        """是否显示列总计"""
        val = self._get_property("ColumnGrand")
        return bool(val) if val is not None else True

    @property
    def table_range(self) -> str:
        """透视表完整区域地址（含页字段）"""
        script = f'return {self._table_js_ref()}.TableRange2.Address();'
        res = self._ctx.evaluate_script_v2(script)
        if not res.get('success', True):
            print(f"获取透视表区域失败: {res.get('error', '未知错误')}")
            return ""
        result = _jsa_result(res)
        return result if isinstance(result, str) else ""

    # ---------- 字段访问 ----------

    def _get_fields_by_category(self, method: str) -> list['PivotField']:
        """获取指定类别的字段列表"""
        script = f'''
let pvt = {self._table_js_ref()};
let fields = [];
for (let i = 1; i <= pvt.{method}().Count; i++) {{
    let f = pvt.{method}(i);
    fields.push({{
        name: f.Name,
        orientation: f.Orientation,
        position: f.Position,
        function: f.Function,
        caption: f.Caption,
        sourceName: f.SourceName,
        numberFormat: f.NumberFormat
    }});
}}
return {{ fields: fields }};'''
        res = self._ctx.evaluate_script_v2(script.strip())
        if not res.get('success', True):
            print(f"获取透视表 {method} 失败: {res.get('error', '未知错误')}")
            return []
        info = _jsa_result(res)
        if not isinstance(info, dict):
            return []
        fields = [
            PivotField(
                ctx=self._ctx,
                sheet_name=self._sheet_name,
                table_name=self._table_name,
                name=f.get("name", ""),
                orientation=f.get("orientation", 0),
                position=f.get("position", 0),
                function=f.get("function", 0),
                caption=f.get("caption", ""),
                source_name=f.get("sourceName", ""),
                number_format=f.get("numberFormat", ""),
            )
            for f in info.get("fields", [])
            if isinstance(f, dict)
        ]
        return fields

    def pivot_fields(self) -> list['PivotField']:
        """获取所有字段

        Returns:
            list[PivotField]: 所有字段列表
        """
        return self._get_fields_by_category("PivotFields")

    def pivot_field(self, name: str) -> 'PivotField':
        """按名称获取单个字段

        Args:
            name: 字段名称

        Returns:
            PivotField: 字段对象

        Raises:
            ValueError: 字段不存在
        """
        script = f'''
let f = {self._table_js_ref()}.PivotFields({json.dumps(name, ensure_ascii=False)});
return {{
    name: f.Name,
    orientation: f.Orientation,
    position: f.Position,
    function: f.Function,
    caption: f.Caption,
    sourceName: f.SourceName,
    numberFormat: f.NumberFormat
}};'''
        res = self._ctx.evaluate_script_v2(script.strip())
        if not res.get('success', True):
            raise ValueError(f"字段 '{name}' 不存在或获取失败: {res.get('error', '未知错误')}")
        info = _jsa_result(res)
        if not isinstance(info, dict):
            raise ValueError(f"字段 '{name}' 不存在或获取失败")
        return PivotField(
            ctx=self._ctx,
            sheet_name=self._sheet_name,
            table_name=self._table_name,
            name=info.get("name", name),
            orientation=info.get("orientation", 0),
            position=info.get("position", 0),
            function=info.get("function", 0),
            caption=info.get("caption", ""),
            source_name=info.get("sourceName", ""),
            number_format=info.get("numberFormat", ""),
        )

    def row_fields(self) -> list['PivotField']:
        """获取行字段列表（按 position 升序）"""
        fields = self._get_fields_by_category("RowFields")
        fields.sort(key=lambda f: f.position)
        return fields

    def column_fields(self) -> list['PivotField']:
        """获取列字段列表（按 position 升序）"""
        fields = self._get_fields_by_category("ColumnFields")
        fields.sort(key=lambda f: f.position)
        return fields

    def data_fields(self) -> list['PivotField']:
        """获取数据字段列表（值区域，按 position 升序）"""
        fields = self._get_fields_by_category("DataFields")
        fields.sort(key=lambda f: f.position)
        return fields

    def page_fields(self) -> list['PivotField']:
        """获取页字段列表（筛选器，按 position 升序）"""
        fields = self._get_fields_by_category("PageFields")
        fields.sort(key=lambda f: f.position)
        return fields

    # ---------- 更新操作 ----------

    def add_data_field(self, field_name: str,
                       caption: str = '',
                       function: str = 'sum') -> None:
        """添加数据字段到值区域

        Args:
            field_name: 源字段名称
            caption: 值区域显示的标题（如 "金额求和"），留空则使用默认标题
            function: 汇总函数，支持 'sum', 'count', 'average', 'max', 'min',
                      'product', 'count_nums', 'stdev', 'var'，默认 'sum'

        Example:
            >>> pvt.add_data_field("金额", caption="金额求和", function="sum")
            >>> pvt.add_data_field("数量", function="count")
        """
        if function not in _FUNCTION_MAP:
            raise ValueError(
                f"不支持的汇总函数: {function}，"
                f"支持的函数: {', '.join(_FUNCTION_MAP.keys())}"
            )
        xl_func = _FUNCTION_MAP[function]
        pvt_ref = self._table_js_ref()
        caption_arg = f', {json.dumps(caption, ensure_ascii=False)}' if caption else ''
        code = f'{pvt_ref}.AddDataField({pvt_ref}.PivotFields({json.dumps(field_name, ensure_ascii=False)}){caption_arg}, {xl_func}); return "ok";'
        res = self._ctx.evaluate_script_v2(code)
        if res is not None and not res.get('success', True):
            print(f"添加数据字段失败: 字段 '{field_name}' 可能不存在于数据源中，请检查数据源的列标题")
            return
        print(f"添加数据字段: {field_name} ({function})")

    def add_fields(self,
                   row_fields: list[str] | None = None,
                   column_fields: list[str] | None = None,
                   page_fields: list[str] | None = None) -> None:
        """批量添加行/列/页字段

        Args:
            row_fields: 行字段名称列表
            column_fields: 列字段名称列表
            page_fields: 页字段名称列表

        Example:
            >>> pvt.add_fields(row_fields=["产品", "地区"], column_fields=["月份"])
        """
        pvt_ref = self._table_js_ref()
        args = []
        if row_fields:
            arr = json.dumps(row_fields, ensure_ascii=False)
            args.append(arr)
        else:
            args.append('undefined')
        if column_fields:
            arr = json.dumps(column_fields, ensure_ascii=False)
            args.append(arr)
        else:
            args.append('undefined')
        if page_fields:
            arr = json.dumps(page_fields, ensure_ascii=False)
            args.append(arr)
        else:
            args.append('undefined')
        code = f'{pvt_ref}.AddFields({", ".join(args)});'
        self._ctx.queue_script(
            code,
            log_message=f"批量添加字段: row={row_fields}, col={column_fields}, page={page_fields}"
        )

    def refresh(self) -> None:
        """用源数据刷新透视表

        Example:
            >>> pvt.refresh()
        """
        code = f'{self._table_js_ref()}.RefreshTable();'
        self._ctx.queue_script(code, log_message=f"刷新透视表: {self._table_name}")

    def clear_all_filters(self) -> None:
        """清除透视表的所有筛选

        Example:
            >>> pvt.clear_all_filters()
        """
        code = f'{self._table_js_ref()}.ClearAllFilters();'
        self._ctx.queue_script(
            code,
            log_message=f"清除透视表 {self._table_name} 所有筛选"
        )

    # ---------- 样式设置 ----------

    def set_table_style(self, style_name: str) -> None:
        """设置透视表样式

        Args:
            style_name: 样式名称，格式 "PivotStyle{类别}{编号}"
                类别: Light(浅色) / Medium(中等) / Dark(深色)，各 28 种
                编号: 1-28，每 7 个一组循环配色：
                    1,8,15,22=黑  2,9,16,23=蓝  3,10,17,24=橙
                    4,11,18,25=灰  5,12,19,26=黄  6,13,20,27=浅蓝  7,14,21,28=绿
                编号段决定视觉特征（以 Medium 为例）：
                    1-7: 填充表头 + 条纹行 + 底部边框
                    8-14: 填充表头 + 条纹行 + 汇总行边框
                    15-21: 填充表头 + 条纹行 + 外边框
                    22-28: 填充表头 + 填充表尾 + 条纹行
                推荐: PivotStyleLight16

        Example:
            >>> pvt.set_table_style("PivotStyleLight16")
        """
        code = f'{self._table_js_ref()}.TableStyle2 = {json.dumps(style_name, ensure_ascii=False)};'
        self._ctx.queue_script(
            code,
            log_message=f"设置透视表样式: {style_name}"
        )

    def row_axis_layout(self, layout: str) -> None:
        """设置行区域版式

        Args:
            layout: 版式类型，'compact'(压缩形式) / 'tabular'(表格形式) / 'outline'(大纲形式)

        Example:
            >>> pvt.row_axis_layout("tabular")
        """
        if layout not in _LAYOUT_MAP:
            raise ValueError(
                f"不支持的版式类型: {layout}，"
                f"支持的类型: {', '.join(_LAYOUT_MAP.keys())}"
            )
        xl_layout = _LAYOUT_MAP[layout]
        code = f'{self._table_js_ref()}.RowAxisLayout({xl_layout});'
        self._ctx.queue_script(
            code,
            log_message=f"设置透视表版式: {layout}"
        )

    def subtotal_location(self, location: str) -> None:
        """设置分类汇总位置

        Args:
            location: 位置，'top'(顶部) 或 'bottom'(底部)

        Example:
            >>> pvt.subtotal_location("top")
        """
        if location not in _SUBTOTAL_LOCATION_MAP:
            raise ValueError(
                f"不支持的汇总位置: {location}，"
                f"支持的位置: {', '.join(_SUBTOTAL_LOCATION_MAP.keys())}"
            )
        xl_loc = _SUBTOTAL_LOCATION_MAP[location]
        code = f'{self._table_js_ref()}.SubtotalLocation({xl_loc});'
        self._ctx.queue_script(
            code,
            log_message=f"设置分类汇总位置: {location}"
        )

    def set_grand_total_name(self, name: str) -> None:
        """设置总计标题文字

        Args:
            name: 总计标题文字（如 "合计"）

        Example:
            >>> pvt.set_grand_total_name("合计")
        """
        code = f'{self._table_js_ref()}.GrandTotalName = {json.dumps(name, ensure_ascii=False)};'
        self._ctx.queue_script(
            code,
            log_message=f"设置总计标题: {name}"
        )

    def set_merge_labels(self, merge: bool) -> None:
        """设置是否合并标签（仅在 outline 大纲形式下生效，tabular/compact 下无效）

        需要先调用 row_axis_layout("outline") 切换为大纲形式，再设置合并标签。

        Args:
            merge: True 合并，False 不合并

        Example:
            >>> pvt.row_axis_layout("outline")
            >>> pvt.set_merge_labels(True)
        """
        code = f'{self._table_js_ref()}.MergeLabels = {str(merge).lower()};'
        self._ctx.queue_script(
            code,
            log_message=f"设置合并标签: {merge}"
        )

    def set_row_grand(self, show: bool) -> None:
        """设置是否显示行总计

        Args:
            show: True 显示，False 隐藏

        Example:
            >>> pvt.set_row_grand(False)
        """
        code = f'{self._table_js_ref()}.RowGrand = {str(show).lower()};'
        self._ctx.queue_script(
            code,
            log_message=f"设置行总计显示: {show}"
        )

    def set_column_grand(self, show: bool) -> None:
        """设置是否显示列总计

        Args:
            show: True 显示，False 隐藏

        Example:
            >>> pvt.set_column_grand(False)
        """
        code = f'{self._table_js_ref()}.ColumnGrand = {str(show).lower()};'
        self._ctx.queue_script(
            code,
            log_message=f"设置列总计显示: {show}"
        )

    # ---------- 计算字段 ----------

    def add_calculated_field(self, name: str, formula: str) -> None:
        """添加计算字段

        Args:
            name: 计算字段名称
            formula: 公式表达式（如 "= 利润 / 销售额"）

        Example:
            >>> pvt.add_calculated_field("利润率", "= 利润 / 销售额")
        """
        code = (
            f'{self._table_js_ref()}.CalculatedFields().Add('
            f'{json.dumps(name, ensure_ascii=False)}, '
            f'{json.dumps(formula, ensure_ascii=False)});'
        )
        self._ctx.queue_script(
            code,
            log_message=f"添加计算字段: {name}"
        )

    # ---------- 删除操作 ----------

    def delete(self) -> None:
        """删除整个数据透视表（清除透视表占据的全部区域）

        Example:
            >>> pvt.delete()
        """
        code = f'{self._table_js_ref()}.TableRange2.Clear();'
        self._ctx.queue_script(
            code,
            log_message=f"删除透视表: {self._table_name}"
        )

    def clear_table(self) -> None:
        """清空透视表（移除所有字段、筛选和排序，重置为初建状态）

        Example:
            >>> pvt.clear_table()
        """
        code = f'{self._table_js_ref()}.ClearTable();'
        self._ctx.queue_script(
            code,
            log_message=f"清空透视表: {self._table_name}"
        )

    def __repr__(self) -> str:
        return f"PivotTable(name={self._table_name!r}, sheet={self._sheet_name!r})"
