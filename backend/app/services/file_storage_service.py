import os
import shutil
import uuid
from pathlib import Path
from mimetypes import guess_extension

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.models.issue_attachment import IssueAttachment


BASE_UPLOAD_DIR = Path("uploads")

ALLOWED_FILES = {
    "image": {
        "folder": "images",
        "mime_prefix": "image/",
        "extensions": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
        "max_size": 10 * 1024 * 1024,
    },
    "video": {
        "folder": "videos",
        "mime_prefix": "video/",
        "extensions": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
        "max_size": 5 * 1024 * 1024,
    },
    "audio": {
        "folder": "audio",
        "mime_prefix": "audio/",
        "extensions": {".mp3", ".wav", ".aac", ".ogg", ".m4a", ".webm"},
        "max_size": 10 * 1024 * 1024,
    },
    "document": {
        "folder": "documents",
        "mime_prefix": "",
        "extensions": {".pdf", ".txt", ".doc", ".docx"},
        "max_size": 10 * 1024 * 1024,
    },
}


DEFAULT_EXTENSIONS = {
    "image": ".jpg",
    "video": ".webm",
    "audio": ".webm",
    "document": ".bin",
}


def infer_file_type(file: UploadFile) -> str:
    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("video/"):
        return "video"
    if content_type.startswith("audio/"):
        return "audio"
    return "document"


def _extension_for_upload(file: UploadFile, file_type: str) -> str:
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension:
        return extension

    guessed_extension = guess_extension(file.content_type or "")
    return guessed_extension or DEFAULT_EXTENSIONS[file_type]


def validate_file(file: UploadFile, file_type: str) -> int:
    config = ALLOWED_FILES[file_type]
    extension = _extension_for_upload(file, file_type)

    if extension not in config["extensions"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported {file_type} format.",
        )

    content_type = file.content_type or ""
    is_audio_blob = file_type == "audio" and content_type in {
        "application/octet-stream",
        "video/webm",
    }

    if config["mime_prefix"] and not content_type.startswith(config["mime_prefix"]) and not is_audio_blob:
        raise HTTPException(
            status_code=400,
            detail=f"Only {file_type} files are allowed.",
        )

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > config["max_size"]:
        max_mb = config["max_size"] // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"{file_type.capitalize()} files must not exceed {max_mb} MB.",
        )

    return file_size


def compress_file_if_possible(file_path: Path, file_type: str) -> None:
    if file_type != "image":
        return

    try:
        from PIL import Image
    except ImportError:
        return

    try:
        with Image.open(file_path) as image:
            image.save(file_path, optimize=True, quality=85)
    except Exception:
        return


def upload_to_cloud_storage(local_path: Path, file_type: str) -> str | None:
    provider = os.getenv("CLOUD_STORAGE_PROVIDER", "").lower()
    if provider not in {"s3", "cloudinary"}:
        return None

    # Hook point for boto3/cloudinary SDK integration.
    return None


def save_upload_file(upload_file: UploadFile | None, folder: str = "general") -> str | None:
    if not upload_file:
        return None

    extension = os.path.splitext(upload_file.filename or "")[1].lower()
    if not extension:
        extension = guess_extension(upload_file.content_type or "") or ".bin"

    upload_dir = BASE_UPLOAD_DIR / folder
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid.uuid4()}{extension}"
    local_path = upload_dir / stored_filename

    with local_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return str(local_path)


def save_issue_attachment(
    db: Session,
    issue: Issue,
    file: UploadFile,
    file_type: str | None = None,
) -> IssueAttachment:
    file_type = file_type or infer_file_type(file)
    file_size = validate_file(file, file_type)
    extension = _extension_for_upload(file, file_type)
    upload_dir = BASE_UPLOAD_DIR / "issues" / str(issue.id) / ALLOWED_FILES[file_type]["folder"]
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid.uuid4()}{extension}"
    local_path = upload_dir / stored_filename

    with local_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    compress_file_if_possible(local_path, file_type)
    cloud_url = upload_to_cloud_storage(local_path, file_type)
    file_url = cloud_url or str(local_path)

    attachment = IssueAttachment(
        issue_id=issue.id,
        file_url=file_url,
        file_type=file_type,
        original_filename=file.filename,
        content_type=file.content_type,
        file_size=file_size,
        size_bytes=file_size,
        storage_provider="cloud" if cloud_url else "local",
    )
    db.add(attachment)

    if file_type == "image" and not issue.image_path:
        issue.image_path = file_url
    elif file_type == "video" and not issue.video_path:
        issue.video_path = file_url
    elif file_type == "audio" and not issue.audio_path:
        issue.audio_path = file_url

    return attachment


def save_issue_attachments(
    db: Session,
    issue: Issue,
    files: list[UploadFile] | None,
    file_type: str | None = None,
) -> list[IssueAttachment]:
    if not files:
        return []

    attachments = []
    for file in files:
        if file:
            attachments.append(save_issue_attachment(db, issue, file, file_type=file_type))

    return attachments


def save_issue_media_groups(
    db: Session,
    issue: Issue,
    image_files: list[UploadFile] | None = None,
    video_files: list[UploadFile] | None = None,
    audio_files: list[UploadFile] | None = None,
    audio_recordings: list[UploadFile] | None = None,
    files: list[UploadFile] | None = None,
) -> list[IssueAttachment]:
    attachments = []
    attachments.extend(save_issue_attachments(db, issue, image_files, file_type="image"))
    attachments.extend(save_issue_attachments(db, issue, video_files, file_type="video"))
    attachments.extend(save_issue_attachments(db, issue, audio_files, file_type="audio"))
    attachments.extend(save_issue_attachments(db, issue, audio_recordings, file_type="audio"))
    attachments.extend(save_issue_attachments(db, issue, files))
    return attachments


def delete_attachment_from_storage(attachment: IssueAttachment) -> None:
    if attachment.storage_provider != "local":
        return

    path = Path(attachment.file_url)
    if path.exists() and path.is_file():
        path.unlink()


def delete_issue_attachments_from_storage(issue: Issue) -> None:
    for attachment in issue.attachments:
        delete_attachment_from_storage(attachment)
