"""Safely initialize and migrate uploads into the normalized hierarchy.

This script never deletes or overwrites an existing file.  Known legacy media
is copied to its new destination with a collision-safe filename, so the old
application can continue to run until the backend path configuration is
switched and the migration is verified.

Run from the backend directory:
    python scripts/initialize_upload_structure.py
"""

from __future__ import annotations

import shutil
from hashlib import sha256
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
UPLOADS_ROOT = BACKEND_ROOT / "uploads"

TERMINAL_DIRECTORIES = (
    "experts/government_id",
    "experts/profile_pic",
    "users/profile_pic",
    "users/issues/images",
    "users/issues/videos",
    "users/issues/audios",
)

# Each legacy source maps to its target terminal directory. Missing sources
# are skipped, which makes the script safe to rerun.
MIGRATION_SOURCES = {
    "experts/government_ids": "experts/government_id",
    "experts/profile_images": "experts/profile_pic",
    "experts/images": "experts/profile_pic",
    "profiles/images": "users/profile_pic",
    "issue_media/images": "users/issues/images",
    "issue_media/videos": "users/issues/videos",
    "issue_media/audio": "users/issues/audios",
    "images": "users/issues/images",
    "videos": "users/issues/videos",
    "audio": "users/issues/audios",
    # Previous issue-specific storage layout.
    "issues": "users/issues",
}


def create_target_structure() -> None:
    """Create every terminal directory and its Git placeholder."""
    for relative_directory in TERMINAL_DIRECTORIES:
        directory = UPLOADS_ROOT / relative_directory
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch(exist_ok=False)


def _unique_destination(directory: Path, filename: str) -> Path:
    """Return a destination that cannot overwrite an existing file."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 1
    while True:
        candidate = directory / f"{stem}__migrated_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _file_digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _already_copied(directory: Path, source: Path) -> bool:
    """Avoid duplicate copies when this safe migration is run again."""
    source_digest = _file_digest(source)
    for candidate in directory.iterdir():
        if candidate.is_file() and candidate.name != ".gitkeep":
            try:
                if _file_digest(candidate) == source_digest:
                    return True
            except OSError:
                continue
    return False


def _copy_files(source: Path, destination: Path) -> int:
    """Copy regular files recursively without altering the source tree."""
    if not source.is_dir():
        return 0

    copied = 0
    for file_path in source.rglob("*"):
        if not file_path.is_file() or file_path.name == ".gitkeep":
            continue
        if _already_copied(destination, file_path):
            continue
        target = _unique_destination(destination, file_path.name)
        shutil.copy2(file_path, target)
        copied += 1
    return copied


def migrate_legacy_media() -> int:
    """Copy known legacy folders into the new structure; return copy count."""
    copied = 0
    for source_relative, target_relative in MIGRATION_SOURCES.items():
        source = UPLOADS_ROOT / source_relative

        # ``uploads/issues/<issue-id>/<media-type>`` needs media-type routing.
        if source_relative == "issues" and source.is_dir():
            target_names = {"images": "images", "videos": "videos", "audio": "audios"}
            for media_directory in source.rglob("*"):
                if media_directory.is_dir() and media_directory.name in target_names:
                    copied += _copy_files(
                        media_directory,
                        UPLOADS_ROOT / "users/issues" / target_names[media_directory.name],
                    )
            continue

        copied += _copy_files(source, UPLOADS_ROOT / target_relative)
    return copied


def main() -> None:
    create_target_structure()
    copied = migrate_legacy_media()
    print(f"Upload structure ready at: {UPLOADS_ROOT}")
    print(f"Copied {copied} legacy file(s); originals were preserved.")
    print("Verify the copied files before removing any legacy folders manually.")


if __name__ == "__main__":
    main()
