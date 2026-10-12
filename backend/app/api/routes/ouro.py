from fastapi import APIRouter, Query

from app.models import League, ListaNoticias
from app.services.noticias import ultimas_noticias_lnb
from app.sources.lnb.client import LNBClient

router = APIRouter(prefix="/ouro", tags=["Liga Ouro"])

_lnb = LNBClient()


@router.get("/noticias", response_model=ListaNoticias, summary="Notícias da Liga Ouro")
def noticias(
    limite: int = Query(5, ge=1, le=50, description="Quantas notícias retornar"),
) -> ListaNoticias:
    """Últimas notícias da Liga Ouro, direto da LNB."""
    return ultimas_noticias_lnb(_lnb, League.OURO, limite=limite)