# src/logic.py
import shutil
from pathlib import Path
from src import data

def scan_directory(directory: Path, extension: str):
    """Finds files but ignores the output directory."""
    files = []
    for f in directory.iterdir():
        if f.is_file() and f.suffix.lower() == f".{extension.lower()}":
            files.append(f)
        elif f.is_dir() and f.name in data.IGNORE_FOLDERS:
            continue
    return files

def organize_files(files: list[Path], base_dir: Path):
    """Moves files and returns the move count."""
    output_dir = base_dir / data.DEFAULT_OUTPUT_FOLDER
    output_dir.mkdir(exist_ok=True)
    
    for f in files:
        shutil.move(str(f), str(output_dir / f.name))
    return len(files)