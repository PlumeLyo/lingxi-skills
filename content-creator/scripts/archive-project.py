#!/usr/bin/env python3
"""
Archive project related files to project directory

Usage:
    python3 archive-project.py <project-name> [files...]

Example:
    python3 archive-project.py my-project reference.html notes.md screenshots/
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime


def ensure_archive_dir(project_path):
    """Ensure archive directory exists"""
    archive_dir = project_path / "archive"
    archive_dir.mkdir(exist_ok=True)
    return archive_dir


def archive_file(source_path, archive_dir):
    """Archive a single file or directory"""
    source = Path(source_path).resolve()

    if not source.exists():
        print(f"⚠️  Skip: {source_path} (not exists)")
        return None

    target = archive_dir / source.name

    # If target exists, add timestamp to avoid overwriting
    if target.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = target.stem
        suffix = target.suffix
        target = target.parent / f"{stem}_{timestamp}{suffix}"

    # Copy file or directory
    try:
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            print(f"✅ Archived: {source.name} → archive/{target.relative_to(archive_dir)}")
        elif source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
            print(f"✅ Archived: {source.name}/ → archive/{target.relative_to(archive_dir)}/")
        return target
    except Exception as e:
        print(f"❌ Archive failed: {source_path} - {e}")
        return None


def generate_manifest(archive_dir, archived_files):
    """Generate archive manifest"""
    manifest_path = archive_dir / "MANIFEST.md"

    content = f"""# Archive Manifest

> Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Archived Files

"""

    for i, file_info in enumerate(archived_files, 1):
        if file_info:
            relative_path = file_info.relative_to(archive_dir)
            content += f"{i}. `{relative_path}`\n"

    content += """
## Notes

This directory contains reference materials and research files used during the project.
"""

    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n📋 Manifest generated: archive/MANIFEST.md")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 archive-project.py <project-name> [files...]")
        print("\nExample:")
        print("  python3 archive-project.py my-project reference.html notes.md")
        sys.exit(1)

    project_name = sys.argv[1]
    files_to_archive = sys.argv[2:] if len(sys.argv) > 2 else []

    project_path = Path(f"projects/{project_name}")

    if not project_path.exists():
        print(f"❌ Error: Project not found: {project_path}")
        sys.exit(1)

    print(f"📦 Archiving files to project: {project_name}\n")

    archive_dir = ensure_archive_dir(project_path)

    if not files_to_archive:
        print("💡 No files specified for archiving")
        sys.exit(0)

    archived_files = []
    for file_path in files_to_archive:
        result = archive_file(file_path, archive_dir)
        if result:
            archived_files.append(result)

    if archived_files:
        generate_manifest(archive_dir, archived_files)
        print(f"\n✅ Archive complete! Total: {len(archived_files)} files")
    else:
        print("\n⚠️ No files were archived")


if __name__ == '__main__':
    main()
