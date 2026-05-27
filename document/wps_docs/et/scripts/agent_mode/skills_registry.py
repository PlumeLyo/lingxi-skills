# 依赖说明（拼接执行时已在命名空间中）：
# - inspect, Dict, List, Optional, Any, Template, dataclass 来自 summary.py / _utils.py
# - Workbook, Sheet, Range, Format, Font, Fill, Border 来自之前加载的文件

import inspect
from typing import Dict, List, Optional, Any
from jinja2 import Template
from dataclasses import dataclass


# 类的显示顺序（按调用层级排列）
SKILL_ORDER = ['Workbook', 'Sheet', 'PivotTable', 'PivotField', 'PivotItem', 'Range', 'Format', 'Font', 'Fill', 'Border']

# pydoc 中隐藏的方法（系统自动调用，不暴露给模型）
_HIDDEN_METHODS = frozenset()

# pydoc 中隐藏的冗余别名属性
_HIDDEN_PROPERTIES = frozenset(['typed_values'])

# 复杂方法判断阈值（达到则标记为复杂，需查 ReadGuideline）
COMPLEX_PARAM_COUNT = 3      # 参数数量阈值（>=3 视为复杂）
COMPLEX_SIGNATURE_LEN = 50   # 签名长度阈值



@dataclass
class SkillInfo:
    """技能信息"""
    name: str                    # 类名
    cls: type                    # 类对象
    class_doc: Optional[str]     # 类文档（__doc__ 第一行作为简短描述）
    methods: List[Dict[str, Any]]  # 方法列表
    properties: List[Dict[str, Any]]  # 属性列表（@property 装饰的）
    access_hint: Optional[str] = None  # 获取方式提示


