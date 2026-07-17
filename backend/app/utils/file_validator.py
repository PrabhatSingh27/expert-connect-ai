from fastapi import HTTPException, UploadFile


FILE_LIMITS = {
    "image": 10 * 1024 * 1024,
    "video": 5 * 1024 * 1024,
    "audio": 10 * 1024 * 1024,
    "document": 10 * 1024 * 1024,
}


def _is_allowed_content_type(content_type: str, expected_type: str) -> bool:
    if expected_type == "document":
        return content_type == "application/pdf" or content_type.startswith("image/")
    return content_type.startswith(f"{expected_type}/")


async def validate_upload_file(file: UploadFile, expected_type: str) -> int:
    """Validate an uploaded file's MIME type and size, then reset its stream."""
    if expected_type not in FILE_LIMITS:
        raise ValueError(f"Unsupported expected file type: {expected_type}")

    content_type = file.content_type or ""
    if not _is_allowed_content_type(content_type, expected_type):
        allowed = "application/pdf or image/*" if expected_type == "document" else f"{expected_type}/*"
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type. Expected {allowed}.",
        )

    content = await file.read()
    try:
        file_size = len(content)
        max_size = FILE_LIMITS[expected_type]
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"{expected_type.capitalize()} files must not exceed {max_size // (1024 * 1024)} MB.",
            )
        return file_size
    finally:
        await file.seek(0)
