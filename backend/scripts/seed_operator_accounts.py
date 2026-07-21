"""Provision Op1 and transfer all operator review ownership to that account."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.security import hash_password  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
import app.models.availability  # noqa: E402, F401
import app.models.chat_message  # noqa: E402, F401
import app.models.expert  # noqa: E402, F401
import app.models.expert_review  # noqa: E402, F401
import app.models.issue_attachment  # noqa: E402, F401
from app.models.issue import Issue  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.operator_service import backfill_operator_review_assignments  # noqa: E402


logger = logging.getLogger(__name__)
PRIMARY_OPERATOR_EMAIL = "op1@gmail.com"
SECONDARY_OPERATOR_EMAIL = "op2@gmail.com"


def _environment_value(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def seed_operator_accounts() -> None:
    """Upsert Op1, deactivate Op2, and idempotently backfill review ownership."""
    operator_name = _environment_value("OPERATOR_1_NAME", "Op1")
    operator_email = _environment_value("OPERATOR_1_EMAIL", PRIMARY_OPERATOR_EMAIL).lower()
    operator_password = _environment_value("OPERATOR_1_PASSWORD", "operator1")

    db = SessionLocal()
    try:
        by_email = db.query(User).filter(User.email == operator_email).first()
        by_name = db.query(User).filter(User.name == operator_name).first()
        if by_email is not None and by_name is not None and by_email.id != by_name.id:
            raise ValueError("Op1 email and username belong to different users")

        primary_operator = by_email or by_name
        if primary_operator is None:
            primary_operator = User(
                name=operator_name,
                email=operator_email,
                password_hash=hash_password(operator_password),
                role="operator",
                phone_number="",
                is_active=True,
            )
            db.add(primary_operator)
            db.flush()
            logger.info("Created primary operator account: %s", operator_email)
        else:
            primary_operator.name = operator_name
            primary_operator.email = operator_email
            primary_operator.password_hash = hash_password(operator_password)
            primary_operator.role = "operator"
            primary_operator.is_active = True
            logger.info("Updated primary operator account: %s", operator_email)

        secondary_operator = db.query(User).filter(User.email == SECONDARY_OPERATOR_EMAIL).first()
        if secondary_operator is not None and secondary_operator.id != primary_operator.id:
            secondary_operator.is_active = False
            logger.info("Deactivated secondary operator account: %s", SECONDARY_OPERATOR_EMAIL)

        # Only review ownership is changed; expert, customer, triage, media,
        # status, and chat data are intentionally left untouched.
        reassigned = backfill_operator_review_assignments(
            db,
            primary_operator.id,
            secondary_operator.id if secondary_operator is not None else None,
        )
        logger.info("Backfilled %s issue review assignments to %s", reassigned, operator_email)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Operator consolidation failed; changes were rolled back")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    seed_operator_accounts()
