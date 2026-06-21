# 依赖说明（拼接执行时已在命名空间中）：
# - json, Literal, Any 等标准库来自 summary.py / _utils.py
# - _Context, _SheetMeta, ... 来自 _utils.py
# - ServerAPISheetDataSource, SummaryBuilder, format_range_address 来自 summary.py
# - Range 来自 range.py
# - PivotTable 来自 pivot_table.py（在 sheet.py 之后加载，方法调用时才引用）

# ============ Sheet ============

class Sheet:
    """工作表操作，用于获取单元格区域和添加图表。
    
    Note:
        通过 `workbook.sheet(name)` 获取实例，类名为 Sheet。
        更多操作（读写数据、设置样式、合并单元格等）请通过 Range 对象进行。
    
    Raises:
        Exception: 设置失败时抛出异常

    Example:
        sheet = workbook.sheet("Sheet1")
        print(sheet.used_range)
        
        # 读写数据通过 Range 对象
        # 逐行写入
        sheet.range("A1:B1").value = [["Name", "Age"]]
        sheet.range("A2:B2").value = [["Alice", 25]]
        # 逐列写入
        sheet.range("C1:C2").value = [["Dept"], ["Tech"]]
        #图表信息
        chart_information = sheet.chart_information()
        


    Raises:
        ValueError: 无效的地址格式（range）或不支持的图表类型（add_chart）
        XLError: 权限不足
        Exception: API 请求执行错误
    """

    __setattr__ = _make_setattr_guard(
        frozenset(['_ctx', '_meta', '_chart_information']),
        []  # Sheet 没有可写的 property
    )

    def __init__(self, ctx: _Context, meta: _SheetMeta):
        self._ctx = ctx
        self._meta = meta
        self._chart_information: dict[int, dict[str, str]] | None = None

    @property
    def name(self) -> str:
        """工作表名称"""
        return self._meta.name

    @property
    def id(self) -> int:
        """工作表 ID"""
        return self._meta.id

    @property
    def used_range(self) -> Range:
        """已使用区域（含数据的最小矩形），返回 Range 对象，可用 print() 查看数据摘要。"""
        return Range(
            self._ctx, self._meta.id, self._meta.name,
            self._meta.row_from, self._meta.row_to,
            self._meta.col_from, self._meta.col_to
        )

    def _parse_range(self, addr: str) -> tuple[int, int, int, int]:
        row_from, row_to, col_from, col_to = _parse_range(addr)
        if row_from == _INDEX_NONE:
            row_from = self._meta.row_from
        if row_to == _INDEX_NONE:
            row_to = self._meta.row_to
        if col_from == _INDEX_NONE:
            col_from = self._meta.col_from
        if col_to == _INDEX_NONE:
            col_to = self._meta.col_to
        return row_from, row_to, col_from, col_to

    def range(self, addr: str) -> Range:
        """获取区域对象
        
        Args:
            addr: A1 格式地址，支持以下格式：
                - 单个单元格: 'A1', 'B2', 'AA100'
                - 矩形区域: 'A1:B10', 'C3:D5'
                - 整列: 'A:A', 'B:C'
                - 整行: '1:1', '2:5'
        
        格式要求:
            - 列字母必须大写（A-Z，支持多字母如AA、AB）
            - 行号必须是正整数
            - 区域用冒号分隔起止位置
            - 不支持逗号分隔的多区域（如 'A1:A5, B1:B5'），需分开调用
            - 错误示例: 'a1'(小写), 'A1,B1'(多区域), 'A1-B2'(错误分隔符)
        
        Returns:
            Range: 区域对象
        
        Example:
            >>> sheet.range('A1')           # 单个单元格
            >>> sheet.range('A1:C10')       # 矩形区域
            >>> sheet.range('A:A')          # 整列
        """
        row_from, row_to, col_from, col_to = self._parse_range(addr)
        return Range(
            self._ctx, self._meta.id, self._meta.name,
            row_from, row_to, col_from, col_to
        )

    def add_chart(self,
                  chart_type: str,
                  source_address: str,
                  rect_address: str,
                  title: str,
                  plot_by: Literal['rows', 'columns'] = 'columns') -> Any:
        """添加图表。添加图表前需要调用chart_information函数查看当前工作表图表情况,图表之间需要避免遮盖
        
        Args:
            chart_type: 图表类型，支持 31 种细分类型（见下方列表）。
            source_address: 数据源地址（如 `"A1:D5"` 或跨表 `"'数据表'!A1:D5"`）。
                - 对于柱形图/条形图/折线图，第一行为图例，第一列为分类轴标签。
                - 对于饼图，需要两列数据：分类名和对应的值。
            rect_address: 图表摆放位置（如 `"F1:L10"`）。
            title: 图表标题
            plot_by: 数据组织方式，'rows'(按行) 或 'columns'(按列)，默认 'columns'
        
        Note:
            #### 支持的图表类型

            **柱形图（Column）**
            * `"column_clustered"` - 簇状柱形图（最常用）
            * `"column_stacked"` - 堆积柱形图
            * `"column_stacked_100"` - 百分比堆积柱形图

            **条形图（Bar）**
            * `"bar_clustered"` - 簇状条形图
            * `"bar_stacked"` - 堆积条形图
            * `"bar_stacked_100"` - 百分比堆积条形图

            **折线图（Line）**
            * `"line"` - 折线图
            * `"line_stacked"` - 堆积折线图
            * `"line_stacked_100"` - 百分比堆积折线图
            * `"line_markers"` - 带数据标记的折线图
            * `"line_markers_stacked"` - 带数据标记的堆积折线图
            * `"line_markers_stacked_100"` - 带数据标记的百分比堆积折线图

            **饼图（Pie）**
            * `"pie"` - 饼图
            * `"pie_of_pie"` - 复合饼图
            * `"bar_of_pie"` - 复合条饼图
            * `"doughnut"` - 圆环图

            **面积图（Area）**
            * `"area"` - 面积图
            * `"area_stacked"` - 堆积面积图
            * `"area_stacked_100"` - 百分比堆积面积图

            **散点图（Scatter）**
            * `"scatter"` - 散点图
            * `"scatter_smooth"` - 带平滑线和数据标记点的散点图
            * `"scatter_smooth_no_markers"` - 带平滑线的散点图
            * `"scatter_lines"` - 带直线和数据标记点的散点图
            * `"scatter_lines_no_markers"` - 带直线的散点图
            * `"bubble"` - 气泡图

            **雷达图（Radar）**
            * `"radar"` - 雷达图
            * `"radar_markers"` - 带数据标记的雷达图
            * `"radar_filled"` - 填充雷达图

            **股票图（Stock）**
            * `"stock_hlc"` - 盘高-盘低-收盘图
            * `"stock_ohlc"` - 开盘-盘高-盘低-收盘图
            * `"stock_vhlc"` - 成交量-盘高-盘低-收盘图
            * `"stock_vohlc"` - 成交量-开盘-盘高-盘低-收盘图

        Example:
            >>> # 使用当前工作表数据
            >>> sheet.add_chart("column_clustered", "A1:D5", "F1:L10", "销售对比")
            >>> # 使用其他工作表数据
            >>> sheet.add_chart("line", "'数据表'!A1:B10", "F1:L10", "趋势图")
        """
        # 图表类型映射：chart_type_string -> (chartType_id, chartStyle_id)
        chart_type_map = {
            # 柱形图
            'column_clustered': (51, 201),
            'column_stacked': (52, 297),
            'column_stacked_100': (53, 297),
            # 条形图
            'bar_clustered': (57, 216),
            'bar_stacked': (58, 297),
            'bar_stacked_100': (59, 297),
            # 折线图
            'line': (4, 227),
            'line_stacked': (63, 227),
            'line_stacked_100': (64, 227),
            'line_markers': (65, 332),
            'line_markers_stacked': (66, 332),
            'line_markers_stacked_100': (67, 332),
            # 饼图
            'pie': (5, 251),
            'pie_of_pie': (68, 333),
            'bar_of_pie': (71, 333),
            'doughnut': (-4120, 251),
            # 面积图
            'area': (1, 276),
            'area_stacked': (76, 276),
            'area_stacked_100': (77, 276),
            # 散点图
            'scatter': (-4169, 240),
            'scatter_smooth': (72, 240),
            'scatter_smooth_no_markers': (73, 240),
            'scatter_lines': (74, 240),
            'scatter_lines_no_markers': (75, 240),
            'bubble': (15, 269),
            # 雷达图
            'radar': (-4151, 317),
            'radar_markers': (81, 317),
            'radar_filled': (82, 317),
            # 股票图
            'stock_hlc': (88, 322),
            'stock_ohlc': (89, 322),
            'stock_vhlc': (90, 322),
            'stock_vohlc': (91, 322),
        }

        if chart_type not in chart_type_map:
            raise ValueError(f"不支持的图表类型: {chart_type}，支持的类型: {', '.join(chart_type_map.keys())}")
        chart_type_id, chart_style_id = chart_type_map[chart_type]

        plot_by_types = {
            'rows': 1,      # xlRows
            'columns': 2,   # xlColumns
        }
        plot_by_id = plot_by_types.get(plot_by, 2)

        self._ctx.flush()
        if not self.insert_chart_is_legality(rect_address):
            print(f"插入图表: {chart_type} 到 sheet: {self.name} 区域: {rect_address} 失败，图表之间需要避免遮盖")
            for chart in self._chart_information.values():
                if chart.get("topLeftCell") == rect_address:
                    print(f"图表: {chart.get('name')} 位置: {chart.get('topLeftCell')} - {chart.get('bottomRightCell')}")
            return

        code = f'''let sheet = Sheets.Item({json.dumps(self.name, ensure_ascii=False)});
sheet.Activate();
let range = sheet.Range({json.dumps(rect_address, ensure_ascii=False)});
sheet.Shapes.AddChart2({chart_style_id}, {chart_type_id}, range.Left, range.Top, range.Width, range.Height);
let count = sheet.Shapes.Count;
let chart = Application.ActiveSheet.Shapes.Item(count).Chart;
chart.SetSourceData(Application.Range({json.dumps(source_address, ensure_ascii=False)}), {plot_by_id});
chart.SetElement(msoElementChartTitleAboveChart);
chart.ChartTitle.Text = {json.dumps(title, ensure_ascii=False)};
chart.HasLegend = true;
chart.Legend.Position = xlLegendPositionBottom;
'''
        self._ctx.queue_script(code.strip(), log_message=f"添加图表: {chart_type} 到 sheet: {self.name} 区域: {rect_address} 成功")
    
    def delete_chart(self,index: int):
        """删除图表
        Args:
            index: 图表索引
        """
        script = f'''
        let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
        sheet.ChartObjects({index}).Delete();
        '''
        self._ctx.queue_script(script.strip(), log_message=f"删除图表: {index} 到 sheet: {self.name}")#走jsa,一套缓存逻辑就够了,不用像server api区分写和删
    
    def update_chart_title(self, index: int, title: str):
        """修改图表标题
        Args:
            index: 图表索引
            title: 新的图表标题
        """
        script = f'''
        let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
        let chart = sheet.ChartObjects({index}).Chart;
        if (chart.HasTitle) {{
            chart.ChartTitle.Text = {json.dumps(title, ensure_ascii=False)};
        }} else {{
            chart.SetElement(msoElementChartTitleAboveChart);
            chart.ChartTitle.Text = {json.dumps(title, ensure_ascii=False)};
        }}
        '''
        self._ctx.queue_script(script.strip(), log_message=f"修改图表标题: {index} 到 sheet: {self.name}")
    
    def update_chart_data_source(self, index: int, source_address: str, plot_by: Literal['rows', 'columns'] = 'columns'):
        """修改图表数据源
        Args:
            index: 图表索引
            source_address: 新的数据源地址（如 "A1:D5" 或跨表 "'数据表'!A1:D5"）
            plot_by: 数据组织方式，'rows'(按行) 或 'columns'(按列)，默认 'columns'
        """
        plot_by_types = {
            'rows': 1,      # xlRows
            'columns': 2,   # xlColumns
        }
        plot_by_id = plot_by_types.get(plot_by, 2)
        
        script = f'''
        let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
        let chart = sheet.ChartObjects({index}).Chart;
        chart.SetSourceData(Application.Range({json.dumps(source_address, ensure_ascii=False)}), {plot_by_id});
        '''
        self._ctx.queue_script(script.strip(), log_message=f"修改图表数据源: {index} 到 sheet: {self.name}")
    
    def update_chart_position(self, index: int, rect_address: str):
        """修改图表位置
        Args:
            index: 图表索引
            rect_address: 新的图表摆放位置（如 "F1:L10"）

        注意：不支持跨工作表移动图表。
        """
        script = f'''
        let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
        let chartObj = sheet.ChartObjects({index});
        let range = sheet.Range({json.dumps(rect_address, ensure_ascii=False)});
        chartObj.Left = range.Left;
        chartObj.Top = range.Top;
        chartObj.Width = range.Width;
        chartObj.Height = range.Height;
        '''
        self._ctx.queue_script(script.strip(), log_message=f"修改图表位置: {index} 到 sheet: {self.name}")
    
    def update_chart_type(self, index: int, chart_type: str):
        """修改图表类型
        Args:
            index: 图表索引
            chart_type: 新的图表类型，支持 31 种细分类型（同 add_chart 方法）
        """
        # 图表类型映射：chart_type_string -> (chartType_id, chartStyle_id)
        chart_type_map = {
            # 柱形图
            'column_clustered': (51, 201),
            'column_stacked': (52, 297),
            'column_stacked_100': (53, 297),
            # 条形图
            'bar_clustered': (57, 216),
            'bar_stacked': (58, 297),
            'bar_stacked_100': (59, 297),
            # 折线图
            'line': (4, 227),
            'line_stacked': (63, 227),
            'line_stacked_100': (64, 227),
            'line_markers': (65, 332),
            'line_markers_stacked': (66, 332),
            'line_markers_stacked_100': (67, 332),
            # 饼图
            'pie': (5, 251),
            'pie_of_pie': (68, 333),
            'bar_of_pie': (71, 333),
            'doughnut': (-4120, 251),
            # 面积图
            'area': (1, 276),
            'area_stacked': (76, 276),
            'area_stacked_100': (77, 276),
            # 散点图
            'scatter': (-4169, 240),
            'scatter_smooth': (72, 240),
            'scatter_smooth_no_markers': (73, 240),
            'scatter_lines': (74, 240),
            'scatter_lines_no_markers': (75, 240),
            'bubble': (15, 269),
            # 雷达图
            'radar': (-4151, 317),
            'radar_markers': (81, 317),
            'radar_filled': (82, 317),
            # 股票图
            'stock_hlc': (88, 322),
            'stock_ohlc': (89, 322),
            'stock_vhlc': (90, 322),
            'stock_vohlc': (91, 322),
        }
        
        if chart_type not in chart_type_map:
            raise ValueError(f"不支持的图表类型: {chart_type}，支持的类型: {', '.join(chart_type_map.keys())}")
        chart_type_id, chart_style_id = chart_type_map[chart_type]
        
        script = f'''
        let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
        let chart = sheet.ChartObjects({index}).Chart;
        chart.ChartType = {chart_type_id};
        chart.ChartStyle = {chart_style_id};
        '''
        self._ctx.queue_script(script.strip(), log_message=f"修改图表类型: {index} 到 sheet: {self.name}")
    
    def update_chart_legend(self, index: int, has_legend: bool, position: str = 'bottom'):
        """修改图表图例
        Args:
            index: 图表索引
            has_legend: 是否显示图例
            position: 图例位置，可选值: 'top', 'bottom', 'left', 'right', 'center'
        """
        position_map = {
            'top': -4160,      # xlLegendPositionTop
            'bottom': -4107,   # xlLegendPositionBottom
            'left': -4131,     # xlLegendPositionLeft
            'right': -4152,    # xlLegendPositionRight
            'center': -4108,   # xlLegendPositionCenter
        }
        position_id = position_map.get(position, -4107)  # 默认底部
        
        script = f'''
        let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
        let chart = sheet.ChartObjects({index}).Chart;
        chart.HasLegend = {str(has_legend).lower()};
        if ({str(has_legend).lower()}) {{
            chart.Legend.Position = {position_id};
        }}
        '''
        self._ctx.queue_script(script.strip(), log_message=f"修改图表图例: {index} 到 sheet: {self.name}")
    
    def update_chart_axis_title(self, index: int, axis_type: Literal['category', 'value'], title: str, visible: bool = True):
        """修改指定坐标轴的显示方式与轴标题。

        **作用范围（每次只动一条轴）**  
        ``axis_type`` 为 ``category`` 时只处理分类轴(X轴)，为 ``value`` 时只处理数值轴(Y轴)
        不会同时隐藏两条轴；另一条轴需再调一次本方法

        Args:
            index: 图表索引（1-based，同 ``chart_information``）
            axis_type: ``category`` 或 ``value``
            title: 轴标题；``visible=True`` 且为空则只开轴、不强制设标题
            visible: 是否显示该坐标轴；``False`` 时关闭该轴及其轴标题
        """
        axis_map = {
            'category': 1,  # xlCategory
            'value': 2,     # xlValue
        }
        axis_id = axis_map.get(axis_type, 1)
        vis_js = 'true' if visible else 'false'
        title_js = json.dumps(title, ensure_ascii=False)

        script = f'''
        let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
        let chart = sheet.ChartObjects({index}).Chart;
        let axisId = {axis_id};
        let xlPrimary = 1;
        let vis = {vis_js};
        let t = {title_js};
        if (vis) {{
            chart.HasAxis(axisId, xlPrimary, true);
        }} else {{
            chart.HasAxis(axisId, xlPrimary, false);
        }}
        let axis = chart.Axes(axisId);
        if (axis) {{
            axis.Visible = vis;
            if (vis) {{
                if (t.length > 0) {{
                    axis.HasTitle = true;
                    axis.AxisTitle.Caption = t;
                    axis.AxisTitle.Text = t;
                }}
            }} else {{
                axis.HasTitle = false;
            }}
        }}
        '''
        self._ctx.queue_script(script.strip(), log_message=f"修改图表坐标轴标题: {index} 到 sheet: {self.name}")


    def chart_information(self, verbose: bool = True) -> dict[int, dict[str, str]] | None:
        """获取当前工作表所有图表对象信息。
        """
        script = f'''
let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
let chartobjects = sheet.ChartObjects();
let chartsInfo = [];
let xlCategory = 1;
let xlValue = 2;

for (let i = 1; i <= chartobjects.Count; i++) {{
    let chartObj = chartobjects.Item(i);
    let chart = chartObj.Chart;

    let axes = {{
        categoryAxis: {{ visible: null, hasTitle: null, title: "" }},
        valueAxis: {{ visible: null, hasTitle: null, title: "" }},
    }};

    let categoryAxis = chart.Axes(xlCategory);
    if (categoryAxis) {{
        axes.categoryAxis.visible = categoryAxis.Visible;
        axes.categoryAxis.hasTitle = categoryAxis.HasTitle;
        if (categoryAxis.HasTitle && categoryAxis.AxisTitle) {{
            axes.categoryAxis.title = categoryAxis.AxisTitle.Text || categoryAxis.AxisTitle.Caption || "";
        }}
    }}

    let valueAxis = chart.Axes(xlValue);
    if (valueAxis) {{
        axes.valueAxis.visible = valueAxis.Visible;
        axes.valueAxis.hasTitle = valueAxis.HasTitle;
        if (valueAxis.HasTitle && valueAxis.AxisTitle) {{
            axes.valueAxis.title = valueAxis.AxisTitle.Text || valueAxis.AxisTitle.Caption || "";
        }}
    }}

    let seriesDetails = [];
    let seriesCount = chart.SeriesCollection().Count;
    for (let j = 1; j <= seriesCount; j++) {{
        let s = chart.SeriesCollection(j);
        seriesDetails.push({{
            index: j,
            name: s.Name || "",
            values: s.Values,
            xValues: s.XValues,
        }});
    }}
    
    chartsInfo.push({{
        index: i,
        name: chartObj.Name,
        chartTitle: chart.HasTitle ? chart.ChartTitle.Text : "",
        topLeftCell: chartObj.TopLeftCell.Address(),
        bottomRightCell: chartObj.BottomRightCell.Address(),
        chartType: chart.ChartType,
        hasLegend: chart.HasLegend,
        axes: axes,
        seriesCount: seriesCount,
        seriesDetails: seriesDetails
    }});
}}

return {{
    count: chartobjects.Count,
    charts: chartsInfo
}};
'''  
# 接口优化统一处理后，现在拿到的信息格式如下：
# {
#   "success": true,
#   "data": {
#     "result": {"charts": [...], "count": N},  // Go 侧已统一提取 return 内容到 result 层
#     "logs": []
#   }
# }
        try:
            res = self._ctx.evaluate_script_v2(script.strip())
            if res is None or not isinstance(res, dict):
                print(f"获取图表信息失败: 脚本返回无效结果 (res={res})")
                print(f"脚本返回信息：{res}")
                return None
            if not res.get("success", True):
                print(f"获取图表信息失败: {res.get('error', '未知错误')}")
                print(f"脚本返回信息：{res}")
                return None
            data = res.get("data")
            if not isinstance(data, dict):
                print(f"获取图表信息失败: data 格式异常 ({type(data).__name__})")
                print(f"脚本返回信息：{res}")
                return None
            
            
            result = data.get("result")
            if result is None:
                print("获取图表信息失败: data 中无 result 字段")
                print(f"脚本返回信息：{res}")
                return None
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except Exception as e:
                    print(f"获取图表信息失败: result JSON 解析异常 ({e})")
                    print(f"脚本返回信息：{res}")
                    return None
            if not isinstance(result, dict):
                print(f"获取图表信息失败: result 不是对象 ({type(result).__name__})")
                print(f"脚本返回信息：{res}")
                return None
            
            
            # Go 侧已统一将 return 内容提取到 result 层，直接使用 result
            info = result
            if not isinstance(info, dict):
                print(f"获取图表信息失败: 图表数据不是对象 ({type(info).__name__ if info is not None else 'None'})")
                print(f"脚本返回信息：{res}")
                return None
            chart_count = info.get("count", 0)
            charts = info.get("charts", [])
            # 无图表时返回的return 字段{"charts":[],"count":0}}
            if not charts or chart_count == 0:
                print(f"{self.name} 没有图表")
                self._chart_information = None
                return None
            
            if verbose:#这个参数是保证判断插入图表是否遮盖已有图表，不多打印图表信息，不增加多余的上下文
                print(f"获取图表信息成功: {self.name} 有 {chart_count} 个图表")
            
            chart_map: dict[int, dict[str, str]] = {}
            for chart in charts:
                if not isinstance(chart, dict):
                    continue
                idx = chart.get("index")
                if idx is not None:
                    chart_map[int(idx)] = {
                        "topLeftCell": chart.get("topLeftCell", ""),
                        "bottomRightCell": chart.get("bottomRightCell", ""),
                    }  # 产品要求图表完全不遮盖
                if verbose:
                    series_meta = [
                        {
                            "index": sd.get("index"),
                            "name": sd.get("name", ""),
                        }
                        for sd in (chart.get("seriesDetails") or [])
                        if isinstance(sd, dict)
                    ]
                    print(
                        "chart: "
                        f"index={chart.get('index', 'N/A')}, "
                        f"name={chart.get('name', 'N/A')}, "
                        f"chartTitle={chart.get('chartTitle', 'N/A')}, "
                        f"topLeftCell={chart.get('topLeftCell', 'N/A')}, "
                        f"bottomRightCell={chart.get('bottomRightCell', 'N/A')}, "
                        f"chartType={chart.get('chartType', 'N/A')}, "
                        f"hasLegend={chart.get('hasLegend', 'N/A')}, "
                        f"axes={chart.get('axes', {})}, "
                        f"seriesCount={chart.get('seriesCount', 'N/A')}, "
                        f"series={series_meta}"
                    )
            self._chart_information = chart_map
            return chart_map

        except Exception as e:
            print(f"获取图表信息异常: {type(e).__name__}: {e}")
            return None
    
    def pivot_table_wizard(self,
                          source_address: str,
                          table_destination: str = '',
                          table_name: str = '',
                          row_grand: bool = True,
                          column_grand: bool = True) -> 'PivotTable':
        """在工作表上创建数据透视表

        Args:
            source_address: 数据源地址（如 "A1:E100"），支持跨表引用（如 "'Sheet1'!A1:E100"）
            table_destination: 透视表放置位置（如 "G1"），留空则自动放置
            table_name: 透视表名称，留空则自动命名
            row_grand: 是否显示行总计，默认 True
            column_grand: 是否显示列总计，默认 True

        Returns:
            PivotTable: 创建后的透视表对象

        Raises:
            Exception: 创建失败

        Example:
            >>> pvt = sheet.pivot_table_wizard("A1:E100", "G1", "销售分析")
            >>> pvt.pivot_field("产品").orientation = "row"
            >>> pvt.add_data_field("金额", caption="金额求和", function="sum")
        """
        self._ctx.flush()
        row_grand = bool(row_grand) if row_grand is not None else True
        column_grand = bool(column_grand) if column_grand is not None else True

        # 数据源地址没有 sheet 前缀时，自动补上当前 sheet 名，
        # 避免 PivotTableWizard 因 Application.Range 解析不到 sheet 而返回 undefined
        if '!' not in source_address:
            source_address = f"'{self.name}'!{source_address}"

        sheet_name_js = json.dumps(self.name, ensure_ascii=False)
        src_js = json.dumps(source_address, ensure_ascii=False)
        dest_js = (
            f'destSheet.Range({json.dumps(table_destination, ensure_ascii=False)})'
            if table_destination else 'undefined'
        )
        name_js = (
            json.dumps(table_name, ensure_ascii=False)
            if table_name else 'undefined'
        )
        rg_js = 'true' if row_grand else 'false'
        cg_js = 'true' if column_grand else 'false'

        script = f'''
let destSheet = Application.Worksheets.Item({sheet_name_js});
let pvt = destSheet.PivotTableWizard(1, Application.Range({src_js}), {dest_js}, {name_js}, {rg_js}, {cg_js});
if (!pvt) return {{ error: "PivotTableWizard returned undefined" }};
let actualSheet = pvt.TableRange2.Worksheet.Name;
return {{ name: pvt.Name, sheet: actualSheet, location: pvt.TableRange2.Cells(1, 1).Address() }};'''

        res = self._ctx.evaluate_script_v2(script.strip())
        if not res.get('success', True):
            hint = f"创建数据透视表失败: {res.get('error', '未知错误')}"
            if table_destination:
                hint += f"，目标位置 {table_destination} 可能已被其他透视表占用，请先删除或选择其他位置"
            raise Exception(hint)
        info = _jsa_result(res)
        if isinstance(info, dict) and "error" in info:
            hint = f"创建数据透视表失败: {info['error']}"
            if table_destination:
                hint += f"，目标位置 {table_destination} 可能已被其他透视表占用，请先删除或选择其他位置"
            raise Exception(hint)
        pvt_name = info.get("name", table_name or "数据透视表1") if isinstance(info, dict) else (table_name or "数据透视表1")
        actual_sheet = info.get("sheet", self.name) if isinstance(info, dict) else self.name
        print(f"创建数据透视表成功: {pvt_name}")
        return PivotTable(self._ctx, actual_sheet, pvt_name)

    def pivot_tables(self) -> list['PivotTable']:
        """获取当前工作表的所有数据透视表

        Returns:
            list[PivotTable]: 透视表列表

        Example:
            >>> for pvt in sheet.pivot_tables():
            ...     print(pvt.name)
        """
        script = f'''
let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
let tables = [];
for (let i = 1; i <= sheet.PivotTables().Count; i++) {{
    let pvt = sheet.PivotTables(i);
    tables.push({{ name: pvt.Name }});
}}
return {{ count: sheet.PivotTables().Count, tables: tables }};'''
        res = self._ctx.evaluate_script_v2(script.strip())
        if not res.get('success', True):
            print(f"获取数据透视表列表失败: {res.get('error', '未知错误')}")
            return []
        info = _jsa_result(res)
        if not isinstance(info, dict):
            return []
        return [
            PivotTable(self._ctx, self.name, t.get("name", ""))
            for t in info.get("tables", [])
            if isinstance(t, dict)
        ]

    def pivot_table(self, name_or_index: 'str | int') -> 'PivotTable':
        """按名称或索引获取单个数据透视表

        Args:
            name_or_index: 透视表名称（str）或索引（int, 从 1 开始）

        Returns:
            PivotTable: 透视表对象

        Raises:
            ValueError: 透视表不存在

        Example:
            >>> pvt = sheet.pivot_table("数据透视表1")
            >>> pvt = sheet.pivot_table(1)
        """
        if isinstance(name_or_index, int):
            key_js = str(name_or_index)
        else:
            key_js = json.dumps(name_or_index, ensure_ascii=False)
        script = f'''
let sheet = Application.Worksheets.Item({json.dumps(self.name, ensure_ascii=False)});
let pvt = sheet.PivotTables({key_js});
return {{ name: pvt.Name }};'''
        res = self._ctx.evaluate_script_v2(script.strip())
        if not res.get('success', True):
            raise ValueError(f"数据透视表 '{name_or_index}' 不存在或获取失败: {res.get('error', '未知错误')}")
        info = _jsa_result(res)
        if not isinstance(info, dict):
            raise ValueError(f"数据透视表 '{name_or_index}' 不存在或获取失败")
        return PivotTable(self._ctx, self.name, info.get("name", ""))

    def insert_chart_is_legality(self, rect_address: str) -> bool:  # 后面还会加上覆盖数据区域判断
        """判断插入图表是否遮盖已有图表"""
        self._chart_information = self.chart_information(verbose=False)
        self._ctx.flush()
        if self._chart_information is None:
            return True

        is_no_overlap = lambda x1, y1, x2, y2, a1, b1, a2, b2: (x2 <= a1) or (x1 >= a2) or (y2 <= b1) or (y1 >= b2)

        ins_row_from, ins_row_to, ins_col_from, ins_col_to = self._parse_range(rect_address)

        for cells in self._chart_information.values():
            top_left = cells.get("topLeftCell", "")
            bottom_right = cells.get("bottomRightCell", "")
            if not top_left or not bottom_right:
                continue
            ch_row_from, ch_row_to, ch_col_from, ch_col_to = self._parse_range(f"{top_left}:{bottom_right}")
            if not is_no_overlap(ins_col_from, ins_row_from, ins_col_to, ins_row_to,
                                 ch_col_from, ch_row_from, ch_col_to, ch_row_to):
                return False

        return True