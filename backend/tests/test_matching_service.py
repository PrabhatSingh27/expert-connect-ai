from datetime import date
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app.services.assignment_service import assign_best_expert
from app.services.matching_service import (
    _is_available_for_issue,
    _matches_required_skills,
    _matches_service_area,
)


class _AvailabilityQuery:
    def __init__(self, slots):
        self.slots = slots

    def filter(self, *_args):
        return self

    def all(self):
        return self.slots


class _AvailabilityDatabase:
    def __init__(self, slots):
        self.slots = slots

    def query(self, *_args):
        return _AvailabilityQuery(self.slots)


class MatchingServiceTests(TestCase):
    def test_candidate_requires_skill_and_matching_service_pincode(self):
        issue = SimpleNamespace(
            required_skills="electrician", category="Electrical", pin_code="560001", location=None
        )
        matching_expert = SimpleNamespace(skills="electrician, ac repair", service_pincodes="560001, 560002")
        wrong_skill_expert = SimpleNamespace(skills="plumber", service_pincodes="560001")
        wrong_area_expert = SimpleNamespace(skills="electrician", service_pincodes="110001")

        self.assertTrue(_matches_required_skills(issue, matching_expert))
        self.assertTrue(_matches_service_area(issue, matching_expert))
        self.assertFalse(_matches_required_skills(issue, wrong_skill_expert))
        self.assertFalse(_matches_service_area(issue, wrong_area_expert))

    def test_preferred_time_must_fit_an_expert_slot(self):
        issue = SimpleNamespace(preferred_visit_date=date(2026, 7, 20), preferred_time="10:30 AM")
        expert = SimpleNamespace(id=7)
        slots = [SimpleNamespace(day_of_week="Monday", start_time="09:00", end_time="12:00")]

        self.assertTrue(_is_available_for_issue(_AvailabilityDatabase(slots), issue, expert))
        issue.preferred_time = "1:00 PM"
        self.assertFalse(_is_available_for_issue(_AvailabilityDatabase(slots), issue, expert))

    def test_assignment_uses_first_shared_fairness_candidate(self):
        expert = SimpleNamespace(id=12)
        issue = SimpleNamespace(assigned_expert_id=None, assigned_at=None, status="submitted")
        db = SimpleNamespace(commit=lambda: None, refresh=lambda _: None)

        with patch(
            "app.services.assignment_service.eligible_experts_for_issue",
            return_value=[{"expert": expert, "load": 0, "score": 150}],
        ):
            selected = assign_best_expert(issue, db, commit=False)

        self.assertIs(selected, expert)
        self.assertEqual(issue.assigned_expert_id, expert.id)
        self.assertEqual(issue.status, "assigned")
