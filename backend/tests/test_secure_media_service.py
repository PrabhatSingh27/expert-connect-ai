from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException

from app.services.secure_media_service import get_authorized_issue_media


class _Query:
    def __init__(self, item):
        self.item = item

    def filter(self, *_conditions):
        return self

    def first(self):
        return self.item

    def all(self):
        return [self.item] if self.item is not None else []


class _Database:
    def __init__(self, issue, attachment):
        self.issue = issue
        self.attachment = attachment
        self.calls = 0

    def query(self, *_models):
        self.calls += 1
        return _Query(self.issue if self.calls == 1 else self.attachment)


class SecureMediaServiceTests(TestCase):
    def setUp(self):
        self.issue = SimpleNamespace(
            id=8,
            customer_id=2,
            assigned_expert_id=9,
            image_path=None,
            video_path=None,
            audio_path=None,
        )
        self.attachment = SimpleNamespace(file_url="uploads/issues/8/images/photo.png")

    def test_customer_can_access_own_issue_media(self):
        db = _Database(self.issue, self.attachment)
        with patch("app.services.secure_media_service._resolve_upload_path", return_value=Path("photo.png")), patch.object(Path, "is_file", return_value=True):
            _, attachment, path = get_authorized_issue_media(
                db,
                issue_id=8,
                filename="photo.png",
                account={"role": "customer", "user_id": 2},
            )
        self.assertIs(attachment, self.attachment)
        self.assertEqual(path.name, "photo.png")

    def test_unrelated_customer_is_forbidden_before_media_lookup(self):
        db = _Database(self.issue, self.attachment)
        with self.assertRaises(HTTPException) as error:
            get_authorized_issue_media(
                db,
                issue_id=8,
                filename="photo.png",
                account={"role": "customer", "user_id": 3},
            )
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(db.calls, 1)

    def test_path_traversal_is_not_a_valid_media_name(self):
        db = _Database(self.issue, self.attachment)
        with self.assertRaises(HTTPException) as error:
            get_authorized_issue_media(
                db,
                issue_id=8,
                filename="../secrets.txt",
                account={"role": "admin"},
            )
        self.assertEqual(error.exception.status_code, 404)
