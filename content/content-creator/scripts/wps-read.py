#!/usr/bin/env python3
"""
从 WPS 笔记读取文章并转换为 Markdown
使用: python wps-read.py --note-id <笔记ID> [--format md|json] [--output <路径>]
"""

import argparse
import json
import re
from pathlib import Path
from typing import Optional


class WPSNoteReader:
    """WPS 笔记内容读取和转换器"""

    def __init__(self):
        self.blocks = []

    def read_note(self, note_id: str) -> dict:
        """
        读取 WPS 笔记内容
        实际使用时调用 MCP 工具: mcp__wpsnote__read_note
        """
        # 这里是占位实现，实际应由 MCP 工具提供数据
        # 返回格式: { "title": "...", "content": "XML内容", "blocks": [...] }
        print(f"📖 正在读取笔记: {note_id}")
        print("   (实际使用时通过 MCP 工具读取)")
        return {
            "note_id": note_id,
            "title": "示例笔记",
            "content": "",
            "blocks": []
        }

    def xml_to_markdown(self, xml_content: str) -> str:
        """
        将 WPS 笔记 XML 转换为 Markdown

        ⚠️ MCP 约束注意：
        - 行内代码 <code> 在 MCP XML 中不支持，会被剥离
        - 引用块 <blockquote> 有严格的内容限制
        - 内容长度超过 2000 字符需要分批处理

        WPS Note XML 格式:
        - <p>: 段落
        - <h1>-<h6>: 标题
        - <strong>: 粗体
        - <em>: 斜体
        - <blockquote>: 引用（有约束）
        - <codeblock>: 代码块
        - <table>: 表格
        - <highlightBlock>: 高亮块
        - <columns>: 分栏
        """
        md_lines = []

        # 解析段落 (简化版，实际需要更完整的 XML 解析)
        # 段落
        xml_content = re.sub(
            r'<p[^>]*>(.*?)</p>',
            lambda m: self._convert_inline_styles(m.group(1)),
            xml_content,
            flags=re.DOTALL
        )

        # 标题
        for i in range(1, 7):
            xml_content = re.sub(
                rf'<h{i}[^>]*>(.*?)</h{i}>',
                rf'{"#" * i} \1\n\n',
                xml_content,
                flags=re.DOTALL
            )

        # 引用块
        xml_content = re.sub(
            r'<blockquote[^>]*>(.*?)</blockquote>',
            lambda m: self._convert_blockquote(m.group(1)),
            xml_content,
            flags=re.DOTALL
        )

        # 代码块
        xml_content = re.sub(
            r'<codeblock[^>]*lang="([^"]*)"[^>]*>(.*?)</codeblock>',
            r'```\1\n\2\n```\n\n',
            xml_content,
            flags=re.DOTALL
        )

        # 高亮块
        xml_content = re.sub(
            r'<highlightBlock[^>]*>(.*?)</highlightBlock>',
            lambda m: self._convert_highlight(m.group(1)),
            xml_content,
            flags=re.DOTALL
        )

        # 清理剩余标签
        xml_content = re.sub(r'<[^>]+>', '', xml_content)

        # 清理多余空行
        xml_content = re.sub(r'\n{3,}', '\n\n', xml_content)

        return xml_content.strip()

    def _convert_inline_styles(self, text: str) -> str:
        """
        转换内联样式

        注意：此方法是将 XML 转换为 Markdown 时使用的
        但在使用 wps-write.py 写入时，<code> 标签会被预处理移除
        因为 MCP XML 不支持行内代码
        """
        # 粗体
        text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
        # 斜体
        text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
        # 行内代码 - 在读取时保留，但写入时会被移除
        text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)
        # 链接
        text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text)

        return text + '\n\n'

    def _convert_blockquote(self, content: str) -> str:
        """转换引用块"""
        lines = content.strip().split('\n')
        quoted = '\n'.join(f'> {line}' for line in lines if line.strip())
        return quoted + '\n\n'

    def _convert_highlight(self, content: str) -> str:
        """转换高亮块"""
        # 提取 emoji 图标
        emoji_match = re.search(r'<emoji[^>]*value="([^"]*)"', content)
        emoji = emoji_match.group(1) if emoji_match else '💡'

        # 提取文本内容
        text = re.sub(r'<[^>]+>', '', content).strip()

        return f'{emoji} **提示**\n\n{text}\n\n'

    def extract_article_features(self, md_content: str) -> dict:
        """
        从文章内容中提取特征（用于模板提取）
        """
        lines = md_content.split('\n')

        # 统计特征
        total_lines = len(lines)
        heading_lines = [l for l in lines if l.startswith('#')]
        paragraph_lines = [l for l in lines if l.strip() and not l.startswith('#')]

        # 计算平均段落长度
        para_lengths = [len(l) for l in paragraph_lines]
        avg_para_length = sum(para_lengths) / len(para_lengths) if para_lengths else 0

        # 识别结构类型
        structure_type = "analysis"  # 默认为分析型
        if len(heading_lines) >= 3:
            structure_type = "structured"
        elif any('##' in l for l in lines[:5]):
            structure_type = "narrative"

        # 识别丰富的格式元素
        format_elements = {
            "code_blocks": len(re.findall(r'```[\s\S]*?```', md_content)),
            "tables": len(re.findall(r'\|.*\|.*\|', md_content)),
            "blockquotes": len(re.findall(r'^\u003e\s+', md_content, re.MULTILINE)),
            "highlight_blocks": len(re.findall(r'^(💡|⚠️|📝|💻|📊|📌)', md_content, re.MULTILINE)),
            "lists": {
                "bullet": len(re.findall(r'^[-*+]\s+', md_content, re.MULTILINE)),
                "numbered": len(re.findall(r'^\d+\.\s+', md_content, re.MULTILINE)),
                "todo": len(re.findall(r'^-?\s*\[([ x])\]', md_content, re.MULTILINE))
            },
            "images": len(re.findall(r'!\[.*?\]\(.*?\)', md_content)),
            "links": len(re.findall(r'\[.*?\]\(.*?\)', md_content)),
            "inline_code": len(re.findall(r'`[^`]+`', md_content))
        }

        # 识别推荐的格式增强
        format_enhancements = []
        if format_elements["code_blocks"] > 0:
            format_enhancements.append("代码块高亮")
        if format_elements["tables"] > 0:
            format_enhancements.append("表格展示")
        if format_elements["highlight_blocks"] > 0:
            format_enhancements.append("高亮提示块")
        if format_elements["blockquotes"] > 0:
            format_enhancements.append("引用块样式")

        return {
            "total_lines": total_lines,
            "heading_count": len(heading_lines),
            "paragraph_count": len(paragraph_lines),
            "avg_paragraph_length": round(avg_para_length, 1),
            "structure_type": structure_type,
            "headings": [l.strip() for l in heading_lines[:10]],
            "format_elements": format_elements,
            "format_enhancements": format_enhancements
        }


