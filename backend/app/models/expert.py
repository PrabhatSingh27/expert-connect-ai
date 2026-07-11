from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Expert(Base):
    __tablename__ = "experts"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, unique=True, nullable=False)
    government_id = Column(String, nullable=False)
    government_id_file_url = Column(String, nullable=True)
    skills = Column(Text, nullable=False)
    service_area = Column(String, nullable=False)
    service_city = Column(String, nullable=True)
    service_pincodes = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    permanent_address = Column(Text, nullable=False)
    profile_image_url = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=False, default=0, server_default="0")
    is_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    availabilities = relationship(
        "Availability",
        back_populates="expert",
        cascade="all, delete-orphan"
    )

    assigned_issues = relationship(
        "Issue",
        foreign_keys="Issue.assigned_expert_id",
        back_populates="assigned_expert"
    )

    reviews = relationship(
        "ExpertReview",
        back_populates="expert",
        cascade="all, delete-orphan"
    )
