from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class ExpertReview(Base):
    __tablename__ = "expert_reviews"
    __table_args__ = (
        UniqueConstraint("issue_id", "customer_id", name="uq_expert_review_issue_customer"),
    )

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    expert_id = Column(Integer, ForeignKey("experts.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    review = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    issue = relationship("Issue", back_populates="reviews")
    expert = relationship("Expert", back_populates="reviews")
    customer = relationship("User")
