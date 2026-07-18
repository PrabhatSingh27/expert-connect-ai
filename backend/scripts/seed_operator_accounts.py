"""Idempotently provision the two fixed operator accounts.

Run from the backend directory with ``py scripts/seed_operator_accounts.py``.
Credentials can be supplied through the following environment variables:

    OPERATOR_1_NAME, OPERATOR_1_EMAIL, OPERATOR_1_PASSWORD,
    OPERATOR_2_NAME, OPERATOR_2_EMAIL, OPERATOR_2_PASSWORD
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path


# Keep this utility decoupled from connection configuration: it imports the
# application's configured session factory instead of declaring a database URL.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.security import hash_password  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
# Import every related model before querying User so SQLAlchemy can resolve the
# relationship strings declared on User and Issue in a standalone process.
import app.models.availability  # noqa: E402, F401
import app.models.chat_message  # noqa: E402, F401
import app.models.expert  # noqa: E402, F401
import app.models.expert_review  # noqa: E402, F401
import app.models.issue  # noqa: E402, F401
import app.models.issue_attachment  # noqa: E402, F401
from app.models.user import User  # noqa: E402


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OperatorAccount:
    """The persisted operator fields supported by the existing User model."""

    username: str
    email: str
    password: str


def _environment_value(name: str, default: str) -> str:
    """Return an environment override when it is non-empty, otherwise default."""
    return os.getenv(name, default).strip() or default


def configured_operator_accounts() -> tuple[OperatorAccount, OperatorAccount]:
    """Build exactly the two required fixed operator accounts."""
    return (
        OperatorAccount(
            # User has no username column; name is the persisted username.
            username=_environment_value("OPERATOR_1_NAME", "Op1"),
            email=_environment_value("OPERATOR_1_EMAIL", "op1@gmail.com").lower(),
            password=_environment_value("OPERATOR_1_PASSWORD", "operator1"),
        ),
        OperatorAccount(
            username=_environment_value("OPERATOR_2_NAME", "Op2"),
            email=_environment_value("OPERATOR_2_EMAIL", "op2@gmail.com").lower(),
            password=_environment_value("OPERATOR_2_PASSWORD", "operator2"),
        ),
    )


def seed_operator_accounts() -> None:
    """Create or reconcile Op1 and Op2 as operators in one transaction.

    The model's numeric primary key cannot store the required string IDs, so
    ``User.name`` is used as the username lookup alongside unique email.  A
    conflicting email/name pair is rejected and the whole operation rolls back.
    """
    accounts = configured_operator_accounts()
    emails = {account.email for account in accounts}
    usernames = {account.username for account in accounts}
    if len(emails) != 2 or len(usernames) != 2:
        raise ValueError("Operator emails and usernames must be distinct")

    db = SessionLocal()
    try:
        for account in accounts:
            existing_by_email = db.query(User).filter(User.email == account.email).first()
            existing_by_username = db.query(User).filter(User.name == account.username).first()

            if (
                existing_by_email is not None
                and existing_by_username is not None
                and existing_by_email.id != existing_by_username.id
            ):
                raise ValueError(
                    f"Email {account.email} and username {account.username} belong to different users"
                )

            user = existing_by_email or existing_by_username
            if user is None:
                user = User(
                    name=account.username,
                    email=account.email,
                    password_hash=hash_password(account.password),
                    role="operator",
                    phone_number="",
                    is_active=True,
                )
                db.add(user)
                logger.info("Created operator account: %s", account.email)
                continue

            # Re-hash only for persistence; plaintext is never stored in User.
            user.name = account.username
            user.email = account.email
            user.password_hash = hash_password(account.password)
            user.role = "operator"
            user.is_active = True
            logger.info("Updated operator account: %s", account.email)

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Operator-account seeding failed; changes were rolled back")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    seed_operator_accounts()
