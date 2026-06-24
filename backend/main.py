from fastapi import FastAPI
from app.api.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router)

from app.api.expert import router as expert_router

app.include_router(expert_router)