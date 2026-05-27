# 标准库导入
import json
import math
import re
import time as _time_module # 使用原名的话貌似不知道被哪里的植入覆盖了
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, Any, Optional, Union
import builtins as _builtins
import requests

# ============ 辅助函数 ============

_INDEX_NONE = -1
_PX_TO_TWIP = 15


def _make_setattr_guard(allowed_attrs: frozenset, writable_props: list[str]):
    """
    创建 __setattr__ 方法，防止设置不存在的属性。
    
    Args:
        allowed_attrs: 允许设置的属性集合（包括私有属性）
        writable_props: 可写的 property 名称列表（用于错误提示）
    """
    def __setattr__(self, name: str, value: Any):
        if name not in allowed_attrs:
            props_hint = ', '.join(writable_props) if writable_props else '无'
            raise AttributeError(
                f"'{type(self).__name__}' 对象没有属性 '{name}'。"
                f"可设置的属性: {props_hint}"
            )
        object.__setattr__(self, name, value)
    return __setattr__

# 可绑定的 API 调用函数引用（优先于 builtins，用于 et.py 多文件切换）
_core_execute_fn = None
_evaluate_script_fn = None


def _bind_client(core_execute_fn, evaluate_script_fn):
    """绑定自定义的 API 调用函数，替代 builtins 全局注入。

    et.py 在每次切换文件时调用此函数，将 HTTPMockBuiltins 实例方法
    绑定到模块级变量，使后续所有 _call_core_execute / _call_evaluate_script
    调用自动路由到新文件的 API 端点。
    """
    global _core_execute_fn, _evaluate_script_fn
    _core_execute_fn = core_execute_fn
    _evaluate_script_fn = evaluate_script_fn


def _call_core_execute(command: str, param: dict) -> dict:
    param_json = json.dumps(param, ensure_ascii=False)
    fn = _core_execute_fn if _core_execute_fn is not None else _builtins.__core_execute
    result_json = fn(command, param_json)
    return json.loads(result_json)


def _call_evaluate_script(data: dict) -> dict:
    """调用 evaluate_script

    返回值格式: {"success": bool, "error": str, "data": any}
    调用方需要自行判断 success 字段并处理错误
    """
    data_json = json.dumps(data, ensure_ascii=False)
    fn = _evaluate_script_fn if _evaluate_script_fn is not None else _builtins.__evaluate_script
    result_json = fn(data_json)
    return json.loads(result_json)

def _jsa_result(res: dict) -> Any:
    """从 evaluate_script_v2 返回值中提取 data.result 并解析 JSON 字符串。

    Go 侧返回的 data.result 可能是 JSON 字符串，这里统一尝试解析。
    """
    result = res.get("data", {}).get("result")
    if isinstance(result, str):
        try:
            return json.loads(result)
        except (json.JSONDecodeError, ValueError):
            pass
    return result

def _r1c1_to_a1(ref: str) -> str:
    """R1C1 引用转 A1 格式，如 'R1C1:R14C2' -> 'A1:B14'，'R3C5' -> 'E3'。
    含 sheet 前缀（如 '=Sheet1!R1C1:R2C3'）时保留 sheet 名。
    无法识别的格式原样返回。
    """
    sheet_prefix = ""
    body = ref
    if "!" in ref:
        sheet_prefix, body = ref.rsplit("!", 1)
        sheet_prefix += "!"
    parts = body.split(":")
    converted = []
    for p in parts:
        m = re.match(r'^R(\d+)C(\d+)$', p.strip(), re.IGNORECASE)
        if not m:
            return ref
        row, col = int(m.group(1)), int(m.group(2))
        converted.append(f"{_decimal_to_base26(col)}{row}")
    return sheet_prefix + ":".join(converted)

def _base26_to_decimal(col_str: str) -> int:
    """列名转列号，如 'A' -> 1, 'AA' -> 27"""
    col_str = col_str.upper()
    result = 0
    for char in col_str:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result


