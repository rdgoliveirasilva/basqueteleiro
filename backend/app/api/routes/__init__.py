from fastapi import APIRouter

from app.api.routes import ldb, nba, nbb, noticias, ouro

api_router = APIRouter(prefix="/api")
api_router.include_router(noticias.router)
api_router.include_router(nbb.router)
api_router.include_router(ouro.router)
api_router.include_router(ldb.router)
api_router.include_router(nba.router)