def search_and_select_note(keyword: str) -> Optional[str]:
    """
    搜索并选择笔记
    调用 MCP 工具: mcp__wpsnote__search_notes
    """
    print(f"🔍 搜索笔记: {keyword}")
    # 实际使用时:
    # result = mcp__wpsnote__search_notes(keyword=keyword)
    # 返回 note_id
    return None


def main():
    parser = argparse.ArgumentParser(description='从 WPS 笔记读取文章')
    parser.add_argument('--note-id', '-n', help='笔记 ID')
    parser.add_argument('--search', '-s', help='搜索关键词（自动选择第一个结果）')
    parser.add_argument('--format', '-f', choices=['md', 'json'], default='md',
                        help='输出格式 (默认: md)')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--extract-template', '-t', action='store_true',
                        help='同时提取写作模板')
    args = parser.parse_args()

    reader = WPSNoteReader()

    # 获取笔记 ID
    note_id = args.note_id
    if args.search:
        note_id = search_and_select_note(args.search)
        if not note_id:
            print("❌ 未找到匹配的笔记")
            return 1

    if not note_id:
        print("❌ 请提供 --note-id 或 --search")
        return 1

    # 读取笔记
    note = reader.read_note(note_id)
    title = note.get('title', 'untitled')

    # 转换为 Markdown
    md_content = reader.xml_to_markdown(note.get('content', ''))

    # 添加标题
    full_md = f"# {title}\n\n{md_content}"

    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        output_path = Path(f"{safe_title}.{args.format}")

    # 根据格式输出
    if args.format == 'md':
        output_path.write_text(full_md, encoding='utf-8')
        print(f"✅ Markdown 已保存: {output_path}")

    elif args.format == 'json':
        features = reader.extract_article_features(md_content)
        output = {
            "title": title,
            "content": md_content,
            "features": features
        }
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"✅ JSON 已保存: {output_path}")

    # 提取模板
    if args.extract_template:
        template_path = output_path.with_suffix('.template.json')
        features = reader.extract_article_features(md_content)
        template = {
            "meta": {
                "source": f"wps-note:{note_id}",
                "title": title,
                "extracted_at": "auto"
            },
            "structure": features,
            "content_sample": md_content[:2000] if len(md_content) > 2000 else md_content
        }
        template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"✅ 模板已提取: {template_path}")

    print(f"\n📊 文章统计:")
    print(f"   标题: {title}")
    print(f"   字数: {len(md_content)}")

    return 0


if __name__ == "__main__":
    exit(main())
