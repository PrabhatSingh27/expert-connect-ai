# app/services/file_storage_service.py

import os
import uuid
from hashlib import sha256
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.models.issue_attachment import IssueAttachment


# ============================================================
# BASE UPLOAD DIRECTORY
# ============================================================

BASE_UPLOAD_DIR = Path("uploads")
ISSUE_MEDIA_DIR = BASE_UPLOAD_DIR / "users" / "issues"


# ============================================================
# ALLOWED FILE CONFIGURATION
# ============================================================

ALLOWED_FILES = {
    "image": {
        "folder": "images",
        "mime_prefix": "image/",
        "extensions": {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
        },
        "max_size": 2 * 1024 * 1024,  # 2 MB
    },

    "video": {
        "folder": "videos",
        "mime_prefix": "video/",
        "extensions": {
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".webm",
        },
        "max_size": 5 * 1024 * 1024,  # 5 MB
    },

    "audio": {
        "folder": "audios",
        "mime_prefix": "audio/",
        "extensions": {
            ".mp3",
            ".wav",
            ".aac",
            ".ogg",
            ".m4a",
            ".webm",
        },
        "max_size": 2 * 1024 * 1024,  # 2 MB
    },

    "document": {
        "folder": "documents",
        "mime_prefix": "",
        "extensions": {".pdf", ".txt", ".doc", ".docx"},
        "max_size": 10 * 1024 * 1024,
    },
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _has_upload(file: Optional[UploadFile]) -> bool:
    """
    Check whether a valid file was actually uploaded.
    """

    return bool(
        file
        and file.filename
        and file.filename.strip()
    )


def _get_extension(file: UploadFile) -> str:
    """
    Get file extension from original filename.
    """

    filename = file.filename or ""

    return Path(filename).suffix.lower()


def _get_file_size(file: UploadFile) -> int:
    """
    Get file size in bytes.

    The file pointer is reset to the beginning
    after checking the size.
    """

    file.file.seek(0, os.SEEK_END)

    file_size = file.file.tell()

    file.file.seek(0)

    return file_size


def _upload_digest(file: UploadFile) -> str:
    """Hash an upload without consuming it for the subsequent save."""
    digest = sha256()
    file.file.seek(0)
    while chunk := file.file.read(1024 * 1024):
        digest.update(chunk)
    file.file.seek(0)
    return digest.hexdigest()


def _file_digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as saved_file:
        while chunk := saved_file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _identical_file_in(directory: Path, content_digest: str) -> Path | None:
    """Find the same content in one managed storage directory."""
    if not directory.is_dir():
        return None
    for candidate in directory.iterdir():
        if candidate.is_file() and candidate.name != ".gitkeep":
            try:
                if _file_digest(candidate) == content_digest:
                    return candidate
            except OSError:
                # An unrelated corrupt/deleted file must not prevent uploads.
                continue
    return None


# ============================================================
# INFER FILE TYPE
# ============================================================

def infer_file_type(file: UploadFile) -> str:
    """
    Detect file type using MIME type.
    """

    content_type = file.content_type or ""

    if content_type.startswith("image/"):
        return "image"

    if content_type.startswith("video/"):
        return "video"

    if content_type.startswith("audio/"):
        return "audio"

    raise HTTPException(
        status_code=415,
        detail=(
            f"Unsupported file type: {content_type or 'unknown'}"
        ),
    )


# ============================================================
# VALIDATE FILE
# ============================================================

def validate_file(
    file: UploadFile,
    file_type: str,
) -> int:
    """
    Validate:

    1. File type
    2. MIME type
    3. File extension
    4. Empty file
    5. Maximum file size

    Returns:
        File size in bytes
    """

    if file_type not in ALLOWED_FILES:

        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file category: {file_type}",
        )

    config = ALLOWED_FILES[file_type]

    # --------------------------------------------------------
    # MIME TYPE VALIDATION
    # --------------------------------------------------------

    content_type = file.content_type or ""

    if not content_type.startswith(
        config["mime_prefix"]
    ):

        raise HTTPException(
            status_code=415,
            detail=(
                f"Only {file_type} files are allowed."
            ),
        )

    # --------------------------------------------------------
    # EXTENSION VALIDATION
    # --------------------------------------------------------

    extension = _get_extension(file)

    if not extension:

        raise HTTPException(
            status_code=400,
            detail=(
                f"{file_type.capitalize()} file "
                "must have a valid extension."
            ),
        )

    if extension not in config["extensions"]:

        allowed_formats = ", ".join(
            sorted(config["extensions"])
        )

        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported {file_type} format. "
                f"Allowed formats: {allowed_formats}"
            ),
        )

    # --------------------------------------------------------
    # FILE SIZE VALIDATION
    # --------------------------------------------------------

    file_size = _get_file_size(file)

    if file_size == 0:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if file_size > config["max_size"]:

        max_size_mb = (
            config["max_size"]
            // (1024 * 1024)
        )

        raise HTTPException(
            status_code=413,
            detail=(
                f"{file_type.capitalize()} files "
                f"must not exceed "
                f"{max_size_mb} MB."
            ),
        )

    return file_size


