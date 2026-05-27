#!/usr/bin/env python3
"""
scan_docs.py - 扫描目录下的可导入文档

用法：
    python3 scan_docs.py <目录路径> [选项]

选项：
    --recursive         递归扫描子目录（默认启用）
    --no-recursive      不递归扫描
    --days N            只列出最近 N 天内修改的文件
    --source TYPE       来源类型：obsidian | siyuan | generic（默认自动检测）
    --formats a,b,c    只扫描指定格式，如：md,pdf,docx
    --output FILE       输出结果到 JSON 文件（默认输出到 stdout）
"""

import os
import sys
import json
import argparse
import datetime
import re
from pathlib import Path


SUPPORTED_FORMATS = {
    'md': 'Markdown',
    'markdown': 'Markdown',
    'pdf': 'PDF',
    'docx': 'Word 文档',
    'pptx': 'PowerPoint 演示文稿',
    'xlsx': 'Excel 表格',
    'xls': 'Excel 表格（旧版）',
    'txt': '纯文本',
    'sy': '思源笔记',
}

# 扫描时忽略的目录名
IGNORE_DIRS = {
    '.git', '.obsidian', '.trash', 'node_modules', '__pycache__',
    '.DS_Store', 'dist', 'build', '.venv', 'venv',
    # 思源笔记的内部目录
    'snippets', 'storage', 'templates', 'widgets', 'plugins', 'public',
}


def detect_source_type(root_path: Path) -> str:
    """自动检测目录类型：obsidian / siyuan / generic"""
    # 检测 Obsidian：有 .obsidian 目录
    if (root_path / '.obsidian').is_dir():
        return 'obsidian'
    # 检测思源：有 data/ 目录且 data/ 下有 .sy 文件
    data_dir = root_path / 'data'
    if data_dir.is_dir():
        for f in data_dir.rglob('*.sy'):
            return 'siyuan'
    # 如果根目录直接有 .sy 文件
    if list(root_path.rglob('*.sy')):
        return 'siyuan'
    return 'generic'


def estimate_image_count(file_path: Path) -> int:
    """估算文件中的图片数量（快速扫描，不完全解析）"""
    ext = file_path.suffix.lower().lstrip('.')
    if ext in ('pdf', 'docx', 'pptx'):
        # 这些格式通过解包才能知道图片数，先返回估算值
        size_mb = file_path.stat().st_size / (1024 * 1024)
        return max(0, int(size_mb * 2))  # 粗估：每 MB 约 2 张图
    elif ext in ('md', 'markdown'):
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            # 统计图片引用数量
            count = len(re.findall(r'!\[.*?\]\(.*?\)', content))
            count += len(re.findall(r'!\[\[.*?\]\]', content))  # Obsidian 语法
            return count
        except Exception:
            return 0
    elif ext == 'sy':
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            return content.count('"NodeImage"')
        except Exception:
            return 0
    return 0


def human_size(size_bytes: int) -> str:
    """将字节数转换为人类可读格式"""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def get_siyuan_notebook_name(file_path: Path, root_path: Path) -> str:
    """获取思源笔记文件所属的笔记本名称"""
    try:
        # 思源结构：root/data/笔记本名/*.sy
        rel = file_path.relative_to(root_path)
        parts = rel.parts
        if len(parts) >= 2 and parts[0] == 'data':
            return parts[1]
        # 直接在 root 下的情况：root/笔记本名/*.sy
        if len(parts) >= 1:
            return parts[0]
    except Exception:
        pass
    return ''


def scan_directory(
    root_path: Path,
    recursive: bool = True,
    days: int = None,
    source_type: str = None,
    formats: list = None,
) -> dict:
    """
    扫描目录，返回文件列表和统计信息

    Returns:
        dict: {
            source_type, root_path, files, total, formats, siyuan_notebooks
        }
    """
    root_path = root_path.resolve()

    if not root_path.exists():
        return {'error': f'目录不存在：{root_path}'}
    if not root_path.is_dir():
        return {'error': f'不是目录：{root_path}'}

    # 自动检测来源类型
    if not source_type or source_type == 'auto':
        source_type = detect_source_type(root_path)

    # 确定扫描格式
    allowed_exts = set(formats) if formats else set(SUPPORTED_FORMATS.keys())

    # 计算时间阈值
    cutoff_time = None
    if days:
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)

    files = []
    format_counts = {}
    siyuan_notebooks = set()

    # 收集所有文件
    if recursive:
        file_iter = root_path.rglob('*')
    else:
        file_iter = root_path.glob('*')

    for file_path in file_iter:
        if not file_path.is_file():
            continue

        # 跳过忽略目录中的文件
        parts_set = set(file_path.relative_to(root_path).parts[:-1])
        if parts_set & IGNORE_DIRS:
            continue

        ext = file_path.suffix.lower().lstrip('.')
        if ext not in allowed_exts:
            continue

        stat = file_path.stat()
        modified = datetime.datetime.fromtimestamp(stat.st_mtime)

        # 时间过滤
        if cutoff_time and modified < cutoff_time:
            continue

        # 思源笔记本信息
        notebook = ''
        if ext == 'sy':
            notebook = get_siyuan_notebook_name(file_path, root_path)
            if notebook:
                siyuan_notebooks.add(notebook)

        # 估算图片数
        img_count = estimate_image_count(file_path)

        file_info = {
            'path': str(file_path),
            'rel_path': str(file_path.relative_to(root_path)),
            'name': file_path.stem,
            'ext': ext,
            'format': SUPPORTED_FORMATS.get(ext, ext.upper()),
            'size_bytes': stat.st_size,
            'size_human': human_size(stat.st_size),
            'modified': modified.isoformat(),
            'estimated_images': img_count,
        }

        if notebook:
            file_info['siyuan_notebook'] = notebook

        files.append(file_info)
        format_counts[ext] = format_counts.get(ext, 0) + 1

    # 按修改时间降序排列
    files.sort(key=lambda x: x['modified'], reverse=True)

    result = {
        'source_type': source_type,
        'root_path': str(root_path),
        'files': files,
        'total': len(files),
        'formats': format_counts,
    }

    if siyuan_notebooks:
        result['siyuan_notebooks'] = sorted(siyuan_notebooks)

    return result


