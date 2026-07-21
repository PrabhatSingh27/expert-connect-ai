from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, default="", server_default="")
    profile_image_url = Column(String, nullable=True)
    role = Column(String, nullable=False, default="customer", server_default="customer")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    issues = relationship(
        "Issue",
        foreign_keys="Issue.customer_id",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    review_issues = relationship(
        "Issue",
        foreign_keys="Issue.review_operator_id",
        back_populates="review_operator",
    )
