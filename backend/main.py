from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.expert import router as expert_router
from app.api.availability import router as availability_router
from app.api.issue import router as issue_router
from app.api.expert_dashboard import router as expert_dashboard_router
from app.api.review import router as review_router
from app.api.feedback import router as feedback_router
from app.api.admin import router as admin_router
from app.database.init_db import ensure_database_schema
from app.core.logging_config import configure_logging

configure_logging()
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:8080",
    "http://localhost:4200",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(expert_router)
app.include_router(expert_dashboard_router)
app.include_router(availability_router)
app.include_router(issue_router)
app.include_router(review_router)
app.include_router(feedback_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Expert Connect API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
def sync_database_schema():
    ensure_database_schema()
