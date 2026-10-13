from fastapi import APIRouter, Query

from app.models import ListaNoticias
from app.services.noticias import ultimas_noticias_ouro
from app.sources.lnb.client import LNBClient

router = APIRouter(prefix="/ouro", tags=["Liga Ouro"])

_lnb = LNBClient()


@router.get("/noticias", response_model=ListaNoticias, summary="Notícias da Liga Ouro")
def noticias(
    limite: int = Query(5, ge=1, le=50, description="Quantas notícias retornar"),
) -> ListaNoticias:
    """Últimas notícias da Liga Ouro (LNB)."""
    return ultimas_noticias_ouro(_lnb, limite=limite)