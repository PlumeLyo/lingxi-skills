#!/usr/bin/env python3
"""
验证作者配置是否完整
"""

import os
import sys
from pathlib import Path

import yaml


def get_config_path():
    """获取配置文件路径"""
    # 优先级: 环境变量 > 默认路径
    env_path = os.environ.get('CONTENT_CREATOR_CONFIG')
    if env_path:
        return Path(env_path)

    default_path = Path.home() / '.config' / 'content-creator' / 'author.yaml'
    return default_path


def validate_config():
    """验证配置完整性"""
    config_path = get_config_path()

    print(f"📖 检查配置文件: {config_path}")

    if not config_path.exists():
        print(f"❌ 配置文件不存在")
        print(f"\n请复制模板并填写你的信息:")
        print(f"  cp references/author-config.template.yaml {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 配置文件解析失败: {e}")
        return False

    errors = []
    warnings = []

    # 检查必需字段
    author = config.get('author', {})
    if not author.get('name') or author.get('name') == '你的姓名':
        errors.append("author.name 未填写")
    if not author.get('position') or '一句话定位' in str(author.get('position', '')):
        errors.append("author.position 未填写")

    # 检查栏目定义
    columns = config.get('columns', [])
    if not columns:
        warnings.append("未定义栏目 (columns)")
    elif len(columns) < 2:
        warnings.append("建议至少定义 2 个栏目")

    # 检查读者画像
    personas = config.get('personas', [])
    if not personas:
        warnings.append("未定义读者画像 (personas)")

    # 检查风格配置
    style = config.get('style', {})
    if not style.get('opening_template'):
        warnings.append("未配置开场白模板")
    if not style.get('closing_template'):
        warnings.append("未配置结尾模板")

    # 输出结果
    if errors:
        print(f"\n❌ 错误 ({len(errors)}):")
        for err in errors:
            print(f"   - {err}")

    if warnings:
        print(f"\n⚠️  警告 ({len(warnings)}):")
        for warn in warnings:
            print(f"   - {warn}")

    if not errors and not warnings:
        print("\n✅ 配置完整！")
        return True
    elif not errors:
        print("\n✅ 配置基本可用，建议完善警告项")
        return True
    else:
        print("\n❌ 配置不完整，请修复错误后重试")
        return False


if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)
