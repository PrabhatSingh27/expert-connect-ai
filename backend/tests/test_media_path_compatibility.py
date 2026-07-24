from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app.services.secure_media_service import _resolve_upload_path


class MediaPathCompatibilityTests(TestCase):
    def test_old_issue_path_resolves_to_renamed_issue_media_location(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            migrated = root / "users" / "issues" / "images" / "asset.jpg"
            migrated.parent.mkdir(parents=True)
            migrated.write_bytes(b"image")

            with patch("app.services.secure_media_service.UPLOAD_ROOT", root):
                resolved = _resolve_upload_path(str(root / "issues" / "7" / "images" / "asset.jpg"))

        self.assertEqual(resolved.name, "asset.jpg")
        self.assertEqual(resolved.parent.name, "images")
