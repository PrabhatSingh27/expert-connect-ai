from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from fastapi import UploadFile
from starlette.datastructures import Headers

from app.services.file_storage_service import save_issue_attachment


class _AttachmentDatabase:
    def add(self, _attachment):
        pass


class IssueMediaStorageTests(TestCase):
    def test_issue_attachment_uses_the_new_issue_media_tree(self):
        with TemporaryDirectory() as directory:
            upload = UploadFile(
                filename="leak.jpg",
                file=__import__("io").BytesIO(b"image-bytes"),
                headers=Headers({"content-type": "image/jpeg"}),
            )
            issue = SimpleNamespace(id=7, image_path=None, video_path=None, audio_path=None)
            with patch("app.services.file_storage_service.BASE_UPLOAD_DIR", Path(directory)):
                attachment = save_issue_attachment(_AttachmentDatabase(), issue, upload, "image")

            stored_path = Path(attachment.file_url)
            self.assertTrue(stored_path.is_file())
            self.assertEqual(stored_path.parent.name, "images")
            self.assertEqual(stored_path.parent.parent.name, "issues")
            self.assertEqual(stored_path.parent.parent.parent.name, "users")