# ============================================================
# VALIDATE ALL MEDIA FILES
# ============================================================

def validate_single_issue_media_uploads(
    image: Optional[UploadFile] = None,
    video: Optional[UploadFile] = None,
    audio: Optional[UploadFile] = None,
) -> dict:

    if _has_upload(image):

        validate_file(
            image,
            "image",
        )

    else:

        image = None

    if _has_upload(video):

        validate_file(
            video,
            "video",
        )

    else:

        video = None

    if _has_upload(audio):

        validate_file(
            audio,
            "audio",
        )

    else:

        audio = None

    return {
        "image": image,
        "video": video,
        "audio": audio,
    }


# ============================================================
# SAVE GENERIC UPLOAD FILE
# ============================================================

def save_upload_file(
    upload_file: Optional[UploadFile],
    folder: str = "general",
    *,
    file_type: Optional[str] = None,
    include_media_subfolder: bool = True,
) -> Optional[str]:

    if not _has_upload(upload_file):

        return None

    file_type = file_type or infer_file_type(upload_file)

    validate_file(
        upload_file,
        file_type,
    )

    config = ALLOWED_FILES[file_type]

    upload_dir = BASE_UPLOAD_DIR / folder
    if include_media_subfolder:
        upload_dir = upload_dir / config["folder"]

    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_file = _identical_file_in(upload_dir, _upload_digest(upload_file))
    if existing_file is not None:
        return str(existing_file)

    extension = _get_extension(
        upload_file
    )

    stored_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = (
        upload_dir
        / stored_filename
    )

    try:

        upload_file.file.seek(0)

        with file_path.open("wb") as buffer:

            while True:

                chunk = upload_file.file.read(
                    1024 * 1024
                )

                if not chunk:

                    break

                buffer.write(chunk)

    except Exception as error:

        if file_path.exists():

            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save file: {str(error)}"
            ),
        )

    return str(file_path)


# ============================================================
# SAVE ISSUE ATTACHMENT
# ============================================================

