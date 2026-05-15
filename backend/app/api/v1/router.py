from fastapi import APIRouter
from app.api.v1.endpoints import auth, documents, chat, admin, workspaces

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
