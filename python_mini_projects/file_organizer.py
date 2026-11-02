#!/usr/bin/env python3
"""
File Organizer Script  (Level 1a)
---------------------------------
Scans a folder, detects each file's type, and moves it into a
categorized sub-folder (Images, Documents, Videos, ...).

Usage:
    python file_organizer.py                      # asks which folder to organize
    python file_organizer.py ~/Downloads          # organize a folder
    python file_organizer.py ~/Downloads --dry-run  # preview only, nothing moves
"""

import argparse
import mimetypes
import shutil
import sys
from collections import defaultdict
from pathlib import Path

# Extension -> category lookup. Edit freely to suit your needs.
CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
               ".tiff", ".tif", ".ico", ".heic", ".raw"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md",
                  ".xls", ".xlsx", ".csv", ".ppt", ".pptx", ".odp", ".ods"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp",
             ".h", ".json", ".xml", ".sh", ".sql", ".yml", ".yaml"},
    "Installers": {".exe", ".msi", ".dmg", ".pkg", ".deb", ".apk"},
}
FALLBACK_CATEGORY = "Others"

# Used only when an extension isn't in CATEGORIES (e.g. ".jfif").
MIME_PREFIX_TO_CATEGORY = {"image": "Images", "video": "Videos", "audio": "Audio"}


def detect_category(file_path: Path) -> str:
    """Return the category folder name for a file."""
    ext = file_path.suffix.lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category

    # Fallback: ask the mimetypes database (image/*, video/*, audio/*).
    mime, _ = mimetypes.guess_type(file_path.name)
    if mime:
        return MIME_PREFIX_TO_CATEGORY.get(mime.split("/")[0], FALLBACK_CATEGORY)
    return FALLBACK_CATEGORY


def unique_destination(destination: Path) -> Path:
    """If destination exists, return 'name (1).ext', 'name (2).ext', ... instead."""
    if not destination.exists():
        return destination
    counter = 1
    while True:
        candidate = destination.with_name(f"{destination.stem} ({counter}){destination.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def scan_directory(directory: Path) -> list[Path]:
    """List regular, non-hidden files directly inside `directory`."""
    this_script = Path(__file__).resolve()
    return sorted(
        item for item in directory.iterdir()
        if item.is_file()
        and not item.name.startswith(".")
        and item.resolve() != this_script
    )


def organize(directory: Path, dry_run: bool = False) -> dict[str, int]:
    """Move every file in `directory` into its category folder. Returns counts."""
    counts: dict[str, int] = defaultdict(int)
    files = scan_directory(directory)

    if not files:
        print("No files to organize.")
        return counts

    for file_path in files:
        category = detect_category(file_path)
        target_dir = directory / category
        destination = unique_destination(target_dir / file_path.name)

        label = "[DRY RUN] " if dry_run else ""
        print(f"{label}{file_path.name}  ->  {category}/{destination.name}")

        if not dry_run:
            try:
                target_dir.mkdir(exist_ok=True)
                shutil.move(str(file_path), str(destination))
            except (OSError, shutil.Error) as err:
                print(f"  ! Could not move {file_path.name}: {err}")
                continue
        counts[category] += 1

    return counts


def print_summary(counts: dict[str, int], dry_run: bool) -> None:
    if not counts:
        return
    verb = "would be moved" if dry_run else "moved"
    print("\nSummary")
    print("-" * 28)
    for category, number in sorted(counts.items()):
        print(f"{category:<14}{number:>4} file(s)")
    print("-" * 28)
    print(f"{'Total':<14}{sum(counts.values()):>4} file(s) {verb}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Organize files into folders by file type.")
    parser.add_argument("directory", nargs="?", help="Folder to organize")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without moving anything")
    args = parser.parse_args()

    raw_path = args.directory or input("Folder to organize: ").strip().strip('"').strip("'")
    directory = Path(raw_path).expanduser().resolve()

    if not directory.is_dir():
        print(f"Error: '{directory}' is not a valid folder.")
        return 1

    print(f"Organizing: {directory}\n")
    counts = organize(directory, dry_run=args.dry_run)
    print_summary(counts, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
