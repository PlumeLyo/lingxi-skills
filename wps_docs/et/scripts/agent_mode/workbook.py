# 依赖说明（拼接执行时已在命名空间中）：
# - Literal, Optional 等标准库来自 summary.py / _utils.py
# - _Context, _make_setattr_guard, _send_event 来自 _utils.py
# - Sheet 来自 sheet.py

# ============ Workbook ============

class Workbook:
    """工作簿操作入口，用于获取工作表、创建新表。

    Note:
        该类已完成初始化，可通过 `workbook` 直接使用，无需手动创建实例。

    Example:
        # 获取工作表
        sheet = workbook.sheet("Sheet1")

        # 读写数据
        print(sheet.range("A1:B10"))
        # 逐行写入
        sheet.range("A1:B1").value = [["姓名", "年龄"]]
        sheet.range("A2:B2").value = [["张三", 25]]
        # 逐列写入
        sheet.range("C1:C2").value = [["部门"], ["技术"]]

        # 设置格式
        rng = sheet.range("A1:B1")
        rng.format.font.bold = True
        rng.format.fill.color = '#4472C4'
    """
    __setattr__ = _make_setattr_guard(
        frozenset(['_ctx', '_active_sheet']),
        []  # Workbook 没有可写的 property
    )

    def __init__(self, active_sheet: Optional[str] = None):
        self._ctx = _Context(active_sheet)
        self._active_sheet = active_sheet

    def sheets(self) -> list[Sheet]:
        """获取所有工作表。
        
        Returns:
            list[Sheet]: 所有工作表对象列表
        """
        return [Sheet(self._ctx, meta) for meta in self._ctx.get_sheets()]

    def sheet(self, name: str) -> Sheet:
        """根据名称获取工作表。
        
        Args:
            name: 工作表名称
        
        Returns:
            Sheet: 工作表对象
        
        Raises:
            ValueError: 工作表不存在
        """
        meta = self._ctx.get_sheet_by_name(name)
        if meta is None:
            available = ', '.join(s.name for s in self._ctx.get_sheets())
            raise ValueError(f"工作表 '{name}' 不存在，可用的工作表: {available}")
        return Sheet(self._ctx, meta)

    def add_sheet(self,
                  name: str,
                  exists: Literal['override', 'new_name', 'ignore', 'error'] = 'override') -> Sheet:
        """新建工作表。
        
        Args:
            name: 工作表名称
            exists: 同名工作表存在时的处理策略
                - 'override': 删除已有的再创建（默认）
                - 'new_name': 自动使用新名称
                - 'ignore': 返回已有工作表
                - 'error': 抛出 ValueError
        
        Returns:
            Sheet: 工作表对象
        
        Note:
            新增 sheet 时，先判断是否存在空白sheet或同名sheet。
        
        Raises:
            ValueError: exists='error' 且工作表已存在
            XLError: 权限不足
            Exception: API请求执行错误
        """
        existing = self._ctx.get_sheet_by_name(name)

        if existing:
            if exists == 'ignore':
                return Sheet(self._ctx, existing)
            elif exists == 'error':
                raise ValueError(f"工作表 '{name}' 已存在")
            elif exists == 'override':
                self._ctx.execute({
                    "command": "http.et.deleteSheets",
                    "param": {"sheetIds": [existing.id]},
                })
                self._ctx.invalidate_sheets_cache()
            # new_name: 让 API 自动分配新名称

        data = self._ctx.execute({
            "command": "http.et.addSheet",
            "param": {
                "end": True,
                "type": "xlWorksheet",
                "defColWidth": 1335,
                "count": 1,
                "name": name,
            },
        })
        if "detail" not in data:
            raise Exception(f"创建工作表返回值缺少detail字段")
        if "sheetId" not in data['detail']:
            raise Exception(f"创建工作表返回值缺少sheetId字段")

        sheet_id = data['detail']['sheetId']
        self._ctx.invalidate_sheets_cache()
        print(f"创建工作表: {name} 成功")

        meta = self._ctx.get_sheet_by_id(sheet_id)
        return Sheet(self._ctx, meta)

    def rename_sheet(self, old_name: str, new_name: str) -> 'Sheet':
        """重命名工作表。
        
        Args:
            old_name: 原工作表名称
            new_name: 新工作表名称
        
        Returns:
            Sheet: 重命名后的工作表对象
        
        Raises:
            ValueError: 原工作表不存在或新名称已被使用
            XLError: 权限不足
            Exception: API请求执行错误
            
        Example:
            重要：必须使用返回值，原有的 sheet 引用在重命名后会失效。
            # 正确用法
            sheet = workbook.rename_sheet(old_name, new_name)
        """
        # 检查原工作表是否存在
        existing = self._ctx.get_sheet_by_name(old_name)
        if existing is None:
            available = ', '.join(s.name for s in self._ctx.get_sheets())
            raise Exception(f"工作表 '{old_name}' 不存在，可用的工作表: {available}")
        
        # 检查新名称是否已被使用
        if self._ctx.get_sheet_by_name(new_name) is not None:
            raise Exception(f"工作表名称 '{new_name}' 已被使用")
        
        # 执行重命名
        self._ctx.execute({
            "command": "http.et.setSheetName",
            "param": {
                "sheetId": existing.id,
                "name": new_name,
            },
        })

        meta = self._ctx.get_sheet_by_id(existing.id)
        meta.name = new_name
        
        # self._ctx.invalidate_sheets_cache()
        print(f"重命名工作表: '{old_name}' -> '{new_name}' 成功")
        
        # 返回重命名后的工作表对象
        # meta = self._ctx.get_sheet_by_id(existing.id)
        return Sheet(self._ctx, meta)

    def delete_sheet(self, name: str) -> None:
        """删除工作表，该操作不可逆，请谨慎使用。
        
        Args:
            name: 要删除的工作表名称
        
        Raises:
            Exception: API请求执行错误
        """
        # 检查工作表是否存在
        existing = self._ctx.get_sheet_by_name(name)
        if existing is None:
            available = ', '.join(s.name for s in self._ctx.get_sheets())
            raise Exception(f"工作表 '{name}' 不存在，可用的工作表: {available}")
        
        # 执行删除
        self._ctx.execute({
            "command": "http.et.deleteSheets",
            "param": {"sheetIds": [existing.id]},
        })
        
        self._ctx.invalidate_sheets_cache()
        print(f"删除工作表: '{name}' 成功")

    def _flush(self) -> None:
        """内部方法：提交写入/删除操作（由系统自动调用，无需手动调用）"""
        self._ctx.flush()

    def _clear_buffer(self) -> None:
        """内部方法：清空未提交的缓冲区（由系统自动调用，无需手动调用）"""
        self._ctx.clear_buffer()

# ============ 导出的公共接口 ============

__all__ = ['Workbook', 'Sheet', 'PivotTable', 'PivotField', 'PivotItem', 'Range', 'Border', 'Font', 'Fill', 'Format']

# 全局实例由 et.py 的 _init_core 按需创建，此处不自动实例化
