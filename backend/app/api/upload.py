from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.file_storage_service import save_upload_file
from app.utils.file_validator import validate_upload_file


router = APIRouter(prefix="/upload", tags=["Uploads"])


@router.post("/image")
async def upload_image(
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
):
    """Compatibility endpoint for multipart image uploads from the frontend."""
    upload = file or image
    if upload is None or not (upload.filename or upload.content_type):
        raise HTTPException(status_code=422, detail="An image file is required")

    await validate_upload_file(upload, "image")
    return {"profile_image_url": save_upload_file(upload, folder="profiles")}


@router.post("/video")
async def upload_video(
    file: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
):
    """Compatibility endpoint for standalone multipart video uploads."""
    upload = file or video
    if upload is None or not (upload.filename or upload.content_type):
        raise HTTPException(status_code=422, detail="A video file is required")

    await validate_upload_file(upload, "video")
    return {"video_path": save_upload_file(upload, folder="videos")}


@router.post("/audio")
async def upload_audio(
    file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
):
    """Compatibility endpoint for standalone multipart audio uploads."""
    upload = file or audio
    if upload is None or not (upload.filename or upload.content_type):
        raise HTTPException(status_code=422, detail="An audio file is required")

    await validate_upload_file(upload, "audio")
    return {"audio_path": save_upload_file(upload, folder="audio")}
