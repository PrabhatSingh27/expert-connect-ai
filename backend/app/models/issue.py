from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(String, nullable=False)  
    description = Column(Text, nullable=False)

    category = Column(String, nullable=True)
    problem_type = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    required_skills = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    operator_note = Column(String, nullable=True)

    preferred_visit_date = Column(Date, nullable=True)
    preferred_time = Column(String, nullable=True)
    location = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    image_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)

    status = Column(String, nullable=False, default="submitted", server_default="submitted")

    assigned_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    assigned_expert_id = Column(
        Integer,
        ForeignKey("experts.id"),
        nullable=True
    )

    customer = relationship(
        "User",
        foreign_keys=[customer_id],
        back_populates="issues"
    )

    assigned_expert = relationship(
        "Expert",
        foreign_keys=[assigned_expert_id],
        back_populates="assigned_issues"
    )

    attachments = relationship(
        "IssueAttachment",
        back_populates="issue",
        cascade="all, delete-orphan"
    )

    reviews = relationship(
        "ExpertReview",
        back_populates="issue",
        cascade="all, delete-orphan"
    )
