from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

# Register all SQLAlchemy relationship targets before constructing Issue in
# isolated service tests, as application startup normally does this for us.
import app.models.availability  # noqa: F401
import app.models.chat_message  # noqa: F401
import app.models.expert  # noqa: F401
import app.models.expert_review  # noqa: F401
import app.models.issue_attachment  # noqa: F401
from app.auth.dependencies import get_current_operator
from app.schemas.operator import OperatorIssueUpdate
from app.services.issue_service import create_issue
from app.services.operator_service import override_issue_decisions


class _IssueDatabase:
    def add(self, _issue):
        pass

    def flush(self):
        # The service needs the persisted identifier before file storage.
        self.issue.id = 101

    def commit(self):
        pass

    def refresh(self, _issue):
        pass


class _OperatorQuery:
    def __init__(self, expert):
        self.expert = expert

    def filter(self, *_args):
        return self

    def first(self):
        return self.expert


class _OperatorDatabase:
    def __init__(self, expert):
        self.expert = expert
        self.committed = False

    def query(self, *_args):
        return _OperatorQuery(self.expert)

    def commit(self):
        self.committed = True

    def refresh(self, _issue):
        pass

    def rollback(self):
        pass


def _issue_data():
    return SimpleNamespace(
        title="AC leaking",
        description="Water is leaking from the AC",
        problem_type=None,
        category=None,
        priority=None,
        urgency=None,
        required_skills=None,
        preferred_visit_date=None,
        preferred_time=None,
        location=None,
        pin_code=None,
        address=None,
        image_path=None,
        video_path=None,
        audio_path=None,
    )


class IssueWorkflowTests(TestCase):
    def test_create_issue_classifies_then_assigns_an_eligible_expert(self):
        db = _IssueDatabase()
        expert = SimpleNamespace(id=12)
        classification = {
            "problem_type": "Air Conditioner",
            "category": "Electrical",
            "priority": "high",
            "urgency": "high",
            "required_skills": ["electrician"],
            "confidence_score": 0.91,
            "ai_explanation": "AC leak requires electrical service.",
        }

        def assign(issue, _db, *, commit):
            self.assertFalse(commit)
            issue.assigned_expert_id = expert.id
            issue.status = "assigned"
            return expert

        with (
            patch("app.services.issue_service.save_issue_media_files"),
            patch("app.services.issue_service.classify_issue_content", return_value=classification),
            patch("app.services.issue_service.assign_best_expert_to_issue", side_effect=assign),
            patch("app.services.issue_service.notify_expert_assigned"),
            patch("app.services.issue_service.publish_issue_update"),
        ):
            original_add = db.add

            def add(issue):
                db.issue = issue
                original_add(issue)

            db.add = add
            issue = create_issue(db, 1, _issue_data())

        self.assertEqual(issue.category, "Electrical")
        self.assertEqual(issue.priority, "high")
        self.assertEqual(issue.assigned_expert_id, expert.id)
        self.assertEqual(issue.status, "assigned")

    def test_create_issue_waits_for_operator_when_no_expert_is_eligible(self):
        db = _IssueDatabase()
        classification = {
            "problem_type": "Air Conditioner",
            "category": "Electrical",
            "priority": "high",
            "urgency": "high",
            "required_skills": ["electrician"],
            "confidence_score": 0.91,
            "ai_explanation": "AC leak requires electrical service.",
        }

        with (
            patch("app.services.issue_service.save_issue_media_files"),
            patch("app.services.issue_service.classify_issue_content", return_value=classification),
            patch("app.services.issue_service.assign_best_expert_to_issue", return_value=None),
            patch("app.services.issue_service.publish_issue_update"),
        ):
            original_add = db.add

            def add(issue):
                db.issue = issue
                original_add(issue)

            db.add = add
            issue = create_issue(db, 1, _issue_data())

        self.assertEqual(issue.status, "waiting_for_assignment")


class OperatorOverrideTests(TestCase):
    def test_operator_can_override_triage_and_assign_an_eligible_expert(self):
        issue = SimpleNamespace(
            id=8,
            problem_type="General",
            category="General",
            priority="low",
            urgency="low",
            operator_note=None,
            assigned_expert_id=None,
            assigned_at=None,
            status="waiting_for_assignment",
        )
        expert = SimpleNamespace(id=9, is_active=True, is_verified=True)
        db = _OperatorDatabase(expert)
        update = OperatorIssueUpdate(
            problem_type="Air Conditioner",
            category="Electrical",
            priority="high",
            urgency="high",
            assigned_expert_id=9,
            operator_note="Verified after reviewing uploaded image.",
        )

        with (
            patch("app.services.operator_service.get_operator_issue", return_value=issue),
            patch("app.services.operator_service.eligible_experts_for_issue", return_value=[{"expert": expert}]),
            patch("app.services.operator_service.publish_issue_update"),
        ):
            result = override_issue_decisions(db, issue.id, update)

        self.assertIs(result, issue)
        self.assertEqual(issue.category, "Electrical")
        self.assertEqual(issue.priority, "high")
        self.assertEqual(issue.assigned_expert_id, expert.id)
        self.assertEqual(issue.status, "assigned")
        self.assertTrue(db.committed)

    def test_operator_cannot_assign_an_inactive_or_unverified_expert(self):
        issue = SimpleNamespace(id=8, assigned_expert_id=None)
        expert = SimpleNamespace(id=9, is_active=False, is_verified=False)
        db = _OperatorDatabase(expert)

        with patch("app.services.operator_service.get_operator_issue", return_value=issue):
            with self.assertRaises(HTTPException) as error:
                override_issue_decisions(db, issue.id, OperatorIssueUpdate(assigned_expert_id=9))

        self.assertEqual(error.exception.status_code, 400)

    def test_operator_payload_rejects_invalid_priority(self):
        with self.assertRaises(ValidationError):
            OperatorIssueUpdate(priority="immediate")

    def test_customer_cannot_satisfy_operator_dependency(self):
        with self.assertRaises(HTTPException) as error:
            get_current_operator(SimpleNamespace(role="customer"))

        self.assertEqual(error.exception.status_code, 403)
