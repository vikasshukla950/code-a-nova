# File Organizer Automation Tool (Level 1a)

## What it does
Scans a folder, detects each file's type by extension and moves it into a named folder (Images, Videos, Documents, ...).

## Features
- Detects file types and sorts into category folders
- Handles duplicate file names (`report.pdf` -> `report_1.pdf`)
- Logs every move to `organizer_log.csv`
- `--undo` restores files using the log
- Custom categories via a JSON file (see `my_categories.example.json`)
- `--dry-run` preview and `--recursive` sub-folder scan
- Error handling for permission/OS errors

## How to run
```
python file_organizer.py <folder_path>
python file_organizer.py <folder_path> --dry-run
python file_organizer.py <folder_path> --categories my_categories.example.json
python file_organizer.py <folder_path> --undo
```

## Example output
```
a.jpg  ->  Images/a.jpg
c.pdf  ->  Documents/c_1.pdf
song.mp3  ->  Audio/song.mp3

Done: 3 file(s) moved, 0 error(s).
```

## Concepts used
File handling, directory operations, error handling, automation, `argparse`, `pathlib`, `shutil`.
