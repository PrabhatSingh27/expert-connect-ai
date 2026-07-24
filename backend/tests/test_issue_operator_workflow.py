from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

# Register all SQLAlchemy relationship targets before constructing Issue in
# isolated service tests, as application startup normally does this for us.
import app.models.availability  # noqa: F401
import app.models.chat_message  # noqa: F401
import app.models.expert  # noqa: F401
import app.models.expert_review  # noqa: F401
import app.models.issue_attachment  # noqa: F401
from app.models.issue import Issue
from app.auth.dependencies import get_current_operator, get_current_user
from app.schemas.operator import OperatorIssueUpdate
from app.services.issue_service import create_issue
from app.services.admin_service import override_issue_expert
from app.services.operator_service import (
    backfill_operator_review_assignments,
    list_operator_issues,
    list_operator_queue,
    override_issue_decisions,
)
from app.services.websocket_manager import broadcast_issue_update, issue_event_payload


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

    def with_for_update(self, **_kwargs):
        return self


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


class _AdminAssignmentDatabase:
    def __init__(self, expert):
        self.expert = expert
        self.committed = False

    def query(self, *_args):
        return _OperatorQuery(self.expert)

    def commit(self):
        self.committed = True


class _ReviewOwnershipQuery:
    def __init__(self):
        self.filters = []
        self.updated_values = None

    def options(self, *_args):
        return self

    def filter(self, *conditions):
        self.filters.extend(conditions)
        return self

    def order_by(self, *_args):
        return self

    def all(self):
        return []

    def update(self, values, **_kwargs):
        self.updated_values = values
        return 2


