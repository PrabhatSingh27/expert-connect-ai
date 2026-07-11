from sqlalchemy import inspect, text

from app.database.base import Base
from app.database.db import engine

from app.models.availability import Availability
from app.models.expert import Expert
from app.models.expert_review import ExpertReview
from app.models.issue import Issue
from app.models.issue_attachment import IssueAttachment
from app.models.user import User
from app.database.session import SessionLocal
from app.core.security import hash_password


def _column_names(table_name: str) -> set[str]:
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _execute(statement: str) -> None:
    with engine.begin() as connection:
        connection.execute(text(statement))


def seed_default_admin() -> None:
    db = SessionLocal()
    try:
        admin = (
            db.query(User)
            .filter(User.email == "admin@gmail.com")
            .first()
        )

        if admin:
            admin.name = "Admin"
            admin.role = "admin"
            admin.is_active = True
            admin.password_hash = hash_password("admin123")
        else:
            admin = User(
                name="Admin",
                email="admin@gmail.com",
                password_hash=hash_password("admin123"),
                role="admin",
                is_active=True,
            )
            db.add(admin)

        db.commit()
    finally:
        db.close()


def ensure_database_schema() -> None:
    Base.metadata.create_all(bind=engine)

    user_columns = _column_names("users")
    if "created_at" not in user_columns:
        _execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL")
    if "is_active" not in user_columns:
        _execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT true NOT NULL")
    _execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'customer'")

    expert_columns = _column_names("experts")
    expert_defaults = {
        "government_id": "VARCHAR DEFAULT '' NOT NULL",
        "government_id_file_url": "VARCHAR",
        "skills": "TEXT DEFAULT '' NOT NULL",
        "service_area": "VARCHAR DEFAULT '' NOT NULL",
        "service_city": "VARCHAR",
        "service_pincodes": "TEXT",
        "bio": "TEXT",
        "permanent_address": "TEXT DEFAULT '' NOT NULL",
        "profile_image_url": "VARCHAR",
        "experience_years": "INTEGER DEFAULT 0 NOT NULL",
        "is_verified": "BOOLEAN DEFAULT false NOT NULL",
        "is_active": "BOOLEAN DEFAULT true NOT NULL",
        "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
        "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
    }
    for column_name, column_definition in expert_defaults.items():
        if column_name not in expert_columns:
            _execute(f"ALTER TABLE experts ADD COLUMN {column_name} {column_definition}")

    issue_columns = _column_names("issues")
    issue_defaults = {
        "assigned_expert_id": "INTEGER",
        "problem_type": "VARCHAR",
        "priority": "VARCHAR",
        "urgency": "VARCHAR",
        "required_skills": "TEXT",
        "confidence_score": "FLOAT",
        "ai_explanation": "TEXT",
        "preferred_visit_date": "DATE",
        "preferred_time": "VARCHAR",
        "location": "VARCHAR",
        "pin_code": "VARCHAR",
        "address": "TEXT",
        "image_path": "VARCHAR",
        "video_path": "VARCHAR",
        "audio_path": "VARCHAR",
        "assigned_at": "TIMESTAMP WITH TIME ZONE",
        "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
        "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
    }
    for column_name, column_definition in issue_defaults.items():
        if column_name not in issue_columns:
            _execute(f"ALTER TABLE issues ADD COLUMN {column_name} {column_definition}")
    if "status" in issue_columns:
        _execute("ALTER TABLE issues ALTER COLUMN status SET DEFAULT 'open'")

    attachment_columns = _column_names("issue_attachments")
    if attachment_columns and "file_size" not in attachment_columns:
        _execute("ALTER TABLE issue_attachments ADD COLUMN file_size INTEGER")

    availability_columns = _column_names("availabilities")
    if "expert_id" not in availability_columns:
        _execute("ALTER TABLE availabilities ADD COLUMN expert_id INTEGER")
        if "user_id" in availability_columns:
            _execute("UPDATE availabilities SET expert_id = user_id WHERE expert_id IS NULL")

    seed_default_admin()
