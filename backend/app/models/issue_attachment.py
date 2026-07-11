from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class IssueAttachment(Base):
    __tablename__ = "issue_attachments"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    storage_provider = Column(String, nullable=False, default="local", server_default="local")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    issue = relationship("Issue", back_populates="attachments")
