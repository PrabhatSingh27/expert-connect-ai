from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.issue import (
    IssueCreate,
    IssueClassificationResponse,
    IssueUpdate,
    IssueResponse,
    IssueSummaryResponse,
)
from app.services.issue_service import (
    classify_issue,
    create_issue,
    get_all_issues,
    get_customer_issue,
    get_my_issues,
    assign_best_expert,
    update_issue,
    delete_issue
)
from app.services.matching_service import match_experts_for_issue

router = APIRouter(
    prefix="/issues",
    tags=["Issues"]
)


def _merge_uploads(
    multiple_files: list[UploadFile] | None,
    single_file: UploadFile | None,
) -> list[UploadFile] | None:
    files = list(multiple_files or [])
    if single_file:
        files.append(single_file)
    return files or None


@router.post("/", response_model=IssueResponse)
def create_new_issue(
    title: str = Form(...),
    description: str = Form(...),
    category: str | None = Form(default=None),
    priority: str | None = Form(default=None),
    urgency: str | None = Form(default=None),
    required_skills: str | None = Form(default=None),
    preferred_visit_date: date | None = Form(default=None),
    preferred_time: str | None = Form(default=None),
    location: str | None = Form(default=None),
    pin_code: str | None = Form(default=None),
    address: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    images: list[UploadFile] | None = File(default=None),
    video: UploadFile | None = File(default=None),
    videos: list[UploadFile] | None = File(default=None),
    audio: UploadFile | None = File(default=None),
    audio_files: list[UploadFile] | None = File(default=None),
    audio_recording: UploadFile | None = File(default=None),
    audio_recordings: list[UploadFile] | None = File(default=None),
    files: list[UploadFile] | None = File(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = IssueCreate.model_validate(
        {
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "urgency": urgency,
            "required_skills": required_skills,
            "preferred_visit_date": preferred_visit_date,
            "preferred_time": preferred_time,
            "location": location,
            "pin_code": pin_code,
            "address": address,
        }
    )
    return create_issue(
        db,
        current_user.id,
        data,
        files=files,
        image_files=_merge_uploads(images, image),
        video_files=_merge_uploads(videos, video),
        audio_files=_merge_uploads(audio_files, audio),
        audio_recordings=_merge_uploads(audio_recordings, audio_recording),
    )

@router.get("/", response_model=list[IssueSummaryResponse])
def list_issues(
    db: Session = Depends(get_db)
):
    return get_all_issues(db)


@router.get("", response_model=list[IssueSummaryResponse])
def list_issues_without_redirect(
    mine: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if mine:
        return get_my_issues(db, current_user.id)
    return get_all_issues(db)


@router.get("/my", response_model=list[IssueSummaryResponse])
def list_my_issues(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_my_issues(db, current_user.id)


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_customer_issue(db, issue_id, current_user.id)

@router.put("/{issue_id}", response_model=IssueResponse)
def edit_issue(
    issue_id: int,
    title: str | None = Form(default=None),
    description: str | None = Form(default=None),
    category: str | None = Form(default=None),
    priority: str | None = Form(default=None),
    urgency: str | None = Form(default=None),
    required_skills: str | None = Form(default=None),
    status: str | None = Form(default=None),
    preferred_visit_date: date | None = Form(default=None),
    preferred_time: str | None = Form(default=None),
    location: str | None = Form(default=None),
    pin_code: str | None = Form(default=None),
    address: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    images: list[UploadFile] | None = File(default=None),
    video: UploadFile | None = File(default=None),
    videos: list[UploadFile] | None = File(default=None),
    audio: UploadFile | None = File(default=None),
    audio_files: list[UploadFile] | None = File(default=None),
    audio_recording: UploadFile | None = File(default=None),
    audio_recordings: list[UploadFile] | None = File(default=None),
    files: list[UploadFile] | None = File(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = IssueUpdate.model_validate(
        {
            key: value
            for key, value in {
                "title": title,
                "description": description,
                "category": category,
                "priority": priority,
                "urgency": urgency,
                "required_skills": required_skills,
                "status": status,
                "preferred_visit_date": preferred_visit_date,
                "preferred_time": preferred_time,
                "location": location,
                "pin_code": pin_code,
                "address": address,
            }.items()
            if value is not None
        }
    )
    return update_issue(
        db,
        issue_id,
        current_user.id,
        data,
        files=files,
        image_files=_merge_uploads(images, image),
        video_files=_merge_uploads(videos, video),
        audio_files=_merge_uploads(audio_files, audio),
        audio_recordings=_merge_uploads(audio_recordings, audio_recording),
    )

@router.delete("/{issue_id}")
def remove_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return delete_issue(db, issue_id, current_user.id)


@router.post("/{issue_id}/classify", response_model=IssueClassificationResponse)
def classify_existing_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return classify_issue(db, issue_id, current_user.id)


@router.get("/{issue_id}/matches")
def get_issue_matches(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    issue = get_customer_issue(db, issue_id, current_user.id)
    return match_experts_for_issue(db, issue)


@router.post("/{issue_id}/assign-best", response_model=IssueResponse)
def assign_best_matching_expert(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return assign_best_expert(db, issue_id, current_user.id)