class SkillsRegistry:
    """技能注册表 - 扫描并管理所有可用技能"""
    
    _instance = None
    _skills: Dict[str, SkillInfo] = {}
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._loaded:
            self._scan_skills()
            SkillsRegistry._loaded = True
    
    def _scan_skills(self):
        """扫描并加载所有技能类"""
        # 第一步：扫描所有类并注册（只注册类名和类对象）
        classes_to_process = [Workbook, Sheet, PivotTable, PivotField, PivotItem, Range, Format, Font, Fill, Border]
        for cls in classes_to_process:
            # 保存完整的 __doc__
            self._skills[cls.__name__] = SkillInfo(
                name=cls.__name__,
                cls=cls,
                class_doc=cls.__doc__,
                methods=[],
                properties=[],
                access_hint=None
            )
        
        # 第二步：处理每个类的方法和属性
        for attr in classes_to_process:
            # 收集方法和属性信息
            methods = []
            properties = []
            
            for name in dir(attr):
                if name.startswith('_') or name in _HIDDEN_METHODS or name in _HIDDEN_PROPERTIES:
                    continue
                
                # 获取类上的原始属性（用于检测 property）
                class_attr = getattr(attr, name, None)
                
                # 检查是否是 property（非下划线开头的属性默认全部暴露）
                if isinstance(class_attr, property):
                    
                    # 获取返回类型注解
                    return_type = ""
                    if class_attr.fget:
                        hints = getattr(class_attr.fget, '__annotations__', {})
                        if 'return' in hints:
                            return_annotation = hints['return']
                            # 对于泛型类型（如 list[Sheet]），直接使用字符串表示
                            # 检查是否是泛型类型：有 __origin__ 属性或字符串表示包含 '['
                            if hasattr(return_annotation, '__origin__') or (hasattr(return_annotation, '__args__') and return_annotation.__args__):
                                return_type = self._simplify_type_string(str(return_annotation))
                            elif hasattr(return_annotation, '__name__'):
                                class_name = return_annotation.__name__
                                # 检查是否是已注册的技能类
                                if class_name in self._skills:
                                    return_type = f"{class_name}"
                                else:
                                    return_type = class_name
                            else:
                                return_type = self._simplify_type_string(str(return_annotation))
                    
                    # 判断属性的读写模式（通过 docstring 标记）
                    # - 只读：有 getter，无 setter
                    # - 只写：docstring 以 [只写] 开头
                    # - 读写：有 getter，有 setter，非只写标记
                    doc = class_attr.fget.__doc__ if class_attr.fget else ""
                    short_desc = self._get_first_line(doc)
                    
                    if class_attr.fset is None:
                        rw_mode = 'readonly'
                    elif doc and doc.strip().startswith('[只写]'):
                        rw_mode = 'writeonly'
                        # 去掉 [只写] 前缀
                        short_desc = short_desc[4:].strip() if short_desc.startswith('[只写]') else short_desc
                    else:
                        rw_mode = 'readwrite'
                    
                    properties.append({
                        'name': name,
                        'return_type': return_type,
                        'doc': doc,
                        'short_desc': short_desc,
                        'rw_mode': rw_mode
                    })
                elif callable(class_attr):
                    try:
                        sig = inspect.signature(class_attr)
                        # 提取返回值类型
                        return_type = ""
                        if sig.return_annotation != inspect.Signature.empty:
                            return_annotation = sig.return_annotation
                            # 对于泛型类型（如 list[Sheet]），直接使用字符串表示
                            # 检查是否是泛型类型：有 __origin__ 属性或字符串表示包含 '['
                            if hasattr(return_annotation, '__origin__') or (hasattr(return_annotation, '__args__') and return_annotation.__args__):
                                return_type = self._simplify_type_string(str(return_annotation))
                            elif hasattr(return_annotation, '__name__'):
                                class_name = return_annotation.__name__
                                # 检查是否是已注册的技能类
                                if class_name in self._skills:
                                    return_type = f"{class_name}"
                                else:
                                    return_type = class_name
                            else:
                                return_type = self._simplify_type_string(str(return_annotation))
                        # 只保留参数部分，移除返回值类型（避免重复）
                        sig_str = str(sig)
                        # 移除 -> 及其后面的返回值类型
                        if ' -> ' in sig_str:
                            sig_str = sig_str.split(' -> ')[0]
                        # 过滤 self 参数
                        sig_str = sig_str.replace('(self, ', '(').replace('(self)', '()')
                    except (ValueError, TypeError):
                        sig_str = "()"
                        return_type = ""
                    methods.append({
                        'name': name,
                        'signature': sig_str,
                        'return_type': return_type,
                        'doc': class_attr.__doc__,
                        'short_desc': self._get_first_line(class_attr.__doc__)
                    })
            
            # 更新已注册的技能信息
            self._skills[attr.__name__].methods = methods
            self._skills[attr.__name__].properties = properties
    
    @staticmethod
    def _get_first_line(doc: Optional[str]) -> str:
        """提取文档的第一行"""
        if not doc:
            return ""
        return doc.strip().split('\n')[0].strip()
    
    @staticmethod
    def _extract_access_hint(doc: Optional[str]) -> Optional[str]:
        """从类文档中提取获取方式提示（从 Note 部分提取）"""
        if not doc:
            return None
        import re
        # 匹配 Note: 后面的内容，提取获取方式
        # 模式1: 预加载名称: `xxx`
        match = re.search(r'预加载名称:\s*`(\w+)`', doc)
        if match:
            return f"预加载: {match.group(1)}"
        # 模式2: 通过 `xxx` 获取实例
        match = re.search(r'通过\s*`([^`]+)`\s*获取', doc)
        if match:
            return f"获取: {match.group(1)}"
        # 模式3: 可通过 `xxx` 直接使用
        match = re.search(r'可通过\s*`(\w+)`\s*直接使用', doc)
        if match:
            return f"预加载: {match.group(1)}"
        # 模式4: 通过 `xxx = Xxx(...)` 设置
        match = re.search(r'通过\s*`([^`]+\s*=\s*\w+\([^)]*\))`', doc)
        if match:
            return f"设置: {match.group(1)}"
        return None
    
    def _simplify_type_string(self, type_str: str) -> str:
        """简化类型字符串，将完整模块路径的类名简化为类名，并标识已注册的技能类"""
        import re
        # 匹配模式：模块路径.类名，例如 src.tools.api.sheet.Sheet
        # 替换为只保留最后的类名，如果是已注册的技能类则添加标识
        # 匹配一个或多个模块名.类名的模式，类名以大写字母开头
        pattern = r'([a-zA-Z_][a-zA-Z0-9_]*\.)+([A-Z][a-zA-Z0-9_]*)'
        def replace_func(match):
            class_name = match.group(2)  # 类名部分
            # 检查是否是已注册的技能类
            if class_name in self._skills:
                return f"{class_name}"
            return class_name
        result = re.sub(pattern, replace_func, type_str)
        return result
    
    def reload(self):
        """重新加载技能"""
        self._skills.clear()
        SkillsRegistry._loaded = False
        self._scan_skills()
        SkillsRegistry._loaded = True
    
    def get_skill(self, name: str) -> Optional[SkillInfo]:
        """获取指定技能"""
        return self._skills.get(name)
    
    def get_all_skills(self) -> Dict[str, SkillInfo]:
        """获取所有技能"""
        return self._skills
    
    def _get_sorted_skills(self) -> List[SkillInfo]:
        """按调用层级排序获取技能列表"""
        sorted_skills = []
        for name in SKILL_ORDER:
            if name in self._skills:
                sorted_skills.append(self._skills[name])
        # 添加不在排序列表中的类
        for skill in self._skills.values():
            if skill not in sorted_skills:
                sorted_skills.append(skill)
        return sorted_skills
    
    def generate_outline(self) -> str:
        """生成技能大纲（简洁版，只显示第一行描述，用于 system prompt）"""
        outline = ""
        
        for skill in self._get_sorted_skills():
            # 添加获取方式提示
            access_hint = "【{}】".format(skill.access_hint) if skill.access_hint else ""
            class_doc = skill.class_doc or ""
            # 检查类描述是否以 [需查询] 开头
            first_line = self._get_first_line(class_doc)
            if first_line.startswith('[需查询]'):
                first_line = first_line[5:]  # 去掉前缀
                outline += "- [需查询] {}: {}{}\n".format(skill.name, first_line, access_hint)
            else:
                outline += "- {}: {}{}\n".format(skill.name, first_line, access_hint)
            if skill.properties:
                outline += "  属性:\n"
                for p in skill.properties:
                    rw_mode = p.get('rw_mode', 'readonly')
                    rw_mark = {'readonly': '(只读)', 'writeonly': '(只写)', 'readwrite': '(读写)'}[rw_mode]
                    type_hint = " -> {}".format(p['return_type']) if p['return_type'] else ""
                    desc = p['short_desc']
                    # 属性有描述时显示描述，无描述时只显示读写标记
                    if desc:
                        outline += "    * {}{}: {}{}\n".format(p['name'], type_hint, desc, rw_mark)
                    else:
                        outline += "    * {}{}{}\n".format(p['name'], type_hint, rw_mark)
            if skill.methods:
                outline += "  方法:\n"
                for m in skill.methods:
                    return_type_hint = " -> {}".format(m['return_type']) if m['return_type'] else ""
                    # 自动判断复杂度：参数数量或签名长度达到阈值
                    sig = m.get('signature', '()')
                    param_count = sig.count(',') + 1 if sig not in ('()', ) else 0
                    is_complex = param_count >= COMPLEX_PARAM_COUNT or len(sig) > COMPLEX_SIGNATURE_LEN
                    if is_complex:
                        # [需查询] 放在前面更醒目
                        outline += "    * [需查询] {}(...){}: {}\n".format(m['name'], return_type_hint, m['short_desc'])
                    else:
                        outline += "    * {}{}{}: {}\n".format(m['name'], sig, return_type_hint, m['short_desc'])
        return outline
    
    @staticmethod
    def _dedent_doc(doc: str) -> str:
        """去除 docstring 的公共缩进前缀"""
        if not doc:
            return ""
        return inspect.cleandoc(doc)

    @staticmethod
    def _format_method_signature(name: str, sig: str, return_type_hint: str, max_len: int = 80) -> List[str]:
        """格式化方法签名，超长时自动折行"""
        one_line = "    def {}{}{}:".format(name, sig, return_type_hint)
        if len(one_line) <= max_len:
            return [one_line]
        params_str = sig[1:-1]
        params = [p.strip() for p in params_str.split(',')]
        result = ["    def {}(".format(name)]
        for i, p in enumerate(params):
            suffix = "," if i < len(params) - 1 else ""
            result.append("        {}{}".format(p, suffix))
        result.append("    ){}:".format(return_type_hint))
        return result

    def generate_full_outline(self, skill_names: Optional[List[str]] = None) -> str:
        lines = []
        
        # 过滤指定的类
        skills = self._get_sorted_skills()
        if skill_names:
            skills = [s for s in skills if s.name in skill_names]
        
        for skill in skills:
            # 类定义
            lines.append("class {}:".format(skill.name))
            
            # 类文档
            class_doc = self._dedent_doc(skill.class_doc or "")
            if class_doc:
                lines.append('    """')
                for line in class_doc.split('\n'):
                    lines.append("    {}".format(line.rstrip()))
                lines.append('    """')
            lines.append("")
            
            # 属性
            for p in skill.properties:
                rw_mode = p.get('rw_mode', 'readonly')
                rw_comment = {'readonly': '  # 只读', 'writeonly': '  # 只写', 'readwrite': ''}[rw_mode]
                type_hint = " -> {}".format(p['return_type']) if p['return_type'] else ""
                lines.append("    @property")
                lines.append("    def {}(self){}:{}".format(p['name'], type_hint, rw_comment))
                
                prop_doc = self._dedent_doc(p.get('doc', '') or '')
                if prop_doc:
                    lines.append('        """')
                    for line in prop_doc.split('\n'):
                        lines.append("        {}".format(line.rstrip()))
                    lines.append('        """')
                lines.append("")
            
            # 方法
            for m in skill.methods:
                return_type_hint = " -> {}".format(m['return_type']) if m['return_type'] else ""
                sig = m.get('signature', '()')
                lines.extend(self._format_method_signature(m['name'], sig, return_type_hint))
                
                method_doc = self._dedent_doc(m.get('doc', '') or '')
                if method_doc:
                    lines.append('        """')
                    for line in method_doc.split('\n'):
                        lines.append("        {}".format(line.rstrip()))
                    lines.append('        """')
                lines.append("")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_full_signature(self, skill_name: str, method_filter: Optional[List[str]] = None) -> str:
        """生成技能的完整签名（用于 ReadGuideline）"""
        skill = self._skills.get(skill_name)
        if not skill:
            return "技能 {} 不存在".format(skill_name)
        
        methods = skill.methods
        properties = skill.properties
        if method_filter:
            methods = [m for m in methods if m['name'] in method_filter]
            properties = [p for p in properties if p['name'] in method_filter]
        
        return Template('''### {{name}}:
#### 类描述：
{{class_description}}
{% if properties -%}
#### 属性：
{%- for prop in properties %}
    @property
    def {{prop.name}}(self) -> {{prop.return_type or 'Any'}}:
        """{{prop.doc}}{% if prop.readonly %}（只读）{% endif %}"""
{% endfor -%}
{% endif -%}
#### 方法说明：
{%- for method in methods %}
    def {{method.name}}{{method.signature}}{% if method.return_type %} -> {{method.return_type}}{% endif %}:
        """{{method.doc}}"""
{% endfor -%}''').render(
            name=skill.name,
            class_description=skill.cls.__doc__,
            methods=methods,
            properties=properties
        )
    
    def generate_api_signature(self, num_start: int = 1) -> str:
        """生成 API 签名（用于原 API 模式的 system prompt）"""
        signature = ""
        num = num_start
        for skill in self._skills.values():
            signature += Template('''### 7.{{num}} {{name}}:
#### 类描述：
{{class_description}}
{% if properties -%}
#### 属性：
{%- for prop in properties %}
    @property
    def {{prop.name}}(self) -> {{prop.return_type or 'Any'}}:
        """{{prop.doc}}{% if prop.readonly %}（只读）{% endif %}"""
{% endfor -%}
{% endif -%}
#### 方法说明：
{%- for method in methods %}
    def {{method.name}}{{method.signature}}{% if method.return_type %} -> {{method.return_type}}{% endif %}:
        """{{method.doc}}"""
{% endfor -%}''').render(
                num=num,
                name=skill.name,
                class_description=skill.cls.__doc__,
                methods=skill.methods,
                properties=skill.properties
            )
            num += 1
        return signature


# 全局单例实例
_registry: Optional[SkillsRegistry] = None


def get_registry() -> SkillsRegistry:
    """获取技能注册表单例"""
    global _registry
    if _registry is None:
        _registry = SkillsRegistry()
    return _registry
