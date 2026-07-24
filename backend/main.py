import asyncio
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.expert import router as expert_router
from app.api.availability import router as availability_router
from app.api.issue import router as issue_router
from app.api.issue_media import router as issue_media_router
from app.api.expert_dashboard import router as expert_dashboard_router
from app.api.review import router as review_router
from app.api.feedback import router as feedback_router
from app.api.admin import router as admin_router
from app.api.operator import router as operator_router
from app.api.chat import router as chat_router
from app.api.upload import router as upload_router
from app.database.init_db import ensure_database_schema
from app.core.logging_config import configure_logging
from app.services.websocket_manager import manager
from app.auth.dependencies import _decode_token
from app.database.session import SessionLocal
from app.models.expert import Expert
from app.models.user import User


def _user_can_use_realtime(user: User) -> bool:
    account_status = str(getattr(user, "account_status", None) or "active").strip().lower()
    return user.is_active and account_status != "suspended"


configure_logging()
app = FastAPI(openapi_version="3.0.3")
BACKEND_ROOT = Path(__file__).resolve().parent
UPLOADS_ROOT = BACKEND_ROOT / "uploads"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(expert_router)
app.include_router(expert_dashboard_router)
app.include_router(availability_router)
app.include_router(issue_router)
app.include_router(issue_media_router)
app.include_router(review_router)
app.include_router(feedback_router)
app.include_router(admin_router)
app.include_router(operator_router)
app.include_router(chat_router)
app.include_router(upload_router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Expert Connect API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/uploads/profiles/images/{filename:path}", include_in_schema=False)
def redirect_legacy_user_profile_image(filename: str):
    """Keep old database image URLs working after the profile folder move."""
    if not filename or Path(filename).name != filename:
        raise HTTPException(status_code=404, detail="Profile image not found")
    return RedirectResponse(
        url=f"/uploads/users/profile_pic/{quote(filename)}",
        status_code=307,
    )


# This mount serves /uploads/users/profile_pic/... and
# /uploads/experts/profile_pic/... using the current hierarchical layout.
UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_ROOT), name="uploads")


@app.on_event("startup")
def sync_database_schema():
    ensure_database_schema()


@app.on_event("startup")
async def configure_websocket_manager():
    manager.set_event_loop(asyncio.get_running_loop())


def _socket_identity_is_valid(account_type: str, account_id: int, token: str | None) -> bool:
    if not token:
        return False

    try:
        payload = _decode_token(token)
    except Exception:
        return False

    role = str(payload.get("role") or payload.get("account_type") or "").strip().lower()
    subject = payload.get("sub")
    db = SessionLocal()
    try:
        if account_type == "expert" and role == "expert":
            expert = db.get(Expert, account_id)
            return subject is not None and int(subject) == account_id and expert is not None and expert.is_active

        if account_type in {"user", "customer", "admin", "operator"} and subject:
            user = db.query(User).filter(User.email == subject).first()
            if user is None or user.id != account_id or not _user_can_use_realtime(user):
                return False
            return (account_type == "admin" and role == "admin") or (
                account_type in {"user", "customer"} and role == "customer"
            ) or (account_type == "operator" and role == "operator")
        return False
    except (TypeError, ValueError):
        return False
    finally:
        db.close()


@app.websocket("/ws/{account_type}/{account_id}")
async def issue_dashboard_websocket(websocket: WebSocket, account_type: str, account_id: int):
    normalized_type = account_type.strip().lower()
    if normalized_type not in {"user", "customer", "expert", "admin", "operator"}:
        await websocket.close(code=1008)
        return

    if not _socket_identity_is_valid(normalized_type, account_id, websocket.query_params.get("token")):
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, normalized_type, account_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, normalized_type, account_id)


def _force_swagger_binary_file_fields(schema_part):
    if isinstance(schema_part, dict):
        if schema_part.get("contentMediaType") == "application/octet-stream":
            schema_part.pop("contentMediaType", None)
            schema_part["format"] = "binary"
        for value in schema_part.values():
            _force_swagger_binary_file_fields(value)
    elif isinstance(schema_part, list):
        for item in schema_part:
            _force_swagger_binary_file_fields(item)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version="3.0.3",
        routes=app.routes,
    )
    _force_swagger_binary_file_fields(openapi_schema)
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
