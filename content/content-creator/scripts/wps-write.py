#!/usr/bin/env python3
"""
将 Markdown 文章写入 WPS 笔记
使用: python wps-write.py --input <md文件> [--title <标题>] [--parent <父笔记ID>]
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List


class WPSNoteWriter:
    """WPS 笔记内容写入器"""

    def __init__(self):
        self.blocks = []

    def preprocess_markdown(self, md_content: str) -> str:
        """
        预处理 Markdown 内容，避免 MCP 错误

        主要处理：
        1. 移除行内代码标记（MCP 不支持 <code>）
        2. 转换引用块为普通段落（避免 blockquote 约束错误）
        3. 处理复杂表格
        """
        # 1. 处理行内代码 - 转换为普通文本（保留内容）
        # 注意：不能直接用 <code> 标签，MCP 会报错
        md_content = re.sub(r'`([^`]+)`', r'\1', md_content)

        # 2. 处理引用块 - 移除 > 标记，转为普通段落
        lines = md_content.split('\n')
        processed_lines = []
        for line in lines:
            if line.strip().startswith('>'):
                # 移除引用标记
                line = re.sub(r'^\s*>\s*', '', line)
            processed_lines.append(line)
        md_content = '\n'.join(processed_lines)

        return md_content

    def markdown_to_xml(self, md_content: str) -> str:
        """
        将 Markdown 转换为 WPS Note XML 格式
        支持丰富的格式元素：表格、高亮块、列表等
        """
        xml_blocks = []
        lines = md_content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            # 标题
            if stripped.startswith('#'):
                level = len(stripped) - len(stripped.lstrip('#'))
                content = stripped.lstrip('#').strip()
                xml_blocks.append(f'<h{level} id="block_{len(xml_blocks)}"><p>{self._escape_xml(content)}</p></h{level}>')
                i += 1
                continue

            # 代码块
            if stripped.startswith('```'):
                lang = stripped[3:].strip() or 'text'
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                code_content = '\n'.join(code_lines)
                xml_blocks.append(
                    f'<codeblock id="block_{len(xml_blocks)}" lang="{lang}">'
                    f'{self._escape_xml(code_content)}'
                    f'</codeblock>'
                )
                i += 1
                continue

            # 表格
            if '|' in stripped and i + 1 < len(lines) and '---' in lines[i + 1]:
                table_rows = []
                # 表头
                headers = [cell.strip() for cell in stripped.split('|') if cell.strip()]
                table_rows.append(headers)
                i += 2  # 跳过表头和分隔符
                # 数据行
                while i < len(lines) and '|' in lines[i]:
                    cells = [cell.strip() for cell in lines[i].split('|') if cell.strip()]
                    if cells:
                        table_rows.append(cells)
                    i += 1
                xml_blocks.append(self._convert_table(table_rows))
                continue

            # 高亮块（以 emoji 开头）
            highlight_match = re.match(r'^(💡|⚠️|📝|💻|📊|📌|✅|❌)\s*\*\*(.+?)\*\*(.*)$', stripped)
            if highlight_match:
                emoji = highlight_match.group(1)
                title = highlight_match.group(2)
                content = highlight_match.group(3).strip()
                # 收集高亮块的内容（直到空行或下一个高亮块）
                highlight_content = [content] if content else []
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(('💡', '⚠️', '📝', '💻', '📊', '📌', '✅', '❌')):
                    highlight_content.append(lines[i].strip())
                    i += 1
                xml_blocks.append(self._convert_highlight(emoji, title, highlight_content))
                continue

            # 引用块
            if stripped.startswith('>'):
                quote_lines = []
                while i < len(lines) and lines[i].strip().startswith('>'):
                    quote_lines.append(lines[i].strip()[1:].strip())
                    i += 1
                quote_content = '\n'.join(quote_lines)
                xml_blocks.append(
                    f'<blockquote id="block_{len(xml_blocks)}">'
                    f'<p>{self._format_inline(self._escape_xml(quote_content))}</p>'
                    f'</blockquote>'
                )
                continue

            # 列表
            list_match = re.match(r'^([-*+]|\d+\.)\s+(.+)$', stripped)
            if list_match:
                list_type = 'bullet' if list_match.group(1) in '-*+' else 'ordered'
                list_items = []
                while i < len(lines):
                    line_stripped = lines[i].strip()
                    if list_type == 'bullet' and line_stripped.startswith(('- ', '* ', '+ ')):
                        list_items.append(line_stripped[2:])
                        i += 1
                    elif list_type == 'ordered' and re.match(r'^\d+\.\s+', line_stripped):
                        list_items.append(re.sub(r'^\d+\.\s*', '', line_stripped))
                        i += 1
                    elif line_stripped.startswith('  ') and list_items:
                        # 列表项的延续
                        list_items[-1] += ' ' + line_stripped.strip()
                        i += 1
                    elif not line_stripped:
                        i += 1
                        continue
                    else:
                        break

                for item in list_items:
                    xml_blocks.append(
                        f'<p id="block_{len(xml_blocks)}" listType="{list_type}" listLevel="0">'
                        f'{self._format_inline(self._escape_xml(item))}'
                        f'</p>'
                    )
                continue

            # 分割线
            if stripped == '---' or stripped == '***' or stripped == '___':
                xml_blocks.append(f'<hr id="block_{len(xml_blocks)}"/>')
                i += 1
                continue

            # 普通段落
            xml_blocks.append(
                f'<p id="block_{len(xml_blocks)}">'
                f'{self._format_inline(self._escape_xml(stripped))}'
                f'</p>'
            )
            i += 1

        return '\n'.join(xml_blocks)

    def _escape_xml(self, text: str) -> str:
        """转义 XML 特殊字符"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

    def _format_inline(self, text: str) -> str:
        """
        格式化内联样式

        ⚠️ 注意：MCP XML 不支持 <code> 行内代码标签
        行内代码在 markdown_to_xml 预处理阶段已被移除
        """
        # 粗体 **text**
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        # 斜体 *text*
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        # ⚠️ 不处理行内代码 - MCP XML 不支持 <code> 标签
        # text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        # 链接 [text](url) - 谨慎使用，部分场景可能不支持
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        return text

    def _convert_table(self, rows: list) -> str:
        """将表格数据转换为 WPS XML"""
        xml = f'<table id="block_{len(self.blocks)}">\n'
        for i, row in enumerate(rows):
            xml += '  <tr>\n'
            for cell in row:
                tag = 'th' if i == 0 else 'td'
                xml += f'    <{tag}><p>{self._format_inline(self._escape_xml(cell))}</p></{tag}>\n'
            xml += '  </tr>\n'
        xml += '</table>'
        return xml

    def _convert_highlight(self, emoji: str, title: str, content: list) -> str:
        """将高亮块转换为 WPS XML"""
        # 根据 emoji 选择颜色
        color_map = {
            '💡': ('#FAF1E6', '#FEC794'),  # 黄色 - 提示
            '⚠️': ('#FAE6E6', '#F2A7A7'),  # 红色 - 警告
            '📝': ('#E6EEFA', '#98C1FF'),  # 蓝色 - 笔记
            '💻': ('#E6FAEB', '#AFE3BB'),  # 绿色 - 代码
            '📊': ('#F5EBFA', '#E5B5FD'),  # 紫色 - 数据
            '📌': ('#FAF1E6', '#FEC794'),  # 黄色 - 重点
            '✅': ('#E6FAEB', '#AFE3BB'),  # 绿色 - 成功
            '❌': ('#FAE6E6', '#F2A7A7'),  # 红色 - 错误
        }
        bg_color, border_color = color_map.get(emoji, ('#FAF1E6', '#FEC794'))

        content_xml = f'<p><strong>{self._escape_xml(title)}</strong></p>'
        for line in content:
            if line:
                content_xml += f'<p>{self._format_inline(self._escape_xml(line))}</p>'

        return (
            f'<highlightBlock emoji="{emoji}" '
            f'highlightBlockBackgroundColor="{bg_color}" '
            f'highlightBlockBorderColor="{border_color}">\n'
            f'  {content_xml}\n'
            f'</highlightBlock>'
        )

    def create_note(self, title: str, xml_content: str, parent_id: Optional[str] = None) -> dict:
        """创建新笔记"""
        print(f"📝 创建笔记: {title}")
        print(f"   内容块数: {xml_content.count('<p') + xml_content.count('<h')}")
        print("   (实际使用时通过 MCP 工具创建)")

        return {
            "note_id": f"new_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "status": "created"
        }

    def append_to_note(self, note_id: str, xml_content: str) -> dict:
        """追加内容到现有笔记"""
        print(f"📝 追加内容到笔记: {note_id}")
        print("   (实际使用时通过 MCP 工具追加)")

        return {
            "note_id": note_id,
            "status": "appended"
        }


