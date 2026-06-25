from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class Availability(Base):
    __tablename__ = "availabilities"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    day_of_week = Column(String, nullable=False)

    start_time = Column(String, nullable=False)

    end_time = Column(String, nullable=False)

    user = relationship("User")