from fastapi import APIRouter, Query

from app.models import League, ListaNoticias
from app.services.noticias import ultimas_noticias_nbb
from app.sources.ge.client import GEClient
from app.sources.lnb.client import LNBClient
from app.sources.surto_olimpico.client import SurtoOlimpicoClient

router = APIRouter(prefix="/nbb", tags=["NBB"])

_lnb = LNBClient()
_ge = GEClient()
_surto = SurtoOlimpicoClient()


@router.get("/noticias", response_model=ListaNoticias, summary="Notícias do NBB")
def noticias(
    limite: int = Query(5, ge=1, le=50, description="Quantas notícias retornar"),
) -> ListaNoticias:
    """Últimas notícias do NBB: LNB + GE + Surto Olímpico, sem duplicatas."""
    return ultimas_noticias_nbb(_lnb, _ge, _surto, League.NBB, limite=limite)