def _decimal_to_base26(col_num: int) -> str:
    """列号转列名，如 1 -> 'A', 27 -> 'AA'"""
    if col_num <= 0:
        raise ValueError(f"列号必须大于0，当前值: {col_num}")
    result = ""
    while col_num > 0:
        col_num, remainder = divmod(col_num - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _parse_column(column: str) -> int:
    """解析列名为 0-based 索引"""
    if not column:
        return _INDEX_NONE
    return _base26_to_decimal(column) - 1


def _parse_row(row: str) -> int:
    """解析行号为 0-based 索引"""
    if not row:
        return _INDEX_NONE
    try:
        return int(row) - 1
    except ValueError:
        return _INDEX_NONE


def _parse_range(addr: str) -> tuple[int, int, int, int]:
    """
    解析单元格地址

    Returns:
        (row_from, row_to, col_from, col_to) - 0-based 索引
    """
    addr = addr.replace(" ", "")
    if not addr:
        raise ValueError("地址不能为空")
    if addr.startswith(":") or addr.endswith(":"):
        raise ValueError(f"无效的地址格式: {addr}")

    pattern = re.compile(r'^\$?([A-Za-z]*)\$?(\d*)(?::\$?([A-Za-z]*)\$?(\d*))?$')
    match = pattern.match(addr)
    if not match:
        raise ValueError(f"无效的地址格式: {addr}")

    col1, row1, col2, row2 = match.groups()

    col_from = _parse_column(col1)
    row_from = _parse_row(row1)

    if col2 is None and row2 is None:
        # 单个单元格，如 "A1"
        if row_from == _INDEX_NONE or col_from == _INDEX_NONE:
            raise ValueError(f"无效的单元格地址: {addr}")
        return row_from, row_from, col_from, col_from

    # 区域，如 "A1:B10"
    col_to = _parse_column(col2) if col2 else col_from
    row_to = _parse_row(row2) if row2 else row_from

    # 确保 from <= to
    if row_from > row_to:
        row_from, row_to = row_to, row_from
    if col_from > col_to:
        col_from, col_to = col_to, col_from

    return row_from, row_to, col_from, col_to


def _format_address(row_from: int, row_to: int, col_from: int, col_to: int) -> str:
    """格式化为地址字符串，0-based 索引"""
    start = f"{_decimal_to_base26(col_from + 1)}{row_from + 1}"
    if row_from == row_to and col_from == col_to:
        return start
    end = f"{_decimal_to_base26(col_to + 1)}{row_to + 1}"
    return f"{start}:{end}"


def _to_cell_value(v: Any) -> str:
    """将值转换为单元格可接受的字符串"""
    if v is None:
        return ''
    if isinstance(v, float) and math.isnan(v):
        return ''
    while isinstance(v, list) and len(v) > 0:
        v = v[0]
    return str(v)


def _color_to_argb(color: str) -> int:
    """将颜色字符串转换为 ARGB 整数值"""
    if not color.startswith('#'):
        raise ValueError(f"颜色必须以 '#' 开头: {color}")

    hex_part = color[1:]
    if len(hex_part) == 6:
        hex_part = 'ff' + hex_part
    elif len(hex_part) != 8:
        raise ValueError(f"颜色格式无效: {color}")

    try:
        return int(hex_part, 16)
    except ValueError:
        raise ValueError(f"颜色包含无效字符: {color}")


def _style_to_xf(style: dict) -> dict:
    """将用户友好的样式字典转换为 API 格式"""
    xf = {}

    if 'numfmt' in style:
        xf['numfmt'] = style['numfmt']
    if 'wrap' in style:
        xf['wrap'] = style['wrap']

    if 'font' in style:
        font = style['font']
        font_xf = {}
        if 'color' in font:
            font_xf['color'] = {'tint': 0, 'type': 2, 'value': _color_to_argb(font['color'])}
        if 'bold' in font:
            font_xf['bls'] = font['bold']
        if 'name' in font:
            font_xf['name'] = font['name']
        if 'italic' in font:
            font_xf['italic'] = font['italic']
        if 'strikeout' in font:
            font_xf['strikeout'] = font['strikeout']
        if font_xf:
            xf['font'] = font_xf

    if 'fill' in style and 'back' in style['fill']:
        xf['fill'] = {
            'type': 1,
            'back': {'type': 2, 'value': _color_to_argb(style['fill']['back'])}
        }

    # 水平对齐
    if 'h_align' in style:
        h_align = style['h_align']
        if h_align == 'left':
            xf['alcH'] = 1
        elif h_align == 'center':
            xf['alcH'] = 2
        elif h_align == 'right':
            xf['alcH'] = 3

    # 垂直对齐
    if 'v_align' in style:
        v_align = style['v_align']
        if v_align == 'top':
            xf['alcV'] = 0
        elif v_align == 'center':
            xf['alcV'] = 1
        elif v_align == 'bottom':
            xf['alcV'] = 2

    return xf


def _parse_rows_arg(rows: 'int | str | Range', rows_end: int | None = None) -> tuple[int, int]:
    """
    解析行参数，返回 0-based 索引。

    用户输入是 1-based，返回值是 0-based（直接传给 API）。

    支持：
    - 单个整数: 5 -> (4, 4)
    - 两个整数: 5, 10 -> (4, 9)
    - 字符串: "5", "5:10" -> (4, 4), (4, 9)
    - Range 对象: 使用其内部 _row_from, _row_to（0-based）
    """
    # 如果是 Range 对象
    if hasattr(rows, '_row_from'):
        return rows._row_from, rows._row_to

    # 如果提供了第二个整数参数
    if rows_end is not None:
        return int(rows) - 1, int(rows_end) - 1

    # 如果是整数
    if isinstance(rows, int):
        return rows - 1, rows - 1

    # 如果是字符串
    if isinstance(rows, str):
        rows = rows.strip()
        if ':' in rows:
            parts = rows.split(':')
            return int(parts[0]) - 1, int(parts[1]) - 1
        else:
            idx = int(rows) - 1
            return idx, idx

    raise ValueError(f"无效的行参数: {rows}")


def _parse_columns_arg(cols: 'int | str | Range', cols_end: int | None = None) -> tuple[int, int]:
    """
    解析列参数，返回 0-based 索引。

    用户输入是 1-based，返回值是 0-based（直接传给 API）。

    支持：
    - 单个整数: 3 -> (2, 2)
    - 两个整数: 2, 5 -> (1, 4)
    - 字符串: "C", "B:E", "B2:E10" -> (2, 2), (1, 4), (1, 4)
    - Range 对象: 使用其内部 _col_from, _col_to（0-based）
    """
    # 如果是 Range 对象
    if hasattr(cols, '_col_from'):
        return cols._col_from, cols._col_to

    # 如果提供了第二个整数参数
    if cols_end is not None:
        return int(cols) - 1, int(cols_end) - 1

    # 如果是整数
    if isinstance(cols, int):
        return cols - 1, cols - 1

    # 如果是字符串
    if isinstance(cols, str):
        cols = cols.strip()
        if ':' in cols:
            # 支持 "B:E" 或 "B2:E10" 格式
            parts = cols.split(':')
            col1 = re.sub(r'\d+', '', parts[0])  # 去掉数字
            col2 = re.sub(r'\d+', '', parts[1])
            return _base26_to_decimal(col1) - 1, _base26_to_decimal(col2) - 1
        else:
            # 支持 "C" 或 "C5" 格式
            col = re.sub(r'\d+', '', cols)
            idx = _base26_to_decimal(col) - 1
            return idx, idx

    raise ValueError(f"无效的列参数: {cols}")



# ============ 内部上下文 ============

@dataclass
class _SheetMeta:
    """Sheet 元数据"""
    id: int
    idx: int
    name: str
    row_from: int
    row_to: int
    col_from: int
    col_to: int
    is_empty: bool = False


class _Context:
    """
    内部上下文，负责：
    - HTTP 通信
    - 写操作缓冲（减少 API 调用次数）
    - 删除操作队列
    - Sheets 元数据缓存
    """
    # 类级别限流状态：按 key 分组，每个 key 独立限流
    _rate_limit_state: dict[str, list[float]] = {}
    _rate_limit = 8  # 每秒最大请求数

    def __init__(self, active_sheet: Optional[str] = None):
        self._sheets_cache: list[_SheetMeta] | None = None
        self._write_buffer: defaultdict[int, list[dict]] = defaultdict(list)
        self._write_logs_buffer: defaultdict[int, list[str]] = defaultdict(list)
        self._delete_queue: list[dict] = []
        self._delete_logs_buffer: defaultdict[int, list[str]] = defaultdict(list)
        self._script_queue: list[str] = []
        self._script_logs_buffer: list[str] = []  # 记录脚本执行后的日志
        self._script_formula_buffer: defaultdict[int, list[dict]] = defaultdict(list)  # 记录脚本写入的公式位置
        self._script_socket = None
        self._active_sheet = active_sheet
        self._protection_permission: str = self._fetch_protection_permission()

    def _fetch_protection_permission(self) -> str:
        """获取表格保护权限状态

        Returns:
            str: 权限状态，'edit' 表示可编辑，'visible' 表示只读
        """
        try:
            result = _call_core_execute("http.et.getProtectionInfo", {})
            if result.get('result') == 'ok':
                return result.get('detail', {}).get('permission', 'edit')
        except Exception:
            pass
        # 默认返回 'edit'，保持向后兼容
        return 'edit'

    @property
    def can_write_formula(self) -> bool:
        """检查是否可以写入公式（需要 edit 权限）"""
        return self._protection_permission == 'edit'

    @classmethod
    def _wait_for_rate_limit(cls, key: str):
        """等待直到满足限流条件（按 key 分组）"""
        now = _time_module.time()
        current_second = int(now)
        
        # 初始化 key 的时间戳列表
        if key not in cls._rate_limit_state:
            cls._rate_limit_state[key] = []
        
        # 清理上一秒之前的时间戳
        cls._rate_limit_state[key] = [
            ts for ts in cls._rate_limit_state[key] 
            if int(ts) == current_second
        ]
        
        # 如果当前秒内已有最大请求数，等待到下一秒
        if len(cls._rate_limit_state[key]) >= cls._rate_limit:
            offset = 0.1
            sleep_time = 1.0 - (now - current_second)
            if sleep_time > 0:
                _time_module.sleep(sleep_time + offset)
            # 清空时间戳（已进入新的一秒）
            cls._rate_limit_state[key] = []
        
        # 记录本次请求时间
        cls._rate_limit_state[key].append(_time_module.time())

    def execute(self, body: dict) -> dict:
        """执行 API 请求"""
        command = body.get('command', '')
        param = body.get('param', {})
        return _call_core_execute(command, param)

    def evaluate_script(self, script: str) -> Any:
        """执行 JS 脚本（旧版本，通过 core/execute）"""
        self.flush()
        res = self.execute({
            "command": "http.et.v8JsEvaluate",
            "param": {"jsStr": script},
        })
        detail = res['detail']
        if not detail.get('result', True):
            raise Exception(f"脚本执行失败: {detail.get('response', 'unknown error')}")
        return detail.get('response')

    def evaluate_script_v2(self, script: str, _skip_flush: bool = False) -> Any:
        """执行 JS 脚本（新版本，通过 script 端点）"""
        if not _skip_flush:
            self.flush()
        self._wait_for_rate_limit('script')
        data = {
            "script": script,
            'script_name': 'script',
            'Context': {},
        }
        return _call_evaluate_script(data)

    def get_sheets(self, refresh: bool = False) -> list[_SheetMeta]:
        """获取所有 sheet 元数据"""
        if self._sheets_cache is None or refresh:
            self._wait_for_rate_limit('get_sheets')
            data = self.execute({
                "command": "http.et.getSheetsInfo",
                "param": {},
            })
            self._sheets_cache = [
                _SheetMeta(
                    id=s['sheetId'],
                    idx=s['sheetIdx'],
                    name=s['sheetName'],
                    row_from=s['rowFrom'],
                    row_to=s['rowTo'],
                    col_from=s['colFrom'],
                    col_to=s['colTo'],
                    is_empty=s['isEmpty'],
                )
                for s in data['detail']['sheetsInfo']
                # 只保留普通表格类型
                if s.get('sheetType', 'et') == 'et'
            ]
        return self._sheets_cache

    def queue_script(self, script: str, formula_info: dict | None = None, log_message: str | None = None) -> None:
        """将脚本加入队列，等待 flush 时执行

        Args:
            script: JS 脚本代码
            formula_info: 公式位置信息，格式为 {'sheet_id': int, 'operations': [{'rowFrom', 'rowTo', 'colFrom', 'colTo', 'formula'}]}
            log_message: 脚本执行后打印的日志消息
        """
        self._script_queue.append(script)
        if formula_info:
            sheet_id = formula_info['sheet_id']
            self._script_formula_buffer[sheet_id].extend(formula_info['operations'])
        if log_message:
            self._script_logs_buffer.append(log_message)

    def _flush_script(self) -> Any:
        """执行队列中的所有脚本，将它们拼接在一起一次性执行，并获取公式计算结果"""
        if not self._script_queue:
            return None

        for sheet_id, operations in self._script_formula_buffer.items():
            if self._has_data_in_write_area(sheet_id, operations):
                raise Exception("写入操作被终止：目标区域已存在数据,如果需要修改值或者设置新公式，需要先删除已有数据，再重新写入，注意非用户需求不得修改用户原始数据,删除前确保选择区域正确")

        try:
            # 将所有脚本用大括号 + 换行包裹并拼接。
            # 注意：如果 script 末尾包含 `//` 行注释，没有换行会把后续拼接内容吞掉导致语法错误。
            combined_script = ''.join(f'{{\n{script}\n}}\n' for script in self._script_queue)
            result = self.evaluate_script_v2(combined_script, _skip_flush=True)

            # 检查脚本执行结果
            if not result.get('success', True):
                error_msg = result.get('error', '未知错误')
                print(f"脚本执行失败: {error_msg}")
                return result

            # 打印脚本执行日志
            for log in self._script_logs_buffer:
                print(log)

            # 获取公式计算结果
            self._print_script_formula_results()

            return result
        except Exception as e:
            raise Exception(f"脚本执行失败: {e}")
        finally:
            self._clear_script_queue()

    def _print_script_formula_results(self) -> None:
        """打印脚本写入的公式计算结果"""
        if not self._script_formula_buffer:
            return

        print('公式写入后计算出的值:')
        for sheet_id, operations in self._script_formula_buffer.items():
            if not operations:
                continue

            # 计算需要读取的范围
            range_info = {
                'rowFrom': operations[0]['rowFrom'],
                'rowTo': operations[0]['rowTo'],
                'colFrom': operations[0]['colFrom'],
                'colTo': operations[0]['colTo'],
            }
            for op in operations:
                range_info['rowFrom'] = min(range_info['rowFrom'], op['rowFrom'])
                range_info['rowTo'] = max(range_info['rowTo'], op['rowTo'])
                range_info['colFrom'] = min(range_info['colFrom'], op['colFrom'])
                range_info['colTo'] = max(range_info['colTo'], op['colTo'])

            try:
                resp = self.execute({
                    'command': 'http.et.getRangeData',
                    'param': {
                        'sheetId': sheet_id,
                        'range': range_info,
                    },
                })
                range_data = resp['detail']['rangeData']
                if range_data is None:
                    range_data = []

                cell_map = {}
                for cell in range_data:
                    key = (cell['rowFrom'], cell['colFrom'])
                    cell_map[key] = cell.get('cellText', '')

                for op in operations:
                    address = _format_address(op['rowFrom'], op['rowTo'], op['colFrom'], op['colTo'])
                    texts = []
                    for row in range(op['rowFrom'], op['rowTo'] + 1):
                        for col in range(op['colFrom'], op['colTo'] + 1):
                            texts.append(cell_map.get((row, col), ''))

                    has_error = any(t in ['#N/A', '#VALUE!', '#DIV/0!', '#REF!', '#NAME?', '#NUM!', '#NULL!'] for t in texts)
                    if has_error:
                        print(f"[{address}] [有错误!] `{op['formula']}`: {texts}")
                    else:
                        print(f"[{address}] `{op['formula']}`: {texts}")
            except:
                pass

    def _clear_script_queue(self) -> None:
        """清空脚本队列"""
        self._script_queue.clear()
        self._script_logs_buffer.clear()
        self._script_formula_buffer.clear()

    def get_sheet_by_name(self, name: str) -> _SheetMeta | None:
        """根据名称获取 sheet 元数据"""
        for s in self.get_sheets():
            if s.name == name:
                return s
        return None

    def get_sheet_by_id(self, sheet_id: int) -> _SheetMeta | None:
        """根据 ID 获取 sheet 元数据"""
        for s in self.get_sheets():
            if s.id == sheet_id:
                return s
        return None

    def invalidate_sheets_cache(self):
        """使 sheets 缓存失效"""
        self._sheets_cache = None

    def buffer_write(self, sheet_id: int, operations: list[dict], log: str):
        """将写操作加入缓冲区"""
        self._flush_delete()
        if sheet_id not in self._write_buffer:
            self._write_buffer[sheet_id] = []
        self._write_buffer[sheet_id].extend(operations)
        if sheet_id not in self._write_logs_buffer:
            self._write_logs_buffer[sheet_id] = []
        self._write_logs_buffer[sheet_id].append(log)

    def queue_delete(self, sheet_id: int, row_from: int, row_to: int, col_from: int, col_to: int, shift: str, log: str):
        """将删除操作加入队列"""
        self._flush_write()
        self._delete_queue.append({
            'sheet_id': sheet_id,
            'row_from': row_from,
            'row_to': row_to,
            'col_from': col_from,
            'col_to': col_to,
            'shift': shift,
        })
        self._delete_logs_buffer[sheet_id].append(log)

    def _has_data_in_write_area(self, sheet_id: int, operations: list[dict]) -> bool:
        """检查写入区域是否与已有数据重叠。
        """
        sht = self.get_sheet_by_id(sheet_id)
        if sht is None or sht.is_empty:
            return False

        data_ops = [op for op in operations if op.get('opType') not in ('format', 'merge')]
        if not data_ops:
            return False

        write_row_from = min(op['rowFrom'] for op in data_ops)
        write_row_to = max(op['rowTo'] for op in data_ops)
        write_col_from = min(op['colFrom'] for op in data_ops)
        write_col_to = max(op['colTo'] for op in data_ops)

        if not (write_row_from <= sht.row_to and write_row_to >= sht.row_from and
                write_col_from <= sht.col_to and write_col_to >= sht.col_from):
            return False

        try:
            self._wait_for_rate_limit('read_range')
            data = self.execute({
                "command": "http.et.getRangeData",
                "param": {
                    "sheetId": sheet_id,
                    "range": {
                        "rowFrom": max(write_row_from, sht.row_from),
                        "rowTo": min(write_row_to, sht.row_to),
                        "colFrom": max(write_col_from, sht.col_from),
                        "colTo": min(write_col_to, sht.col_to),
                    },
                },
            })
            range_data = data['detail'].get('rangeData', [])
            if not range_data:
                return False

            write_cells = {(op['rowFrom'], op['colFrom']) for op in data_ops} #我这里只取操作的区域，不是上面getRange拿到的区域,理论上是正确的
            return any(
                (cell['rowFrom'], cell['colFrom']) in write_cells
                for cell in range_data
            )
        except Exception:
            return True

    def _flush_write(self):
        for sheet_id, operations in self._write_buffer.items():
            if self._has_data_in_write_area(sheet_id, operations):
                raise Exception("写入操作被终止：目标区域已存在数据,如果需要修改值或者设置新公式，需要先删除已有数据，再重新写入，注意非用户需求不得修改用户原始数据,删除前确保选择区域正确")

        formula_operations = []
        for sheet_id, operations in self._write_buffer.items():
            sht = self.get_sheet_by_id(sheet_id)
            if sht is None:
                continue
            if not operations:
                continue
            self._wait_for_rate_limit('write')
            self.execute({
                "command": "http.et.updateRangeData",
                "param": {
                    "sheetId": sheet_id,
                    "rangeData": operations,
                },
            })
            for log in self._write_logs_buffer[sheet_id]:
                print(log)
            # 收集公式操作
            formula_operations.extend([
                (sheet_id, op) for op in operations
                if op.get('opType', '') == 'formula'
                and op.get('formula', '').strip().startswith('=')
            ])
        # 输出公式写入后计算出的值，遇错不中断
        if len(formula_operations) > 0:
            print('公式写入后计算出的值:')
            # 按 sheet_id 分组，并计算每个 sheet 的范围边界
            sheet_ranges = {}
            for sheet_id, op in formula_operations:
                if sheet_id not in sheet_ranges:
                    sheet_ranges[sheet_id] = {
                        'rowFrom': op['rowFrom'],
                        'rowTo': op['rowTo'],
                        'colFrom': op['colFrom'],
                        'colTo': op['colTo'],
                        'operations': []
                    }
                sheet_ranges[sheet_id]['rowFrom'] = min(sheet_ranges[sheet_id]['rowFrom'], op['rowFrom'])
                sheet_ranges[sheet_id]['rowTo'] = max(sheet_ranges[sheet_id]['rowTo'], op['rowTo'])
                sheet_ranges[sheet_id]['colFrom'] = min(sheet_ranges[sheet_id]['colFrom'], op['colFrom'])
                sheet_ranges[sheet_id]['colTo'] = max(sheet_ranges[sheet_id]['colTo'], op['colTo'])
                sheet_ranges[sheet_id]['operations'].append(op)
            
            # 对每个 sheet 只请求一次数据
            for sheet_id, range_info in sheet_ranges.items():
                try:
                    resp = self.execute({
                        'command': 'http.et.getRangeData',
                        'param': {
                            'sheetId': sheet_id,
                            'range': {
                                'rowFrom': range_info['rowFrom'],
                                'rowTo': range_info['rowTo'],
                                'colFrom': range_info['colFrom'],
                                'colTo': range_info['colTo'],
                            },
                        },
                    })
                    range_data = resp['detail']['rangeData']
                    if range_data is None:
                        range_data = []
                    
                    # 构建位置到单元格数据的映射
                    cell_map = {}
                    for cell in range_data:
                        key = (cell['rowFrom'], cell['colFrom'])
                        cell_map[key] = cell.get('cellText', '')
                    
                    # 对每个公式操作，从缓存的数据中提取对应的值
                    for op in range_info['operations']:
                        address = _format_address(op['rowFrom'], op['rowTo'], op['colFrom'], op['colTo'])
                        texts = []
                        for row in range(op['rowFrom'], op['rowTo'] + 1):
                            for col in range(op['colFrom'], op['colTo'] + 1):
                                texts.append(cell_map.get((row, col), ''))
                        
                        has_error = any(t in ['#N/A', '#VALUE!', '#DIV/0!', '#REF!', '#NAME?', '#NUM!', '#NULL!'] for t in texts)
                        if has_error:
                            print(f"[{address}] [有错误!] `{op['formula']}`: {texts}")
                        else:
                            print(f"[{address}] `{op['formula']}`: {texts}")
                except:
                    pass
        # 清空写入缓冲区
        self._clear_write_buffer()

    def _clear_write_buffer(self):
        self._write_buffer.clear()
        self._write_logs_buffer.clear()

    def _clear_delete_buffer(self):
        self._delete_queue.clear()
        self._delete_logs_buffer.clear()

    def clear_buffer(self):
        self._clear_write_buffer()
        self._clear_delete_buffer()
        self._clear_script_queue()

    def _flush_delete(self):
        if len(self._delete_queue) == 0:
            return
        self._wait_for_rate_limit('delete')
        delete_groups: dict[tuple[int, str], list[dict]] = {}
        for op in self._delete_queue:
            sht = self.get_sheet_by_id(op['sheet_id'])
            if sht is None:
                continue
            key = (op['sheet_id'], op['shift'])
            if key not in delete_groups:
                delete_groups[key] = []
            delete_groups[key].append({
                'rowFrom': op['row_from'],
                'rowTo': op['row_to'],
                'colFrom': op['col_from'],
                'colTo': op['col_to'],
            })

        for (sheet_id, shift), ranges in delete_groups.items():
            self.execute({
                "command": "http.et.deleteRange",
                "param": {
                    "sheetId": sheet_id,
                    "rangeData": ranges,
                    "type": shift,
                },
            })

        # 打印删除日志
        for sheet_id, logs in self._delete_logs_buffer.items():
            sht = self.get_sheet_by_id(sheet_id)
            if sht is None:
                continue
            for log in logs:
                print(log)

        self._clear_delete_buffer()

    def flush(self):
        """提交所有缓冲的操作"""
        # 提交写操作
        self._flush_write()

        # 执行脚本（公式写入）
        self._flush_script()

        # 再提交删除操作（按 sheet 和 shift 类型分组）
        self._flush_delete()

    def read_range(self, sheet_id: int, row_from: int, row_to: int, col_from: int, col_to: int) -> list[dict]:
        """读取区域数据（读取前先 flush 以确保数据一致性）"""
        self.flush()
        self._wait_for_rate_limit('read_range')
        num_cells = (row_to - row_from + 1) * (col_to - col_from + 1)
        if num_cells > 1_000_000:
            raise ValueError("所选区域格子数量超过100万个，操作被拒绝")
        data = self.execute({
            "command": "http.et.getRangeData",
            "param": {
                "sheetId": sheet_id,
                "range": {
                    "rowFrom": row_from,
                    "rowTo": row_to,
                    "colFrom": col_from,
                    "colTo": col_to,
                },
            },
        })
        return data['detail'].get('rangeData', [])
