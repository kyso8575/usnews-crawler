#!/usr/bin/env python3
"""
Delete university folders under downloads/ when all files inside have identical sizes.

Default behavior:
- Only consider .html files
- Dry-run (no deletion). Use --yes to actually delete
- Require at least 2 matching files (configurable via --min-files)

Usage examples:
  python clean_equal_size_folders.py                  # dry-run, downloads/, *.html
  python clean_equal_size_folders.py --yes            # actually delete
  python clean_equal_size_folders.py --dir downloads  # explicit directory
  python clean_equal_size_folders.py --all            # consider all files (not only .html)
  python clean_equal_size_folders.py --min-files 3    # require >=3 files
"""

import argparse
import os
import shutil
from pathlib import Path
from typing import List


def list_subdirectories(root: Path) -> List[Path]:
    return [p for p in root.iterdir() if p.is_dir()]


def collect_file_sizes(folder: Path, html_only: bool) -> List[int]:
    sizes: List[int] = []
    for entry in folder.iterdir():
        if entry.is_file():
            if html_only and entry.suffix.lower() != ".html":
                continue
            try:
                sizes.append(entry.stat().st_size)
            except Exception:
                # Skip files we cannot stat
                continue
    return sizes


def main():
    parser = argparse.ArgumentParser(description="Delete folders where all files have identical sizes.")
    parser.add_argument("--dir", dest="root_dir", default="downloads", help="Root directory containing folders (default: downloads)")
    parser.add_argument("--yes", dest="confirm", action="store_true", help="Actually delete matching folders (default: dry-run)")
    parser.add_argument("--all", dest="all_files", action="store_true", help="Consider all files, not only .html")
    parser.add_argument("--min-files", dest="min_files", type=int, default=2, help="Minimum number of files required to consider deletion (default: 2)")
    args = parser.parse_args()

    root = Path(args.root_dir)
    if not root.exists() or not root.is_dir():
        print(f"❌ Root directory not found or not a directory: {root}")
        return 1

    html_only = not args.all_files
    subdirs = list_subdirectories(root)

    print(f"📂 Scanning: {root}")
    print(f"🔎 Mode: {'ALL files' if not html_only else 'HTML (.html) files only'} | Min files: {args.min_files} | {'DELETE' if args.confirm else 'DRY-RUN'}")

    to_delete: List[Path] = []
    inspected = 0

    for folder in sorted(subdirs):
        inspected += 1
        sizes = collect_file_sizes(folder, html_only=html_only)

        if len(sizes) < args.min_files:
            print(f"- {folder.name}: skip (files considered: {len(sizes)})")
            continue

        unique_sizes = set(sizes)
        if len(unique_sizes) == 1:
            only_size = next(iter(unique_sizes))
            print(f"✅ {folder.name}: all files have identical size ({only_size} bytes) -> marked for deletion")
            to_delete.append(folder)
        else:
            print(f"- {folder.name}: {len(unique_sizes)} different sizes -> keep")

    print("\n📊 Summary")
    print(f"Inspected folders: {inspected}")
    print(f"Folders to delete: {len(to_delete)}")

    if not to_delete:
        print("Nothing to delete.")
        return 0

    if not args.confirm:
        print("\nDry-run complete. Re-run with --yes to delete the folders above.")
        return 0

    # Proceed with deletion
    deleted = 0
    for folder in to_delete:
        try:
            shutil.rmtree(folder)
            print(f"🗑️  Deleted: {folder}")
            deleted += 1
        except Exception as e:
            print(f"❌ Failed to delete {folder}: {e}")

    print(f"\n✅ Done. Deleted {deleted}/{len(to_delete)} folders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


