from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI
from app.api.auth import router as auth_router

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

from app.api.expert import router as expert_router

app.include_router(expert_router)

from app.api.availability import router as availability_router

app.include_router(availability_router)

from app.api.issue import router as issue_router

app.include_router(issue_router)

from app.api.upload import router as upload_router

app.include_router(upload_router)

from app.api.upload import router as upload_router

app.include_router(upload_router)