def format_file_list_for_display(scan_result: dict, max_display: int = 20) -> str:
    """格式化扫描结果，用于展示给用户"""
    if 'error' in scan_result:
        return f"❌ 错误：{scan_result['error']}"

    lines = []
    total = scan_result['total']
    fmt_counts = scan_result['formats']
    source = scan_result['source_type']

    source_labels = {
        'obsidian': 'Obsidian Vault',
        'siyuan': '思源笔记',
        'generic': '通用目录',
    }

    lines.append(f"📁 来源类型：{source_labels.get(source, source)}")
    lines.append(f"📂 扫描目录：{scan_result['root_path']}")
    lines.append(f"📊 共找到 {total} 个文件：")

    for ext, count in sorted(fmt_counts.items(), key=lambda x: -x[1]):
        fmt_name = SUPPORTED_FORMATS.get(ext, ext.upper())
        lines.append(f"   - {fmt_name} (.{ext})：{count} 个")

    if scan_result.get('siyuan_notebooks'):
        lines.append(f"\n📓 思源笔记本：{', '.join(scan_result['siyuan_notebooks'])}")

    lines.append(f"\n文件列表（{'前' + str(max_display) + '个，' if total > max_display else ''}共 {total} 个）：")

    files_to_show = scan_result['files'][:max_display]
    for i, f in enumerate(files_to_show, 1):
        img_info = f" 🖼{f['estimated_images']}张" if f['estimated_images'] > 0 else ""
        mod_date = f['modified'][:10]
        lines.append(
            f"  {i:3d}. {f['rel_path']:<50s}  "
            f"({mod_date}, {f['size_human']}{img_info})"
        )

    if total > max_display:
        lines.append(f"  ... 还有 {total - max_display} 个文件未显示")

    lines.append("\n请问你想如何导入？")
    lines.append("  [A] 全部导入（所有文件）")

    for ext, count in sorted(fmt_counts.items(), key=lambda x: -x[1]):
        fmt_name = SUPPORTED_FORMATS.get(ext, ext.upper())
        lines.append(f"  [{ext.upper()[0]}] 只导入 {fmt_name} 文件（{count} 个）")

    lines.append("  [D] 手动选择（输入文件编号，如：1,3,5-10）")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='扫描目录下的可导入文档',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('directory', help='要扫描的目录路径')
    parser.add_argument('--no-recursive', action='store_true', help='不递归扫描子目录')
    parser.add_argument('--days', type=int, help='只列出最近 N 天内修改的文件')
    parser.add_argument('--source', choices=['obsidian', 'siyuan', 'generic', 'auto'],
                        default='auto', help='来源类型（默认自动检测）')
    parser.add_argument('--formats', help='只扫描指定格式，逗号分隔（如 md,pdf,docx）')
    parser.add_argument('--output', help='将 JSON 结果输出到文件')
    parser.add_argument('--display', action='store_true', help='以人类可读格式输出（用于展示给用户）')
    parser.add_argument('--max-display', type=int, default=20, help='展示模式下最多显示几个文件（默认20）')

    args = parser.parse_args()

    formats = [f.strip().lower() for f in args.formats.split(',')] if args.formats else None

    result = scan_directory(
        root_path=Path(args.directory),
        recursive=not args.no_recursive,
        days=args.days,
        source_type=args.source,
        formats=formats,
    )

    if args.display:
        print(format_file_list_for_display(result, max_display=args.max_display))
    else:
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
            print(f"✓ 扫描结果已保存到：{args.output}")
        else:
            print(output)


if __name__ == '__main__':
    main()
