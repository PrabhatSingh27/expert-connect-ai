from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

from app.models.expert_profile import ExpertProfile

from app.models.availability import Availability

from app.models.issue import Issue