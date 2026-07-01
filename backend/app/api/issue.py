from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.issue import (
    IssueCreate,
    IssueUpdate,
    IssueResponse
)
from app.services.issue_service import (
    create_issue,
    get_all_issues,
    get_issue_by_id,
    update_issue,
    delete_issue
)

router = APIRouter(
    prefix="/issues",
    tags=["Issues"]
)

@router.post("/", response_model=IssueResponse)
def create_new_issue(
    data: IssueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_issue(db, current_user.id, data)

@router.get("/", response_model=list[IssueResponse])
def list_issues(
    db: Session = Depends(get_db)
):
    return get_all_issues(db)

@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db)
):
    return get_issue_by_id(db, issue_id)

@router.put("/{issue_id}", response_model=IssueResponse)
def edit_issue(
    issue_id: int,
    data: IssueUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_issue(db, issue_id, current_user.id, data)

@router.delete("/{issue_id}")
def remove_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return delete_issue(db, issue_id, current_user.id)

