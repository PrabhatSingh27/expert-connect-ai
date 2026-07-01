from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.issue import Issue


def create_issue(db: Session, customer_id: int, data):
    issue = Issue(
        customer_id=customer_id,
        title=data.title,
        description=data.description,
        category=data.category,
        status="open"
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return issue


def get_all_issues(db: Session):
    return db.query(Issue).all()


def get_issue_by_id(db: Session, issue_id: int):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )

    return issue


def update_issue(db: Session, issue_id: int, current_user_id: int, data):
    issue = get_issue_by_id(db, issue_id)

    if issue.customer_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    issue.title = data.title
    issue.description = data.description
    issue.category = data.category
    issue.status = data.status

    db.commit()
    db.refresh(issue)

    return issue


def delete_issue(db: Session, issue_id: int, current_user_id: int):
    issue = get_issue_by_id(db, issue_id)

    if issue.customer_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    db.delete(issue)
    db.commit()

    return {"message": "Issue deleted successfully"}