from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_account, get_db
from app.models.chat_message import ChatMessage
from app.models.issue import Issue
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse


router = APIRouter(prefix="/issues", tags=["Chat"])


def _authorized_issue_participant(db: Session, issue_id: int, account: dict) -> tuple[Issue, str, int]:
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    if account["role"] == "customer" and issue.customer_id == account["user_id"]:
        return issue, "customer", account["user_id"]
    if account["role"] == "expert" and issue.assigned_expert_id == account["expert_id"]:
        return issue, "expert", account["expert_id"]

    raise HTTPException(status_code=403, detail="Not authorized to access this issue chat")


@router.get("/{issue_id}/messages", response_model=list[ChatMessageResponse])
def list_messages(
    issue_id: int,
    account: dict = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    _authorized_issue_participant(db, issue_id, account)
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.issue_id == issue_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .all()
    )


@router.post("/{issue_id}/messages", response_model=ChatMessageResponse, status_code=201)
def send_message(
    issue_id: int,
    data: ChatMessageCreate,
    account: dict = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    _, sender_type, sender_id = _authorized_issue_participant(db, issue_id, account)
    chat_message = ChatMessage(
        issue_id=issue_id,
        sender_id=sender_id,
        sender_type=sender_type,
        message=data.message,
    )
    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)
    return chat_message