def generate_front_matter(title: str, author: str = "", tags: List[str] = None) -> str:
    """生成文章前言/元数据"""
    today = datetime.now().strftime("%Y-%m-%d")

    front_matter = f"""---
title: {title}
date: {today}
"""
    if author:
        front_matter += f"author: {author}\n"
    if tags:
        front_matter += f"tags: {', '.join(tags)}\n"

    front_matter += "---\n\n"
    return front_matter


def format_for_wechat(md_content: str, title: str) -> str:
    """格式化为公众号风格"""
    formatted = md_content

    # 确保段落间距
    formatted = re.sub(r'\n{2,}', '\n\n', formatted)

    # 加粗小标题
    formatted = re.sub(
        r'^##\s*(.+)$',
        r'## **\1**',
        formatted,
        flags=re.MULTILINE
    )

    # 添加开头引导
    if not formatted.startswith('#'):
        formatted = f"# {title}\n\n{formatted}"

    return formatted


def main():
    parser = argparse.ArgumentParser(description='将文章写入 WPS 笔记')
    parser.add_argument('--input', '-i', required=True, help='输入 Markdown 文件')
    parser.add_argument('--title', '-t', help='笔记标题（默认使用文件名）')
    parser.add_argument('--parent', '-p', help='父笔记 ID（用于创建子笔记）')
    parser.add_argument('--append', '-a', help='追加到现有笔记 ID')
    parser.add_argument('--tags', help='标签，逗号分隔')
    parser.add_argument('--author', help='作者名')
    parser.add_argument('--wechat-style', '-w', action='store_true',
                        help='应用公众号格式优化')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='仅预览，不实际写入')
    args = parser.parse_args()

    # 读取输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        return 1

    md_content = input_path.read_text(encoding='utf-8')

    # 确定标题
    title = args.title
    if not title:
        match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
        if match:
            title = match.group(1)
        else:
            title = input_path.stem

    print(f"📄 读取文件: {input_path}")
    print(f"📝 文章标题: {title}")
    print(f"📊 字数统计: {len(md_content)}")

    # 公众号格式优化
    if args.wechat_style:
        md_content = format_for_wechat(md_content, title)
        print("✨ 已应用公众号格式")

    # 添加前言
    tags = args.tags.split(',') if args.tags else []
    front_matter = generate_front_matter(title, args.author, tags)
    full_content = front_matter + md_content

    # 预处理 Markdown（避免 MCP 错误）
    print("🔄 预处理内容（移除不支持的格式）...")
    writer = WPSNoteWriter()
    full_content = writer.preprocess_markdown(full_content)

    # 转换为 XML
    xml_content = writer.markdown_to_xml(full_content)

    if args.dry_run:
        print("\n🔍 预览模式（未实际写入）")
        print("=" * 50)
        print(f"标题: {title}")
        print(f"标签: {tags}")
        print(f"内容预览 (前500字符):")
        print(xml_content[:500] + "..." if len(xml_content) > 500 else xml_content)
        print("=" * 50)
        return 0

    # 写入 WPS 笔记
    if args.append:
        result = writer.append_to_note(args.append, xml_content)
        print(f"\n✅ 内容已追加到笔记: {args.append}")
    else:
        result = writer.create_note(title, xml_content, args.parent)
        print(f"\n✅ 笔记已创建:")
        print(f"   ID: {result['note_id']}")
        print(f"   标题: {result['title']}")

    return 0


if __name__ == "__main__":
    exit(main())
