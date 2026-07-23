"""Authorization and local-path resolution for issue media downloads.

This module deliberately trusts only media records already persisted by the
upload workflow.  The request filename is used as an identifier, never as a
filesystem path.
"""

from pathlib import Path, PurePath

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.models.issue_attachment import IssueAttachment
from app.services.file_storage_service import BASE_UPLOAD_DIR


UPLOAD_ROOT = Path(BASE_UPLOAD_DIR).resolve()

MEDIA_TYPES_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
}


def get_authorized_issue_media(
    db: Session,
    *,
    issue_id: int,
    filename: str,
    account: dict,
) -> tuple[Issue, IssueAttachment | None, Path]:
    """Return an authorized attachment and a safe local path, or raise HTTP errors."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    _ensure_issue_media_access(issue, account)
    _ensure_plain_filename(filename)

    attachments = (
        db.query(IssueAttachment)
        .filter(IssueAttachment.issue_id == issue.id)
        .all()
    )
    attachment = next(
        (
            candidate
            for candidate in attachments
            if Path(candidate.file_url).name == filename
        ),
        None,
    )

    # Older issues may predate issue_attachments. Keep their already-stored
    # image/video/audio fields readable, but only when the requested basename
    # exactly matches one of those fields.
    stored_path = attachment.file_url if attachment else _legacy_media_path(issue, filename)
    if not stored_path:
        raise HTTPException(status_code=404, detail="Media file not found")

    local_path = _resolve_upload_path(stored_path)
    if not local_path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")

    return issue, attachment, local_path


def media_content_type(path: Path) -> str:
    """Return a deterministic media MIME type based on the stored extension."""
    suffix = path.suffix.lower()
    if suffix == ".webm":
        # WebM can be audio or video; the endpoint uses attachment metadata
        # when available to resolve that ambiguity.
        return "video/webm"
    return MEDIA_TYPES_BY_EXTENSION.get(suffix, "application/octet-stream")


def _ensure_issue_media_access(issue: Issue, account: dict) -> None:
    role = str(account.get("role") or "").strip().lower()
    if role in {"admin", "operator"}:
        return
    if role == "customer" and account.get("user_id") == issue.customer_id:
        return
    if role == "expert" and account.get("expert_id") == issue.assigned_expert_id:
        return
    raise HTTPException(status_code=403, detail="Not authorized to access this issue media")


def _ensure_plain_filename(filename: str) -> None:
    requested = PurePath(filename)
    if not filename or requested.name != filename or filename in {".", ".."}:
        # Treat traversal attempts as an unknown media identifier so no
        # filesystem information is revealed.
        raise HTTPException(status_code=404, detail="Media file not found")


def _legacy_media_path(issue: Issue, filename: str) -> str | None:
    for value in (issue.image_path, issue.video_path, issue.audio_path):
        if value and Path(value).name == filename:
            return value
    return None


def _resolve_upload_path(stored_path: str) -> Path:
    candidate = Path(stored_path)
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(UPLOAD_ROOT)
    except ValueError:
        # A database value outside our managed upload root must never be served.
        raise HTTPException(status_code=404, detail="Media file not found")
    return candidate
