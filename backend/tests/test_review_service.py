from types import SimpleNamespace
from unittest import TestCase

# Register SQLAlchemy relationship targets before constructing ExpertReview.
import app.models.expert  # noqa: F401
import app.models.user  # noqa: F401
from app.services.review_service import create_review


class _ReviewQuery:
    def __init__(self, value):
        self.value = value

    def filter(self, *_conditions):
        return self

    def first(self):
        return self.value


class _ReviewDatabase:
    def __init__(self, issue, existing_review=None):
        self.issue = issue
        self.existing_review = existing_review
        self.query_count = 0
        self.added = None

    def query(self, *_models):
        self.query_count += 1
        return _ReviewQuery(self.issue if self.query_count == 1 else self.existing_review)

    def add(self, review):
        self.added = review

    def commit(self):
        pass

    def refresh(self, _review):
        pass


class ReviewServiceTests(TestCase):
    def test_customer_can_review_an_in_progress_assigned_issue(self):
        issue = SimpleNamespace(id=2, customer_id=7, assigned_expert_id=5, status="in_progress")
        db = _ReviewDatabase(issue)
        result = create_review(db, 2, 7, SimpleNamespace(rating=5, review="Great work"))

        self.assertIs(result, db.added)
        self.assertEqual(result.expert_id, 5)
        self.assertEqual(result.rating, 5)

    def test_duplicate_review_returns_existing_record(self):
        issue = SimpleNamespace(id=2, customer_id=7, assigned_expert_id=5, status="assigned")
        existing = SimpleNamespace(id=99, issue_id=2, customer_id=7)
        db = _ReviewDatabase(issue, existing_review=existing)

        result = create_review(db, 2, 7, SimpleNamespace(rating=5, review="Great work"))

        self.assertIs(result, existing)
        self.assertIsNone(db.added)
