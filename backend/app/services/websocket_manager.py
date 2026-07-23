import asyncio
from datetime import date, datetime
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[tuple[str, int], set[WebSocket]] = {}
        self.event_loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop) -> None:
        self.event_loop = event_loop

    async def connect(self, websocket: WebSocket, account_type: str, account_id: int) -> None:
        await websocket.accept()
        self.active_connections.setdefault((account_type, account_id), set()).add(websocket)

    def disconnect(self, websocket: WebSocket, account_type: str, account_id: int) -> None:
        key = (account_type, account_id)
        connections = self.active_connections.get(key)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self.active_connections.pop(key, None)

    async def close_account_connections(
        self,
        account_type: str,
        account_id: int,
        *,
        code: int = 4003,
        reason: str = "Account unavailable",
    ) -> None:
        key = (account_type, account_id)
        for connection in list(self.active_connections.get(key, set())):
            try:
                await connection.close(code=code, reason=reason)
            finally:
                self.disconnect(connection, account_type, account_id)

    async def send_personal_message(self, data: dict[str, Any], account_type: str, account_id: int) -> None:
        key = (account_type, account_id)
        for connection in list(self.active_connections.get(key, set())):
            try:
                await connection.send_json(data)
            except Exception:
                self.disconnect(connection, account_type, account_id)

    async def broadcast_to_account_type(self, data: dict[str, Any], account_type: str) -> None:
        recipients = [key for key in self.active_connections if key[0] == account_type]
        for _, account_id in recipients:
            await self.send_personal_message(data, account_type, account_id)


manager = ConnectionManager()


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def issue_event_payload(issue: Any, event: str) -> dict[str, Any]:
    expert = issue.assigned_expert
    assigned_expert = None
    if expert is not None:
        assigned_expert = {
            "id": expert.id,
            "fullName": expert.full_name,
            "email": expert.email,
            "phone": expert.phone,
            "skills": expert.skills,
            "profileImageUrl": expert.profile_image_url,
        }

    return {
        "event": event,
        "issue": {
            "id": issue.id,
            "title": issue.title,
            "description": getattr(issue, "description", None),
            "problemType": issue.problem_type,
            "category": issue.category,
            "priority": issue.priority,
            "urgency": issue.urgency,
            "status": issue.status,
            "operatorNote": issue.operator_note,
            "customerId": issue.customer_id,
            "assignedExpertId": issue.assigned_expert_id,
            "reviewOperatorId": issue.review_operator_id,
            "assignedExpert": assigned_expert,
            "assignedAt": _json_value(issue.assigned_at),
            "updatedAt": _json_value(issue.updated_at),
        },
    }


async def broadcast_issue_update(
    payload: dict[str, Any],
    previous_expert_id: int | None = None,
) -> None:
    issue = payload["issue"]
    await manager.send_personal_message(payload, "user", issue["customerId"])
    await manager.send_personal_message(payload, "customer", issue["customerId"])
    if issue["assignedExpertId"] is not None:
        await manager.send_personal_message(payload, "expert", issue["assignedExpertId"])
    if previous_expert_id is not None and previous_expert_id != issue["assignedExpertId"]:
        await manager.send_personal_message(payload, "expert", previous_expert_id)
    operator_queue_event = issue.get("status") in {
        "submitted",
        "ai_classified",
        "waiting_for_assignment",
        "pending_assignment",
        "operator_review",
        "need_more_info",
        "assigned",
        "in_progress",
    }
    if operator_queue_event:
        await manager.broadcast_to_account_type(payload, "operator")
    elif issue["reviewOperatorId"] is not None:
        await manager.send_personal_message(payload, "operator", issue["reviewOperatorId"])
    await manager.broadcast_to_account_type(payload, "admin")


def publish_issue_update(
    issue: Any,
    event: str,
    *,
    previous_expert_id: int | None = None,
) -> None:
    """Schedule a dashboard update from synchronous SQLAlchemy service functions."""
    loop = manager.event_loop
    if loop is None or not loop.is_running():
        return
    payload = issue_event_payload(issue, event)
    asyncio.run_coroutine_threadsafe(
        broadcast_issue_update(payload, previous_expert_id=previous_expert_id),
        loop,
    )


async def broadcast_account_status_update(payload: dict[str, Any]) -> None:
    await manager.broadcast_to_account_type(payload, "admin")
    if payload.get("role") == "operator":
        operator_id = payload.get("id")
        if operator_id is not None:
            await manager.send_personal_message(payload, "operator", operator_id)
            if payload.get("accountStatus") == "suspended":
                await manager.close_account_connections(
                    "operator",
                    operator_id,
                    code=4003,
                    reason="Suspended",
                )


def publish_account_status_update(user: Any) -> None:
    loop = manager.event_loop
    if loop is None or not loop.is_running():
        return
    payload = {
        "event": "account_status_updated",
        "id": user.id,
        "role": user.role,
        "isActive": user.is_active,
        "accountStatus": getattr(user, "account_status", None) or "active",
    }
    asyncio.run_coroutine_threadsafe(broadcast_account_status_update(payload), loop)
