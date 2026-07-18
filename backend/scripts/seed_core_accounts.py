"""Idempotently provision the fixed administrator and operator accounts.

Run from the backend directory with ``py scripts/seed_core_accounts.py`` after
setting DATABASE_URL.  Environment variables allow credentials to be replaced
without modifying source code:

    ADMIN_EMAIL, ADMIN_PASSWORD,
    OPERATOR_1_NAME, OPERATOR_1_EMAIL, OPERATOR_1_PASSWORD,
    OPERATOR_2_NAME, OPERATOR_2_EMAIL, OPERATOR_2_PASSWORD
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path


# Allow the utility to run directly while keeping all database configuration in
# the application package.  No connection settings are duplicated here.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.security import hash_password  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SeedAccount:
    """The minimal user data supported by the existing User model."""

    name: str
    email: str
    password: str
    role: str


def _environment_value(name: str, default: str) -> str:
    """Read a non-empty environment value, otherwise retain the fixed default."""
    return os.getenv(name, default).strip() or default


def configured_accounts() -> tuple[SeedAccount, ...]:
    """Build the required fixed accounts, allowing environment overrides."""
    return (
        SeedAccount(
            name="Admin",
            email=_environment_value("ADMIN_EMAIL", "admin@gmail.com").lower(),
            password=_environment_value("ADMIN_PASSWORD", "admin123"),
            role="admin",
        ),
        SeedAccount(
            # The schema has no username column, so this is the stored username.
            name=_environment_value("OPERATOR_1_NAME", "Op1"),
            email=_environment_value("OPERATOR_1_EMAIL", "op1@gmail.com").lower(),
            password=_environment_value("OPERATOR_1_PASSWORD", "operator1"),
            role="operator",
        ),
        SeedAccount(
            name=_environment_value("OPERATOR_2_NAME", "Op2"),
            email=_environment_value("OPERATOR_2_EMAIL", "op2@gmail.com").lower(),
            password=_environment_value("OPERATOR_2_PASSWORD", "operator2"),
            role="operator",
        ),
    )


def seed_core_accounts() -> None:
    """Create or reconcile the fixed admin/operator accounts in one transaction.

    Email is the database's unique identifier.  The existing model has no
    string ID/username column, so name is also checked to prevent an account
    such as ``Op1`` from being accidentally duplicated under a new email.
    Existing records are reconciled (role, name, and password) rather than
    inserted again, making repeated runs safe.
    """
    accounts = configured_accounts()
    emails = [account.email for account in accounts]
    names = [account.name for account in accounts]

    if len(set(emails)) != len(emails) or len(set(names)) != len(names):
        raise ValueError("Seed account emails and names must each be unique")

    db = SessionLocal()
    try:
        for account in accounts:
            existing_by_email = db.query(User).filter(User.email == account.email).first()
            existing_by_name = db.query(User).filter(User.name == account.name).first()

            if (
                existing_by_email is not None
                and existing_by_name is not None
                and existing_by_email.id != existing_by_name.id
            ):
                raise ValueError(
                    f"Cannot seed {account.email}: email and username '{account.name}' "
                    "belong to different existing users"
                )

            user = existing_by_email or existing_by_name
            if user is None:
                user = User(
                    name=account.name,
                    email=account.email,
                    # Hash only at the persistence boundary; never store plaintext.
                    password_hash=hash_password(account.password),
                    role=account.role,
                    phone_number="",
                    is_active=True,
                )
                db.add(user)
                logger.info("Created %s account: %s", account.role, account.email)
                continue

            # Reconcile configured credentials and permissions without creating
            # duplicates.  This guarantees an administrator and two operators
            # with the configured identities on every execution.
            user.name = account.name
            user.email = account.email
            user.role = account.role
            user.password_hash = hash_password(account.password)
            user.is_active = True
            logger.info("Updated existing %s account: %s", account.role, account.email)

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Core-account seeding failed; all changes were rolled back")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    seed_core_accounts()
