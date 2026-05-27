#!/usr/bin/env python3
"""
从样张文章提取写作模板
使用: python extract-template.py <样张文件路径> [--output template.json]
"""

import argparse
import json
import re
from pathlib import Path
from collections import Counter
import math


def analyze_structure(text):
    """分析文章结构"""
    lines = text.split('\n')
    sections = []
    current_section = {"type": "intro", "content": "", "length": 0}

    # 识别标题/章节
    heading_pattern = re.compile(r'^(#{1,6}\s+|\d+[\.、]|【|「|\[)', re.MULTILINE)
    paragraphs = text.split('\n\n')

    # 分析丰富的格式元素（基于 WPS Note 能力）
    format_elements = {
        "code_blocks": len(re.findall(r'```[\s\S]*?```', text)),
        "tables": len(re.findall(r'\|.*\|.*\|', text)),
        "blockquotes": len(re.findall(r'^>\s+', text, re.MULTILINE)),
        "highlight_blocks": len(re.findall(r'^(💡|⚠️|📝|💻|📊|📌)', text, re.MULTILINE)),
        "lists": {
            "bullet": len(re.findall(r'^[-*+]\s+', text, re.MULTILINE)),
            "numbered": len(re.findall(r'^\d+\.\s+', text, re.MULTILINE)),
            "todo": len(re.findall(r'^-?\s*\[([ x])\]', text, re.MULTILINE))
        },
        "images": len(re.findall(r'!\[.*?\]\(.*?\)', text)),
        "links": len(re.findall(r'\[.*?\]\(.*?\)', text)),
        "inline_code": len(re.findall(r'`[^`]+`', text))
    }

    section_types = []
    for para in paragraphs[:20]:  # 分析前20段
        para = para.strip()
        if not para:
            continue

        # 识别段落类型
        if heading_pattern.match(para):
            section_types.append("heading")
        elif len(para) < 50:
            if any(w in para for w in ['？', '?']):
                section_types.append("question")
            else:
                section_types.append("short")
        elif '：' in para[:20] or ':' in para[:20]:
            section_types.append("explanation")
        else:
            section_types.append("content")

    # 统计段落长度分布
    para_lengths = [len(p) for p in paragraphs if p.strip()]
    if para_lengths:
        avg_length = sum(para_lengths) / len(para_lengths)
        short_ratio = sum(1 for l in para_lengths if l < 100) / len(para_lengths)
        medium_ratio = sum(1 for l in para_lengths if 100 <= l < 500) / len(para_lengths)
        long_ratio = sum(1 for l in para_lengths if l >= 500) / len(para_lengths)
    else:
        avg_length = 0
        short_ratio = medium_ratio = long_ratio = 0

    return {
        "section_types": Counter(section_types),
        "avg_paragraph_length": round(avg_length, 1),
        "paragraph_distribution": {
            "short": round(short_ratio, 2),
            "medium": round(medium_ratio, 2),
            "long": round(long_ratio, 2)
        },
        "total_paragraphs": len(para_lengths),
        "format_elements": format_elements
    }