def save_issue_attachment(
    db: Session,
    issue: Issue,
    file: UploadFile,
    file_type: Optional[str] = None,
) -> IssueAttachment:

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if not _has_upload(file):

        raise HTTPException(
            status_code=400,
            detail="No file was uploaded.",
        )

    # --------------------------------------------------------
    # DETECT FILE TYPE
    # --------------------------------------------------------

    if file_type is None:

        file_type = infer_file_type(
            file
        )

    # --------------------------------------------------------
    # VALIDATE FILE
    # --------------------------------------------------------

    file_size = validate_file(
        file,
        file_type,
    )

    config = ALLOWED_FILES[file_type]

    # --------------------------------------------------------
    # CREATE DIRECTORY
    # --------------------------------------------------------

    # Issue media now has one dedicated, flat UUID-based storage tree.  The
    # UUID filename already prevents collisions, so an issue-ID subdirectory
    # is unnecessary and would recreate the removed uploads/issues layout.
    upload_dir = ISSUE_MEDIA_DIR / config["folder"]

    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    upload_digest = _upload_digest(file)
    # Prevent duplicate attachment records when an issue edit or client retry
    # submits exactly the same media again.  Scope this to one issue so media
    # deletion for another issue can never affect it.
    for existing_attachment in getattr(issue, "attachments", []) or []:
        existing_path = Path(existing_attachment.file_url)
        if not existing_path.is_absolute():
            existing_path = (Path.cwd() / existing_path).resolve()
        try:
            if existing_path.is_file() and _file_digest(existing_path) == upload_digest:
                return existing_attachment
        except OSError:
            continue

    # --------------------------------------------------------
    # UNIQUE FILE NAME
    # --------------------------------------------------------

    extension = _get_extension(
        file
    )

    stored_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    local_path = (
        upload_dir
        / stored_filename
    )

    # --------------------------------------------------------
    # SAVE FILE
    # --------------------------------------------------------

    try:

        file.file.seek(0)

        with local_path.open("wb") as buffer:

            while True:

                chunk = file.file.read(
                    1024 * 1024
                )

                if not chunk:

                    break

                buffer.write(chunk)

    except Exception as error:

        if local_path.exists():

            local_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save uploaded file: "
                f"{str(error)}"
            ),
        )

    # --------------------------------------------------------
    # LOCAL FILE URL
    # --------------------------------------------------------

    file_url = str(
        local_path
    ).replace("\\", "/")

    # --------------------------------------------------------
    # CREATE DATABASE ATTACHMENT
    # --------------------------------------------------------

    attachment = IssueAttachment(

        issue_id=issue.id,

        file_url=file_url,

        file_type=file_type,

        original_filename=file.filename,

        content_type=file.content_type,

        file_size=file_size,

        size_bytes=file_size,

        storage_provider="local",

    )

    db.add(
        attachment
    )

    # --------------------------------------------------------
    # UPDATE ISSUE FILE PATH
    # --------------------------------------------------------

    if (
        file_type == "image"
        and not issue.image_path
    ):

        issue.image_path = file_url

    elif (
        file_type == "video"
        and not issue.video_path
    ):

        issue.video_path = file_url

    elif (
        file_type == "audio"
        and not issue.audio_path
    ):

        issue.audio_path = file_url

    return attachment


# ============================================================
# SAVE ALL ISSUE MEDIA FILES
# ============================================================

def save_issue_media_files(
    db: Session,
    issue: Issue,
    image: Optional[UploadFile] = None,
    video: Optional[UploadFile] = None,
    audio: Optional[UploadFile] = None,
) -> list[IssueAttachment]:

    attachments = []

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if _has_upload(image):

        image_attachment = (
            save_issue_attachment(
                db=db,
                issue=issue,
                file=image,
                file_type="image",
            )
        )

        attachments.append(
            image_attachment
        )

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    if _has_upload(video):

        video_attachment = (
            save_issue_attachment(
                db=db,
                issue=issue,
                file=video,
                file_type="video",
            )
        )

        attachments.append(
            video_attachment
        )

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    if _has_upload(audio):

        audio_attachment = (
            save_issue_attachment(
                db=db,
                issue=issue,
                file=audio,
                file_type="audio",
            )
        )

        attachments.append(
            audio_attachment
        )

    return attachments


# ============================================================
# DELETE SINGLE ATTACHMENT
# ============================================================

def delete_attachment_from_storage(
    attachment: IssueAttachment,
) -> None:

    if (
        attachment.storage_provider
        != "local"
    ):

        return

    if not attachment.file_url:

        return

    file_path = Path(
        attachment.file_url
    )

    if (
        file_path.exists()
        and file_path.is_file()
    ):

        file_path.unlink()


# ============================================================
# DELETE ALL ISSUE ATTACHMENTS
# ============================================================

def delete_issue_attachments_from_storage(
    issue: Issue,
) -> None:

    for attachment in issue.attachments:

        delete_attachment_from_storage(
            attachment
        )
