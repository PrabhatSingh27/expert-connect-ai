from sqlalchemy.orm import Session
from app.models.expert_profile import ExpertProfile

def create_expert_profile(
    db: Session,
    user_id: int,
    profile_data
):
    profile = ExpertProfile(
        user_id=user_id,
        title=profile_data.title,
        bio=profile_data.bio,
        skills=profile_data.skills,
        experience_years=profile_data.experience_years,
        hourly_rate=profile_data.hourly_rate
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile

def get_my_profile(
    db,
    user_id: int
):
    return (
        db.query(ExpertProfile)
        .filter(
            ExpertProfile.user_id == user_id
        )
        .first()
    )

def update_my_profile(
    db,
    user_id: int,
    profile_data
):
    profile = (
        db.query(ExpertProfile)
        .filter(
            ExpertProfile.user_id == user_id
        )
        .first()
    )

    if not profile:
        return None

    profile.title = profile_data.title
    profile.bio = profile_data.bio
    profile.skills = profile_data.skills
    profile.experience_years = profile_data.experience_years
    profile.hourly_rate = profile_data.hourly_rate

    db.commit()
    db.refresh(profile)

    return profile

def get_all_experts(db):
    return db.query(
        ExpertProfile
    ).all()

def get_expert_by_id(
    db: Session,
    expert_id: int
):
    return (
        db.query(ExpertProfile)
        .filter(ExpertProfile.id == expert_id)
        .first()
    )