def analyze_language(text):
    """分析语言风格特征"""
    sentences = re.split(r'[。！？；\n]', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # 句子长度统计
    sent_lengths = [len(s) for s in sentences]
    avg_length = sum(sent_lengths) / len(sent_lengths) if sent_lengths else 0

    # 标点符号分析
    punctuation_patterns = {
        "ellipsis": len(re.findall(r'…|\.\.\.', text)),  # 省略号
        "brackets": len(re.findall(r'[（(].*?[）)]', text)),  # 括号
        "guillemets": len(re.findall(r'[「『].*?[」』]', text)),  # 书名号
        "quotes": len(re.findall(r'[""].*?[""]', text)),  # 引号
        "exclamation": len(re.findall(r'！', text)),  # 感叹号
        "question": len(re.findall(r'[？?]', text)),  # 问号
    }

    # 常用过渡词/句式
    transition_words = []
    patterns = [
        r'坦白讲|说实话|实在话|说白了|简单来说',
        r'但.*?是|不过|然而',
        r'后来|之后|然后',
        r'首先|其次|最后',
        r'比如|例如|像',
        r'这意味着|这说明|这表示',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            transition_words.extend(matches[:3])  # 取前3个

    # 独特表达识别
    unique_patterns = []
    if re.search(r'但，这真的对[吗么]', text):
        unique_patterns.append("自我质疑: 但，这真的对吗？")
    if re.search(r'后来我开始怀疑', text):
        unique_patterns.append("转折: 后来我开始怀疑")
    if re.search(r'真正[的得]', text):
        unique_patterns.append("强调: 真正的问题/本质")

    return {
        "sentence": {
            "avg_length": round(avg_length, 1),
            "preference": "short" if avg_length < 30 else "medium" if avg_length < 50 else "long",
            "count": len(sentences)
        },
        "punctuation": punctuation_patterns,
        "transitions": list(set(transition_words))[:10],
        "unique_patterns": unique_patterns
    }


def analyze_thinking(text):
    """分析思考模式"""
    thinking_patterns = []

    # 多层推演识别
    deduction_markers = [
        r'第一层[：:]|第一层推演',
        r'第二层[：:]|第二层推演',
        r'第三层[：:]|第三层推演',
    ]
    deduction_count = sum(len(re.findall(p, text)) for p in deduction_markers)
    if deduction_count >= 2:
        thinking_patterns.append("multi_layer_deduction")

    # 对比验证识别
    contrast_markers = [
        r'[而但].*?[却反而]',
        r'Before|After|之前|之后',
        r'对比|相比|相较于',
        r'一方面.*另一方面',
    ]
    contrast_count = sum(len(re.findall(p, text)) for p in contrast_markers)
    if contrast_count >= 3:
        thinking_patterns.append("contrast_validation")

    # 案例分析识别
    case_markers = len(re.findall(r'案例|例子|比如|例如|像.*?一样', text))
    if case_markers >= 3:
        thinking_patterns.append("case_based")

    # 情感升华识别
    emotion_markers = len(re.findall(r'感慨|触动|感动|震撼|焦虑|迷茫|希望', text))
    if emotion_markers >= 2:
        thinking_patterns.append("emotional_arc")

    # 结构类型判断
    if "multi_layer_deduction" in thinking_patterns:
        structure_pattern = "多层推演"
    elif "contrast_validation" in thinking_patterns:
        structure_pattern = "对比验证"
    elif "case_based" in thinking_patterns:
        structure_pattern = "案例分析"
    else:
        structure_pattern = "线性论述"

    return {
        "patterns": thinking_patterns,
        "structure_pattern": structure_pattern,
        "depth_indicators": {
            "deduction_layers": deduction_count,
            "contrasts": contrast_count,
            "cases": case_markers
        }
    }


def extract_opening_closing(text):
    """提取开头和结尾套路"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    opening = ""
    closing = ""

    if paragraphs:
        # 分析开头
        first_para = paragraphs[0]
        if len(first_para) < 100:
            if any(w in first_para for w in ['Hi', '你好', '我是']):
                opening = "自我介绍开场"
            elif '？' in first_para or '?' in first_para:
                opening = "提问开场"
            else:
                opening = "短句引入"
        else:
            opening = "场景描述开场"

        # 分析结尾
        last_para = paragraphs[-1]
        if any(w in last_para for w in ['？', '?']):
            closing = "开放问题结尾"
        elif any(w in last_para for w in ['总结', '总的来说', '总之']):
            closing = "总结式结尾"
        elif any(w in last_para for w in ['关于我', '关注我']):
            closing = "引导关注结尾"
        else:
            closing = "观点收束结尾"

    return {
        "opening": opening,
        "closing": closing
    }


def generate_template(text, filename):
    """生成完整模板"""
    word_count = len(text)

    structure = analyze_structure(text)
    language = analyze_language(text)
    thinking = analyze_thinking(text)
    bookends = extract_opening_closing(text)

    # 识别推荐的 WPS 格式增强
    format_enhancements = []
    if structure.get("format_elements", {}).get("code_blocks", 0) > 0:
        format_enhancements.append("代码块高亮")
    if structure.get("format_elements", {}).get("tables", 0) > 0:
        format_enhancements.append("表格展示")
    if structure.get("format_elements", {}).get("highlight_blocks", 0) > 0:
        format_enhancements.append("高亮提示块")
    if structure.get("format_elements", {}).get("blockquotes", 0) > 0:
        format_enhancements.append("引用块样式")

    template = {
        "meta": {
            "extracted_from": filename,
            "extracted_at": "auto",
            "word_count": word_count,
            "style_type": thinking["structure_pattern"],
            "format_enhancements": format_enhancements
        },
        "structure": {
            "type": thinking["structure_pattern"],
            "paragraph_distribution": structure["paragraph_distribution"],
            "avg_paragraph_length": structure["avg_paragraph_length"],
            "total_paragraphs": structure["total_paragraphs"],
            "format_elements": structure["format_elements"]
        },
        "language": {
            "sentence_avg_length": language["sentence"]["avg_length"],
            "sentence_preference": language["sentence"]["preference"],
            "punctuation_style": {
                k: v for k, v in language["punctuation"].items() if v > 0
            },
            "common_transitions": language["transitions"],
            "unique_patterns": language["unique_patterns"]
        },
        "thinking": {
            "patterns": thinking["patterns"],
            "depth": thinking["depth_indicators"]
        },
        "bookends": bookends
    }

    return template


def main():
    parser = argparse.ArgumentParser(description='从样张文章提取写作模板')
    parser.add_argument('input', help='样张文件路径')
    parser.add_argument('--output', '-o', default='template.json', help='输出模板文件路径')
    args = parser.parse_args()

    # 读取样张
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        return 1

    text = input_path.read_text(encoding='utf-8')

    # 检查字数
    word_count = len(text)
    if word_count < 500:
        print(f"⚠️ 样张较短 ({word_count} 字)，可能影响提取质量。建议提供 1000 字以上的完整文章。")

    print(f"📖 正在分析: {input_path.name} ({word_count} 字)")

    # 生成模板
    template = generate_template(text, input_path.name)

    # 保存模板
    output_path = Path(args.output)
    output_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"✅ 模板已保存: {output_path.absolute()}")
    print(f"\n📋 提取到的关键特征:")
    print(f"   - 结构类型: {template['thinking']['structure_pattern']}")
    print(f"   - 句子偏好: {template['language']['sentence_preference']} (平均 {template['language']['sentence_avg_length']} 字/句)")
    print(f"   - 开头套路: {template['bookends']['opening']}")
    print(f"   - 结尾套路: {template['bookends']['closing']}")

    if template['language']['unique_patterns']:
        print(f"   - 独特表达: {', '.join(template['language']['unique_patterns'][:3])}")

    # 显示格式元素
    format_elements = template['structure'].get('format_elements', {})
    if format_elements:
        print(f"\n🎨 检测到的格式元素:")
        if format_elements.get('code_blocks', 0) > 0:
            print(f"   - 代码块: {format_elements['code_blocks']} 个")
        if format_elements.get('tables', 0) > 0:
            print(f"   - 表格: {format_elements['tables']} 行")
        if format_elements.get('highlight_blocks', 0) > 0:
            print(f"   - 高亮块: {format_elements['highlight_blocks']} 个")
        if format_elements.get('blockquotes', 0) > 0:
            print(f"   - 引用块: {format_elements['blockquotes']} 处")

    return 0


if __name__ == "__main__":
    exit(main())
