"""
WPS Note 智能搜索 Skill - 轻量级入口

此模块仅提供 CLI 接口，通过 subprocess 调用，不进入 Context Window。
"""

__version__ = "1.0.0"

import sys
import json
import argparse
from typing import Optional, Dict, Any


def parse_intent(query: str) -> Dict[str, Any]:
    """
    解析用户查询，提取搜索参数。

    Args:
        query: 用户自然语言查询

    Returns:
        包含搜索参数的字典
    """
    query = query.strip()
    if not query:
        return {"error": "查询不能为空"}

    # 时间关键词映射
    time_keywords = {
        "今天": {"since": "today", "before": "today"},
        "昨日": {"since": "yesterday", "before": "yesterday"},
        "昨天": {"since": "yesterday", "before": "yesterday"},
        "本周": {"since": "this_week_start", "before": "now"},
        "上周": {"since": "last_week_start", "before": "last_week_end"},
        "本月": {"since": "this_month_start", "before": "now"},
        "上月": {"since": "last_month_start", "before": "last_month_end"},
        "最近": {"since": "7_days_ago", "before": "now"},
        "近期": {"since": "7_days_ago", "before": "now"},
    }

    # 提取时间范围
    time_range = None
    for keyword, range_def in time_keywords.items():
        if keyword in query:
            time_range = range_def
            break

    # 提取标签（以 # 开头或引号中的内容）
    import re
    tags = re.findall(r'#(\w+)', query)

    # 提取关键词（去除时间词后的剩余内容）
    keywords = query
    for keyword in time_keywords.keys():
        keywords = keywords.replace(keyword, "")
    # 去除常见停用词
    for word in ["的", "笔记", "关于", "查找", "搜索", "找一下", "帮我", "给我"]:
        keywords = keywords.replace(word, "")
    keywords = keywords.strip()

    return {
        "query": query,
        "keywords": keywords if keywords else None,
        "time_range": time_range,
        "tags": tags if tags else None,
        "max_results": 10,
    }


def cli_main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(description="WPS Note 智能搜索")
    parser.add_argument("command", choices=["parse"], help="命令")
    parser.add_argument("--query", "-q", required=True, help="搜索查询")
    parser.add_argument("--output", "-o", help="输出文件路径")

    args = parser.parse_args()

    if args.command == "parse":
        result = parse_intent(args.query)
        output = json.dumps(result, ensure_ascii=False, indent=2)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"结果已保存到: {args.output}")
        else:
            print(output)

    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
