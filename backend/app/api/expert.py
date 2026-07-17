from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_db,
    get_current_expert
)

from app.models.expert import Expert

from app.schemas.expert import (
    ExpertSignup,
    ExpertLogin,
    ExpertResponse,
    ExpertUpdate
)
from app.schemas.auth import Token
from app.schemas.issue import IssueResponse, IssueStatusUpdate
from app.core.rate_limit import rate_limit

from app.services.expert_service import (
    create_expert_account,
    expert_login,
    get_expert_issue,
    get_expert_issues,
    get_my_profile,
    update_my_profile,
    get_all_experts,
    get_expert_by_id,
    update_issue_status,
)
from app.services.file_storage_service import save_upload_file

router = APIRouter(
    prefix="/experts",
    tags=["Experts"]
)


@router.post(
    "/signup",
    response_model=ExpertResponse
)
def expert_signup(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(default=""),
    government_id: str = Form(default=""),
    skills: str = Form(default=""),
    service_area: str = Form(default=""),
    service_city: str | None = Form(default=None),
    service_pincodes: str | None = Form(default=None),
    bio: str | None = Form(default=None),
    permanent_address: str = Form(default=""),
    experience_years: int = Form(default=0),
    profile_image: UploadFile | None = File(default=None),
    government_id_document: UploadFile | None = File(default=None),
    _: None = Depends(rate_limit(limit=10, window_seconds=60)),
    db: Session = Depends(get_db)
):
    signup_data = ExpertSignup(
        full_name=full_name,
        email=email,
        phone=phone,
        government_id=government_id,
        government_id_file_url=save_upload_file(government_id_document, "experts/government_ids"),
        skills=skills,
        service_area=service_area,
        service_city=service_city,
        service_pincodes=service_pincodes,
        bio=bio,
        permanent_address=permanent_address,
        profile_image_url=save_upload_file(profile_image, "experts/profile_images"),
        experience_years=experience_years,
        password=password,
    )
    return create_expert_account(db, signup_data)



@router.post("/login", response_model=Token)
def login(
    login_data: ExpertLogin,
    _: None = Depends(rate_limit(limit=10, window_seconds=60)),
    db: Session = Depends(get_db)
):
    return expert_login(db, login_data)



@router.get(
    "/me",
    response_model=ExpertResponse
)
def my_profile_alias(
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    return get_my_profile(
        db,
        current_expert.id
    )


@router.get(
    "/profile/me",
    response_model=ExpertResponse
)
def my_profile(
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    return get_my_profile(
        db,
        current_expert.id
    )



@router.put(
    "/profile/me",
    response_model=ExpertResponse
)
def update_profile(
    full_name: str | None = Form(default=None),
    phone: str | None = Form(default=None),
    skills: str | None = Form(default=None),
    service_area: str | None = Form(default=None),
    service_city: str | None = Form(default=None),
    service_pincodes: str | None = Form(default=None),
    bio: str | None = Form(default=None),
    permanent_address: str | None = Form(default=None),
    experience_years: int | None = Form(default=None),
    profile_image: UploadFile | None = File(default=None),
    government_id_document: UploadFile | None = File(default=None),
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    update_payload = {
        "full_name": full_name,
        "phone": phone,
        "skills": skills,
        "service_area": service_area,
        "service_city": service_city,
        "service_pincodes": service_pincodes,
        "bio": bio,
        "permanent_address": permanent_address,
        "experience_years": experience_years,
        "profile_image_url": save_upload_file(profile_image, "experts/profile_images"),
        "government_id_file_url": save_upload_file(government_id_document, "experts/government_ids"),
    }
    profile_data = ExpertUpdate.model_validate(
        {key: value for key, value in update_payload.items() if value is not None}
    )
    return update_my_profile(
        db,
        current_expert.id,
        profile_data
    )



@router.get(
    "/",
    response_model=list[ExpertResponse]
)
def list_experts(
    db: Session = Depends(get_db)
):
    return get_all_experts(db)


@router.get(
    "/issues",
    response_model=list[IssueResponse]
)
def list_assigned_issues(
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    return get_expert_issues(db, current_expert.id)


@router.get(
    "/issues/{issue_id}",
    response_model=IssueResponse
)
def assigned_issue_details(
    issue_id: int,
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    return get_expert_issue(db, current_expert.id, issue_id)


@router.patch(
    "/issues/{issue_id}/status",
    response_model=IssueResponse
)
def update_assigned_issue_status(
    issue_id: int,
    data: IssueStatusUpdate,
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    return update_issue_status(
        db,
        current_expert.id,
        issue_id,
        data.status,
    )



@router.get(
    "/{expert_id}",
    response_model=ExpertResponse
)
def expert_details(
    expert_id: int,
    db: Session = Depends(get_db)
):
    return get_expert_by_id(
        db,
        expert_id
    )
