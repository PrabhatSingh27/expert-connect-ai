"""Authenticated issue-media streaming endpoint."""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_account, get_db
from app.services.secure_media_service import get_authorized_issue_media, media_content_type


router = APIRouter(prefix="/api/issues", tags=["Issue Media"])


@router.get("/{issue_id}/media/{filename}")
def serve_issue_media(
    issue_id: int,
    filename: str,
    account: dict = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Stream an issue attachment after role- and issue-scoped authorization."""
    _, attachment, local_path = get_authorized_issue_media(
        db,
        issue_id=issue_id,
        filename=filename,
        account=account,
    )

    content_type = media_content_type(local_path)
    if attachment and getattr(attachment, "content_type", None) in {"audio/webm", "video/webm"}:
        content_type = attachment.content_type

    return FileResponse(
        path=local_path,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
