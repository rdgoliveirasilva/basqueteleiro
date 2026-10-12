from fastapi import APIRouter, Query

from app.models import League, ListaNoticias
from app.services.noticias import ultimas_noticias_google
from app.sources.google_news.client import GoogleNewsClient

router = APIRouter(prefix="/noticias", tags=["Notícias"])

_google = GoogleNewsClient()


@router.get("", response_model=ListaNoticias, summary="Últimas notícias (agregado)")
def noticias(
    limite: int = Query(5, ge=1, le=50, description="Quantas notícias retornar"),
) -> ListaNoticias:
    """Últimas notícias de basquete (Google News). Agregado multi-fontes."""
    return ultimas_noticias_google(_google, "basquete", League.GERAL, limite=limite)