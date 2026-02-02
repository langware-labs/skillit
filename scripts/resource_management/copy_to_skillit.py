import shutil
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent
DEST_DIR = Path("/Users/shlom/Documents/dev/skillit/scripts")


def main() -> None:
    if not DEST_DIR.exists() or not DEST_DIR.is_dir():
        raise SystemExit(f"Destination folder does not exist: {DEST_DIR}")

    target = DEST_DIR / "resource_management"
    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(SOURCE_DIR, target)


if __name__ == "__main__":
    main()
