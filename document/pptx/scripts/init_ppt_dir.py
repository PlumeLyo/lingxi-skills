"""
PPT 目录初始化脚本

功能：为新的 PPT 项目创建目录结构。

使用方式：
    import sys
    sys.path.insert(0, "{skill_path}/skills/pptx/scripts")
    from init_ppt_dir import init_ppt_dir
    ppt_dir = init_ppt_dir("quarterly_report", "/path/to/workspace")
"""
from __future__ import annotations

from pathlib import Path


def init_ppt_dir(ppt_name: str, workspace_root: str | None = None) -> str:
    """初始化 PPT 项目目录。

    在 workspace_root 下创建以 ppt_name 命名的目录，

    Args:
        ppt_name: PPT 项目名称（不含扩展名）
        workspace_root: 工作空间根目录，默认为脚本上 3 级的 workspace 文件夹

    Returns:
        str: 创建的 PPT 目录的绝对路径

    Raises:
        FileExistsError: 如果目标目录已存在
    """
    if workspace_root is None:
        script_dir = Path(__file__).parent
        workspace_root_path = script_dir.parent.parent.parent / "workspace"
    else:
        workspace_root_path = Path(workspace_root)

    ppt_dir = workspace_root_path / ppt_name

    if ppt_dir.exists():
        raise FileExistsError(f"目录已存在: {ppt_dir}")

    try:
        ppt_dir.mkdir(parents=True, exist_ok=False)

        print(f"成功初始化PPT目录: {ppt_dir}")
        return str(ppt_dir)

    except FileExistsError:
        raise
    except Exception as e:
        if ppt_dir.exists():
            import shutil
            shutil.rmtree(ppt_dir)
        raise RuntimeError(f"初始化PPT目录失败: {e}")


def main() -> None:
    """命令行入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python init_ppt_dir.py <PPT项目名称> [工作空间路径]")
        print("示例: python init_ppt_dir.py quarterly_report /path/to/workspace")
        sys.exit(1)

    ppt_name = sys.argv[1]
    workspace_root = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        ppt_dir = init_ppt_dir(ppt_name, workspace_root)
        print(f"项目目录已创建: {ppt_dir}")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
