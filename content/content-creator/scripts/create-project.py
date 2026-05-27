#!/usr/bin/env python3
"""
创建文章项目文件夹
使用: python create-project.py "文章标题"
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path


def sanitize_filename(filename):
    """清理文件名，移除不合法字符"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.strip()
    if len(filename) > 50:
        filename = filename[:50]
    return filename


def create_project(title):
    """创建文章项目文件夹"""
    # 获取当前日期 MMDD
    today = datetime.now()
    date_prefix = today.strftime("%m.%d")

    # 清理标题
    clean_title = sanitize_filename(title)

    # 文件夹名称: MM.DD 标题关键词
    folder_name = f"{date_prefix} {clean_title}"

    # 创建项目路径（优先使用环境变量，否则使用当前目录）
    base_dir = os.environ.get('CONTENT_CREATOR_ARTICLES_DIR', '.')
    project_path = Path(base_dir) / folder_name

    # 如果文件夹已存在，添加序号
    counter = 1
    original_path = project_path
    while project_path.exists():
        project_path = Path(f"{original_path}_{counter}")
        counter += 1

    # 创建文件夹结构
    (project_path / "素材").mkdir(parents=True)
    (project_path / "versions").mkdir(parents=True)

    # 创建思路.md 模板
    idea_template = f"""# {title}

## 选题背景

[简要说明为什么选择这个话题]

## 核心观点

[一句话概括文章核心观点]

## 目标读者

[这篇文章主要面向哪类读者]

## 文章结构

### 开头
[如何引入]

### 主体
1. [第一部分]
2. [第二部分]
3. [第三部分]

### 结尾
[如何收尾]

## 参考材料

- [链接/文件]

## 预期栏目

[选择栏目]

## 预估字数

- [ ] 2000-3000（轻量分享）
- [ ] 5000-10000（技术分析）
- [ ] 10000+（深度长文）
"""

    (project_path / "思路.md").write_text(idea_template, encoding='utf-8')

    print(f"✅ 项目创建成功: {project_path}")
    print(f"   文件夹: {project_path.absolute()}")
    print(f"   下一步: 编辑 '思路.md' 完善选题思路")

    return project_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python create-project.py \"文章标题\"")
        sys.exit(1)

    title = sys.argv[1]
    create_project(title)
