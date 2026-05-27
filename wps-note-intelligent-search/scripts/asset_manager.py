"""
WPS Note 智能搜索 Skill - 资产管理层

管理 ~/.claude/wps-search-assets/ 的 JSON 读写。
此模块通过 subprocess 调用，不进入 Context Window。
"""

import os
import json
import argparse
from typing import Dict, Any, Optional
from pathlib import Path


ASSETS_DIR = Path.home() / ".claude" / "wps-search-assets"


def ensure_assets_dir():
    """确保资产目录存在"""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    return ASSETS_DIR


def read_asset(filename: str) -> Optional[Dict[str, Any]]:
    """
    读取资产文件。

    Args:
        filename: 资产文件名（不含路径）

    Returns:
        资产内容字典，不存在则返回 None
    """
    filepath = ASSETS_DIR / filename
    if not filepath.exists():
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def write_asset(filename: str, data: Dict[str, Any]) -> bool:
    """
    写入资产文件。

    Args:
        filename: 资产文件名（不含路径）
        data: 要写入的数据

    Returns:
        是否写入成功
    """
    ensure_assets_dir()
    filepath = ASSETS_DIR / filename

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def list_assets() -> list:
    """列出所有资产文件"""
    if not ASSETS_DIR.exists():
        return []

    return [f.name for f in ASSETS_DIR.iterdir() if f.is_file() and f.suffix == '.json']


def delete_asset(filename: str) -> bool:
    """
    删除资产文件。

    Args:
        filename: 资产文件名

    Returns:
        是否删除成功
    """
    filepath = ASSETS_DIR / filename
    if not filepath.exists():
        return False

    try:
        filepath.unlink()
        return True
    except IOError:
        return False


def cli_main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(description="WPS Note 搜索资产管理")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # read 命令
    read_parser = subparsers.add_parser("read", help="读取资产")
    read_parser.add_argument("filename", help="资产文件名")

    # write 命令
    write_parser = subparsers.add_parser("write", help="写入资产")
    write_parser.add_argument("filename", help="资产文件名")
    write_parser.add_argument("--data", "-d", required=True, help="JSON 数据字符串")

    # list 命令
    subparsers.add_parser("list", help="列出资产")

    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除资产")
    delete_parser.add_argument("filename", help="资产文件名")

    args = parser.parse_args()

    if args.command == "read":
        result = read_asset(args.filename)
        if result is None:
            print(json.dumps({"error": "资产不存在或读取失败"}, ensure_ascii=False))
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "write":
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "无效的 JSON 数据"}, ensure_ascii=False))
            return 1

        success = write_asset(args.filename, data)
        print(json.dumps({"success": success}, ensure_ascii=False))

    elif args.command == "list":
        assets = list_assets()
        print(json.dumps({"assets": assets}, ensure_ascii=False, indent=2))

    elif args.command == "delete":
        success = delete_asset(args.filename)
        print(json.dumps({"success": success}, ensure_ascii=False))

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(cli_main())
