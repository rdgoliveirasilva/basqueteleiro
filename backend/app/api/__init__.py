from fastapi import APIRouter

from app.api.routes import nbb, noticias

api_router = APIRouter(prefix="/api")
api_router.include_router(noticias.router)
api_router.include_router(nbb.router)