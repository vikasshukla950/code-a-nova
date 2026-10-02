#!/usr/bin/env python3
"""File Organizer Automation Tool (Level 1a)

Scans a directory, detects file types by extension and moves each file into a
category folder (Images, Videos, ...). Features:
  * duplicate file-name handling (report.pdf -> report_1.pdf)
  * log of every move (organizer_log.csv) and an --undo option
  * custom categories via a JSON file
  * --dry-run preview, optional --recursive scan
  * error handling for permission / OS errors

Usage:
  python file_organizer.py ~/Downloads
  python file_organizer.py ~/Downloads --dry-run
  python file_organizer.py ~/Downloads --categories my_categories.json
  python file_organizer.py ~/Downloads --undo
"""
import argparse
import csv
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".heic"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Code": [".py", ".js", ".java", ".c", ".cpp", ".html", ".css", ".json", ".sh"],
    "Installers": [".exe", ".msi", ".dmg", ".apk", ".deb"],
}
OTHERS = "Others"
LOG_NAME = "organizer_log.csv"


def load_categories(path):
    """Return default categories, or those from a user JSON file."""
    if not path:
        return DEFAULT_CATEGORIES
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return {name: [e.lower() if e.startswith(".") else f".{e.lower()}" for e in exts]
                for name, exts in data.items()}
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"Could not read categories file: {exc}")


def category_for(file: Path, categories):
    ext = file.suffix.lower()
    for name, exts in categories.items():
        if ext in exts:
            return name
    return OTHERS


def unique_destination(dest: Path) -> Path:
    """If dest exists, append _1, _2 ... before the extension."""
    if not dest.exists():
        return dest
    counter = 1
    while True:
        candidate = dest.with_name(f"{dest.stem}_{counter}{dest.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def organize(directory: Path, categories, dry_run=False, recursive=False):
    log_path = directory / LOG_NAME
    pattern = directory.rglob("*") if recursive else directory.iterdir()
    category_dirs = set(categories) | {OTHERS}
    moved, errors = [], 0

    for item in sorted(pattern):
        if not item.is_file() or item.name == LOG_NAME or item.name.startswith("."):
            continue
        # don't re-organize files already inside a category folder
        if item.parent != directory and item.parent.name in category_dirs:
            continue
        category = category_for(item, categories)
        target_dir = directory / category
        target = unique_destination(target_dir / item.name)
        try:
            if not dry_run:
                target_dir.mkdir(exist_ok=True)
                shutil.move(str(item), str(target))
            moved.append((datetime.now().isoformat(timespec="seconds"), str(item), str(target)))
            print(f"{'[dry-run] ' if dry_run else ''}{item.name}  ->  {category}/{target.name}")
        except (PermissionError, OSError) as exc:
            errors += 1
            print(f"  ! Could not move {item.name}: {exc}")

    if moved and not dry_run:
        new_file = not log_path.exists()
        with open(log_path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if new_file:
                writer.writerow(["timestamp", "source", "destination"])
            writer.writerows(moved)

    print(f"\nDone: {len(moved)} file(s) {'would be ' if dry_run else ''}moved, {errors} error(s).")
    return moved


def undo(directory: Path):
    """Move files back using the log, then clear the log."""
    log_path = directory / LOG_NAME
    if not log_path.exists():
        sys.exit("No log file found - nothing to undo.")
    with open(log_path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    restored = 0
    for row in reversed(rows):
        src, dst = Path(row["source"]), Path(row["destination"])
        if dst.exists():
            try:
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(unique_destination(src)))
                restored += 1
            except OSError as exc:
                print(f"  ! Could not restore {dst.name}: {exc}")
    for sub in directory.iterdir():  # remove now-empty category folders
        if sub.is_dir() and not any(sub.iterdir()):
            sub.rmdir()
    log_path.unlink()
    print(f"Restored {restored} file(s).")


def main():
    parser = argparse.ArgumentParser(description="Organize a messy folder by file type.")
    parser.add_argument("directory", help="Folder to organize")
    parser.add_argument("--dry-run", action="store_true", help="Preview without moving anything")
    parser.add_argument("--recursive", action="store_true", help="Include sub-folders")
    parser.add_argument("--categories", help="JSON file with custom {category: [extensions]}")
    parser.add_argument("--undo", action="store_true", help="Revert the previous run using the log")
    args = parser.parse_args()

    directory = Path(args.directory).expanduser().resolve()
    if not directory.is_dir():
        sys.exit(f"'{directory}' is not a valid directory.")
    if args.undo:
        undo(directory)
    else:
        organize(directory, load_categories(args.categories), args.dry_run, args.recursive)


if __name__ == "__main__":
    main()
