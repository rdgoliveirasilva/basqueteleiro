from fastapi import APIRouter, Query

from app.models import League, ListaNoticias
from app.services.noticias import ultimas_noticias_google
from app.sources.google_news.client import GoogleNewsClient

router = APIRouter(prefix="/nba", tags=["NBA"])

_google = GoogleNewsClient()


@router.get("/noticias", response_model=ListaNoticias, summary="Notícias da NBA")
def noticias(
    limite: int = Query(5, ge=1, le=50, description="Quantas notícias retornar"),
) -> ListaNoticias:
    """Últimas notícias da NBA (só Google News)."""
    return ultimas_noticias_google(_google, "NBA basquete", League.NBA, limite=limite)