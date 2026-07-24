from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.utils.file_handler import save_file


def _upload(filename: str, content_type: str, content: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers=Headers({"content-type": content_type}),
    )


class FileHandlerTests(TestCase):
    def test_save_file_validates_and_returns_a_uuid_storage_path(self):
        with TemporaryDirectory() as directory:
            with patch("app.utils.file_handler.BASE_UPLOAD_DIR", directory):
                result = save_file(_upload("photo.png", "image/png", b"image-bytes"), "image")

            stored_path = Path(result["path"])
            self.assertTrue(stored_path.is_file())
            self.assertEqual(stored_path.read_bytes(), b"image-bytes")
            self.assertEqual(result["original_filename"], "photo.png")
            self.assertNotEqual(result["stored_filename"], "photo.png")

    def test_save_file_rejects_the_wrong_media_type(self):
        with self.assertRaises(HTTPException) as error:
            save_file(_upload("photo.png", "audio/mpeg", b"audio"), "image")

        self.assertEqual(error.exception.status_code, 400)

    def test_save_file_reuses_an_identical_upload(self):
        with TemporaryDirectory() as directory:
            with patch("app.utils.file_handler.BASE_UPLOAD_DIR", directory):
                first = save_file(_upload("a.png", "image/png", b"same-image"), "image")
                second = save_file(_upload("b.png", "image/png", b"same-image"), "image")

        self.assertEqual(first["path"], second["path"])
