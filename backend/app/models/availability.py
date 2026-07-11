from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class Availability(Base):
    __tablename__ = "availabilities"

    id = Column(Integer, primary_key=True, index=True)

    expert_id = Column(
        Integer,  
        ForeignKey("experts.id"),
        nullable=False
    )

    day_of_week = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)

    expert = relationship(
        "Expert",
        back_populates="availabilities"
    )