class _ReviewOwnershipDatabase:
    def __init__(self):
        self.review_query = _ReviewOwnershipQuery()

    def query(self, *_args):
        return self.review_query


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

        def assign_review_operator(_db, issue):
            issue.review_operator_id = 3
            return SimpleNamespace(id=3)

        with (
            patch("app.services.issue_service.save_issue_media_files"),
            patch("app.services.issue_service.classify_issue_content", return_value=classification),
            patch("app.services.issue_service.assign_best_expert_to_issue", side_effect=assign),
            patch("app.services.issue_service.assign_primary_operator_review", side_effect=assign_review_operator),
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
        self.assertEqual(issue.review_operator_id, 3)
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

        def assign_review_operator(_db, issue):
            issue.review_operator_id = 3
            return SimpleNamespace(id=3)

        with (
            patch("app.services.issue_service.save_issue_media_files"),
            patch("app.services.issue_service.classify_issue_content", return_value=classification),
            patch("app.services.issue_service.assign_best_expert_to_issue", return_value=None),
            patch("app.services.issue_service.assign_primary_operator_review", side_effect=assign_review_operator),
            patch("app.services.issue_service.publish_issue_update"),
        ):
            original_add = db.add

            def add(issue):
                db.issue = issue
                original_add(issue)

            db.add = add
            issue = create_issue(db, 1, _issue_data())

        self.assertEqual(issue.status, "waiting_for_assignment")
        self.assertEqual(issue.review_operator_id, 3)


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
            review_operator_id=3,
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
            result = override_issue_decisions(db, issue.id, 3, update)

        self.assertIs(result, issue)
        self.assertEqual(issue.category, "Electrical")
        self.assertEqual(issue.priority, "high")
        self.assertEqual(issue.assigned_expert_id, expert.id)
        self.assertEqual(issue.status, "assigned")
        self.assertTrue(db.committed)

    def test_operator_cannot_assign_an_inactive_or_unverified_expert(self):
        issue = SimpleNamespace(id=8, assigned_expert_id=None, review_operator_id=3)
        expert = SimpleNamespace(id=9, is_active=False, is_verified=False)
        db = _OperatorDatabase(expert)

        with patch("app.services.operator_service.get_operator_issue", return_value=issue):
            with self.assertRaises(HTTPException) as error:
                override_issue_decisions(db, issue.id, 3, OperatorIssueUpdate(assigned_expert_id=9))

        self.assertEqual(error.exception.status_code, 400)

    def test_operator_can_force_assign_an_active_verified_expert_outside_ai_matches(self):
        issue = SimpleNamespace(
            id=8,
            problem_type="General",
            category="General",
            priority="low",
            urgency="low",
            operator_note=None,
            assigned_expert_id=None,
            review_operator_id=3,
            assigned_at=None,
            status="waiting_for_assignment",
            admin_override_at=None,
        )
        expert = SimpleNamespace(id=10, is_active=True, is_verified=True)
        db = _OperatorDatabase(expert)

        with (
            patch("app.services.operator_service.get_operator_issue", return_value=issue),
            patch("app.services.operator_service.eligible_experts_for_issue", return_value=[]),
            patch("app.services.operator_service.publish_issue_update"),
        ):
            result = override_issue_decisions(
                db,
                issue.id,
                3,
                OperatorIssueUpdate(assignedExpertId=10),
            )

        self.assertIs(result, issue)
        self.assertEqual(issue.assigned_expert_id, 10)
        self.assertEqual(issue.status, "assigned")

    def test_operator_cannot_override_after_admin_override(self):
        issue = SimpleNamespace(
            id=8,
            assigned_expert_id=None,
            review_operator_id=3,
            admin_override_at="2026-07-22T00:00:00+00:00",
        )
        db = _OperatorDatabase(expert=None)

        with patch("app.services.operator_service.get_operator_issue", return_value=issue):
            with self.assertRaises(HTTPException) as error:
                override_issue_decisions(db, issue.id, 3, OperatorIssueUpdate(priority="high"))

        self.assertEqual(error.exception.status_code, 409)

    def test_operator_payload_rejects_invalid_priority(self):
        with self.assertRaises(ValidationError):
            OperatorIssueUpdate(priority="immediate")

    def test_operator_assignment_payload_accepts_browser_and_admin_field_names(self):
        self.assertEqual(OperatorIssueUpdate(assignedExpertId="9").assigned_expert_id, 9)
        self.assertEqual(OperatorIssueUpdate(expertId=10).assigned_expert_id, 10)

    def test_customer_cannot_satisfy_operator_dependency(self):
        with self.assertRaises(HTTPException) as error:
            get_current_operator(SimpleNamespace(role="customer"))

        self.assertEqual(error.exception.status_code, 403)

    def test_backfill_assigns_missing_and_op2_review_work_to_op1(self):
        db = _ReviewOwnershipDatabase()

        reassigned = backfill_operator_review_assignments(
            db,
            primary_operator_id=3,
            secondary_operator_id=4,
        )

        self.assertEqual(reassigned, 2)
        self.assertEqual(db.review_query.updated_values, {Issue.review_operator_id: 3})

    def test_operator_list_is_scoped_to_the_review_owner(self):
        db = _ReviewOwnershipDatabase()

        list_operator_issues(db, operator_id=3)

        self.assertTrue(any("review_operator_id" in str(condition) for condition in db.review_query.filters))

    def test_operator_queue_is_scoped_to_active_review_work(self):
        db = _ReviewOwnershipDatabase()

        list_operator_queue(db, operator_id=3)

        joined_filters = " ".join(str(condition) for condition in db.review_query.filters)
        self.assertIn("review_operator_id", joined_filters)
        self.assertIn("status", joined_filters)

    def test_inactive_operator_cannot_authenticate(self):
        inactive_operator = SimpleNamespace(email="op2@gmail.com", is_active=False)
        db = SimpleNamespace(
            query=lambda *_args: SimpleNamespace(
                filter=lambda *_filters: SimpleNamespace(first=lambda: inactive_operator)
            )
        )
        credentials = SimpleNamespace(credentials="test-token")

        with patch("app.auth.dependencies._decode_token", return_value={"sub": "op2@gmail.com"}):
            with self.assertRaises(HTTPException) as error:
                get_current_user(credentials, db)

        self.assertEqual(error.exception.status_code, 403)

    def test_suspended_operator_cannot_authenticate(self):
        suspended_operator = SimpleNamespace(
            email="op2@gmail.com",
            is_active=True,
            account_status="suspended",
        )
        db = SimpleNamespace(
            query=lambda *_args: SimpleNamespace(
                filter=lambda *_filters: SimpleNamespace(first=lambda: suspended_operator)
            )
        )
        credentials = SimpleNamespace(credentials="test-token")

        with patch("app.auth.dependencies._decode_token", return_value={"sub": "op2@gmail.com"}):
            with self.assertRaises(HTTPException) as error:
                get_current_user(credentials, db)

        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(error.exception.detail, "Suspended")


class AdminAssignmentTests(TestCase):
    def test_assignment_returns_reloaded_assigned_expert_and_broadcasts_it(self):
        prior_issue = SimpleNamespace(
            id=8,
            assigned_expert_id=None,
            assigned_at=None,
            status="waiting_for_assignment",
            admin_override_at=None,
        )
        expert = SimpleNamespace(id=9)
        response_issue = SimpleNamespace(
            id=8,
            assigned_expert_id=9,
            assigned_expert=SimpleNamespace(id=9, full_name="Expert One"),
        )
        db = _AdminAssignmentDatabase(expert)

        with (
            patch(
                "app.services.admin_service._get_issue_with_assigned_expert",
                side_effect=[prior_issue, response_issue],
            ),
            patch("app.services.admin_service.publish_issue_update") as publish,
        ):
            result = override_issue_expert(db, issue_id=8, expert_id=9)

        self.assertTrue(db.committed)
        self.assertIs(result, response_issue)
        self.assertEqual(prior_issue.assigned_expert_id, 9)
        publish.assert_called_once_with(response_issue, "admin_override", previous_expert_id=None)

    def test_assignment_returns_none_for_missing_issue_or_expert(self):
        db = _AdminAssignmentDatabase(expert=SimpleNamespace(id=9))
        with patch("app.services.admin_service._get_issue_with_assigned_expert", return_value=None):
            self.assertIsNone(override_issue_expert(db, issue_id=999, expert_id=9))

        issue = SimpleNamespace(id=8)
        db = _AdminAssignmentDatabase(expert=None)
        with patch("app.services.admin_service._get_issue_with_assigned_expert", return_value=issue):
            self.assertIsNone(override_issue_expert(db, issue_id=8, expert_id=999))


class WebsocketIssueEventTests(IsolatedAsyncioTestCase):
    def test_issue_event_payload_includes_review_operator_and_dropdown_fields(self):
        issue = SimpleNamespace(
            id=8,
            title="AC leaking",
            description="Water leaking from AC",
            problem_type="Air Conditioner",
            category="Electrical",
            priority="high",
            urgency="high",
            status="assigned",
            operator_note="Reviewed",
            customer_id=2,
            assigned_expert_id=9,
            review_operator_id=3,
            assigned_expert=SimpleNamespace(
                id=9,
                full_name="Expert One",
                email="expert@example.com",
                phone="9999999999",
                skills="Electrical",
                profile_image_url=None,
            ),
            assigned_at=None,
            updated_at=None,
        )

        payload = issue_event_payload(issue, "operator_issue_updated")

        self.assertEqual(payload["issue"]["problemType"], "Air Conditioner")
        self.assertEqual(payload["issue"]["priority"], "high")
        self.assertEqual(payload["issue"]["assignedExpertId"], 9)
        self.assertEqual(payload["issue"]["reviewOperatorId"], 3)

    async def test_issue_update_broadcast_reaches_review_operator_and_admins(self):
        payload = {
            "event": "operator_issue_updated",
            "issue": {
                "customerId": 2,
                "assignedExpertId": 9,
                "reviewOperatorId": 3,
            },
        }

        with (
            patch("app.services.websocket_manager.manager.send_personal_message", new_callable=AsyncMock) as send,
            patch("app.services.websocket_manager.manager.broadcast_to_account_type", new_callable=AsyncMock) as broadcast,
        ):
            await broadcast_issue_update(payload, previous_expert_id=None)

        send.assert_any_await(payload, "operator", 3)
        broadcast.assert_awaited_once_with(payload, "admin")
