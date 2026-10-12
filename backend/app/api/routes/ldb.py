from fastapi import APIRouter, Query

from app.models import League, ListaNoticias
from app.services.noticias import ultimas_noticias_ldb
from app.sources.google_news.client import GoogleNewsClient
from app.sources.lnb.client import LNBClient

router = APIRouter(prefix="/ldb", tags=["LDB"])

_lnb = LNBClient()
_google = GoogleNewsClient()


@router.get("/noticias", response_model=ListaNoticias, summary="Notícias da LDB")
def noticias(
    limite: int = Query(5, ge=1, le=50, description="Quantas notícias retornar"),
) -> ListaNoticias:
    """Últimas notícias da LDB: LNB + Google News, sem duplicatas."""
    return ultimas_noticias_ldb(_lnb, _google, League.LDB, limite=limite)