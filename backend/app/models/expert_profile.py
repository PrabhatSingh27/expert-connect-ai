from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class ExpertProfile(Base):
    __tablename__ = "expert_profiles"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True
    )

    title = Column(String, nullable=False)

    bio = Column(Text)

    skills = Column(Text)

    experience_years = Column(Integer)

    hourly_rate = Column(Integer)

    user = relationship(
        "User",
        back_populates="expert_profile"
    )