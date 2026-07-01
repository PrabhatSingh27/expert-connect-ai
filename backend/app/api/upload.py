import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

BASE_UPLOAD_DIR = "uploads"

ALLOWED_FILES = {
    "image": {
        "folder": "images",
        "mime_prefix": "image/",
        "extensions": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
        "max_size": 10 * 1024 * 1024
    },
    "video": {
        "folder": "videos",
        "mime_prefix": "video/",
        "extensions": {".mp4", ".mov", ".avi", ".mkv"},
        "max_size": 5 * 1024 * 1024
    },
    "audio": {
        "folder": "audio",
        "mime_prefix": "audio/",
        "extensions": {".mp3", ".wav", ".aac", ".ogg", ".m4a"},
        "max_size": 10 * 1024 * 1024
    }
}


def save_file(file: UploadFile, file_type: str):
    config = ALLOWED_FILES[file_type]

    if not file.content_type.startswith(config["mime_prefix"]):
        raise HTTPException(
            status_code=400,
            detail=f"Only {file_type} files are allowed."
        )

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in config["extensions"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported {file_type} format."
        )
    
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > config["max_size"]:
        raise HTTPException(
            status_code=400,
            detail=f"{file_type.capitalize()} files must not exceed {config['max_size'] // (1024 * 1024)} MB."
        )

    upload_dir = os.path.join(BASE_UPLOAD_DIR, config["folder"])
    os.makedirs(upload_dir, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": f"{file_type.capitalize()} uploaded successfully.",
        "original_filename": file.filename,
        "stored_filename": unique_filename,
        "content_type": file.content_type,
        "path": file_path
    }


@router.post("/image")
def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    return save_file(file, "image")


@router.post("/video")
def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    return save_file(file, "video")


@router.post("/audio")
def upload_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    return save_file(file, "audio")