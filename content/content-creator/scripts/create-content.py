#!/usr/bin/env python3
"""
基于写作模板创作新内容
使用: python create-content.py --template template.json --topic "主题" [--materials 资料路径] [--output 输出路径]
"""

import argparse
import json
from pathlib import Path
from datetime import datetime


def load_template(template_path):
    """加载模板文件"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_outline(template, topic):
    """基于模板生成大纲"""
    structure_type = template.get('thinking', {}).get('structure_pattern', '线性论述')
    bookends = template.get('bookends', {})

    outline = f"""# {topic}

## 文章大纲

**结构类型**: {structure_type}
**创作时间**: {datetime.now().strftime("%Y-%m-%d")}

"""

    # 根据结构类型生成不同大纲
    if structure_type == "多层推演":
        outline += """
### 开头（Hook）
- 【套路】{opening}
- 引入话题，制造共鸣或好奇心

### 第一层：现象/案例
- 描述具体案例或现象
- 建立共识基础

### 第二层：初步洞察
- 从现象中提炼观点
- 提出初步结论

### 第三层：自我质疑
- 【使用模板中的质疑句式】
- 转折，提出问题

### 第四层：深层推演
- 深入分析
- 揭示本质

### 结尾
- 【套路】{closing}
- 收束观点或开放思考
""".format(opening=bookends.get('opening', '场景引入'), closing=bookends.get('closing', '观点收束'))

    elif structure_type == "对比验证":
        outline += """
### 开头（Hook）
- 【套路】{opening}
- 提出背景或问题

### 现状分析
- 描述当前情况
- Before 状态

### 对比对象
- 引入对比案例/方案
- After 状态

### 核心差异
- 对比分析
- 关键差异点

### 结论
- 【套路】{closing}
- 洞察或建议
""".format(opening=bookends.get('opening', '场景引入'), closing=bookends.get('closing', '观点收束'))

    else:  # 线性论述
        outline += """
### 开头（Hook）
- 【套路】{opening}
- 引入话题

### 主体部分
- 论点一
- 论点二
- 案例支撑

### 深入分析
- 进一步论证
- 独特洞察

### 结尾
- 【套路】{closing}
- 总结或开放思考
""".format(opening=bookends.get('opening', '场景引入'), closing=bookends.get('closing', '观点收束'))

    # 添加风格提示
    language = template.get('language', {})
    if language.get('unique_patterns'):
        outline += "\n\n### 风格提示\n"
        for pattern in language.get('unique_patterns', [])[:3]:
            outline += f"- 复用表达: {pattern}\n"

    return outline


def generate_writing_guide(template, topic):
    """生成写作指导"""
    language = template.get('language', {})
    thinking = template.get('thinking', {})

    guide = f"""# 创作指导: {topic}

## 语言风格要求

"""

    # 句子风格
    sent_pref = language.get('sentence_preference', 'medium')
    sent_avg = language.get('sentence_avg_length', 25)

    if sent_pref == 'short':
        guide += f"- **短句优先**: 控制每句 {int(sent_avg)} 字左右，一句话一个意思\n"
        guide += "- **独立成段**: 短句可以单独成段，制造节奏感\n"
    else:
        guide += f"- **句子长度**: 平均 {int(sent_avg)} 字/句\n"

    # 标点符号
    punct = language.get('punctuation_style', {})
    if punct.get('ellipsis', 0) > 0:
        guide += "- **省略号**: 善用…制造停顿和思考感\n"
    if punct.get('brackets', 0) > 0:
        guide += "- **括号**: 用（）插入吐槽或补充说明\n"
    if punct.get('guillemets', 0) > 0:
        guide += "- **书名号**: 用「」框住概念或术语\n"

    # 过渡词
    transitions = language.get('common_transitions', [])
    if transitions:
        guide += f"\n## 推荐过渡词\n"
        guide += ", ".join(transitions[:5])
        guide += "\n"

    # 思考模式
    patterns = thinking.get('patterns', [])
    if patterns:
        guide += f"\n## 思考模式\n"
        for p in patterns:
            if p == 'multi_layer_deduction':
                guide += "- **多层推演**: 现象 → 初步结论 → 自我质疑 → 深层洞察\n"
                guide += "  使用句式: '但，这真的对吗？' '后来我开始怀疑'\n"
            elif p == 'contrast_validation':
                guide += "- **对比验证**: Before/After 或 A vs B 对比\n"
            elif p == 'case_based':
                guide += "- **案例分析**: 用具体案例支撑观点\n"

    # 独特表达
    unique = language.get('unique_patterns', [])
    if unique:
        guide += f"\n## 复用独特表达\n"
        for u in unique[:5]:
            guide += f"- {u}\n"

    return guide


def create_content(template_path, topic, materials=None, output_dir=None):
    """创作内容的主函数"""

    # 加载模板
    template = load_template(template_path)
    print(f"📖 已加载模板: {template['meta']['extracted_from']}")
    print(f"   风格类型: {template['thinking']['structure_pattern']}")

    # 确定输出路径
    if output_dir is None:
        output_dir = Path('.')
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # 生成大纲
    outline = generate_outline(template, topic)
    outline_path = output_dir / 'outline.md'
    outline_path.write_text(outline, encoding='utf-8')
    print(f"✅ 大纲已生成: {outline_path}")

    # 生成写作指导
    guide = generate_writing_guide(template, topic)
    guide_path = output_dir / 'writing-guide.md'
    guide_path.write_text(guide, encoding='utf-8')
    print(f"✅ 写作指导已生成: {guide_path}")

    # 生成初稿占位文件
    draft_placeholder = f"""# {topic}

> 基于模板 "{template['meta']['extracted_from']}" 创作

【根据 writing-guide.md 的风格指导和 outline.md 的大纲结构撰写内容】

---

## 写作检查清单

### 结构
- [ ] 符合 {template['thinking']['structure_pattern']} 结构
- [ ] 开头使用 {template['bookends'].get('opening', '适当')} 套路
- [ ] 结尾使用 {template['bookends'].get('closing', '适当')} 套路

### 语言风格
- [ ] 句子长度控制在 {int(template['language'].get('sentence_avg_length', 25))} 字左右
- [ ] 使用模板中的过渡词
- [ ] 复用独特表达方式

### 内容
- [ ] 有明确的核心观点
- [ ] 有案例或数据支撑
- [ ] 有独特洞察（非人云亦云）
"""

    draft_path = output_dir / 'draft.md'
    draft_path.write_text(draft_placeholder, encoding='utf-8')
    print(f"✅ 初稿占位已生成: {draft_path}")

    return {
        'outline': outline_path,
        'guide': guide_path,
        'draft': draft_path
    }


def main():
    parser = argparse.ArgumentParser(description='基于写作模板创作新内容')
    parser.add_argument('--template', '-t', required=True, help='模板文件路径')
    parser.add_argument('--topic', required=True, help='创作主题')
    parser.add_argument('--materials', '-m', help='参考资料路径（可选）')
    parser.add_argument('--output', '-o', default='.', help='输出目录')
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.exists():
        print(f"❌ 模板文件不存在: {template_path}")
        return 1

    print(f"📝 开始创作: {args.topic}")
    print(f"   使用模板: {template_path}")

    files = create_content(
        template_path=args.template,
        topic=args.topic,
        materials=args.materials,
        output_dir=args.output
    )

    print(f"\n📁 输出文件:")
    for name, path in files.items():
        print(f"   - {name}: {path.absolute()}")

    return 0


if __name__ == "__main__":
    exit(main())
