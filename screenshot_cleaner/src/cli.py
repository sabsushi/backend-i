import typer
from pathlib import Path
from src import logic, data

# We create the app instance
app = typer.Typer(help="The Professional Screenshot Organizer")

# By adding no sub-command, this becomes the primary action
@app.callback(invoke_without_command=True)
def main(
    path: Path = typer.Argument(
        Path("."), 
        help="Target folder to clean",
        show_default=True
    ),
    ext: str = typer.Option(
        "png", 
        "--ext", 
        "-e", 
        help="Extension to target"
    ),
    dry_run: bool = typer.Option(
        False, 
        "--dry-run", 
        help="Preview changes without moving files"
    )
):
    """Scan and move files to a clean sub-folder."""
    files = logic.scan_directory(path, ext)
    
    if not files:
        typer.secho(" Folder is already pristine!", fg=typer.colors.GREEN)
        return

    typer.echo(f" Found {len(files)} {ext} files in {path.resolve()}")
    
    if dry_run:
        typer.secho(" DRY RUN: No files were moved.", fg=typer.colors.CYAN)
        for f in files:
            typer.echo(f"  -> Would move: {f.name}")
    else:
        count = logic.organize_files(files, path)
        typer.secho(f" Success! {count} screenshots moved to '{data.DEFAULT_OUTPUT_FOLDER}'.", fg=typer.colors.GREEN, bold=True)

if __name__ == "__main__":
    app()