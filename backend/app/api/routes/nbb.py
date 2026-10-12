from fastapi import APIRouter, Query

from app.models import League, ListaNoticias
from app.services.noticias import ultimas_noticias
from app.sources.google_news.client import GoogleNewsClient
from app.sources.lnb.client import LNBClient

router = APIRouter(prefix="/nbb", tags=["NBB"])

# clients únicos, reaproveitados entre requisições (session keep-alive + throttle)
_lnb = LNBClient()
_google = GoogleNewsClient()


@router.get("/noticias", response_model=ListaNoticias, summary="Notícias do NBB")
def noticias(
    limite: int = Query(4, ge=1, le=50, description="Quantas notícias retornar"),
) -> ListaNoticias:
    """Últimas notícias do NBB: LNB + Google News, sem duplicatas."""
    return ultimas_noticias(_lnb, _google, League.NBB, limite=limite)