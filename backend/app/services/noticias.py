"""Serviço de notícias: funde fontes, deduplica, ordena.

Radar NBB agora funde 3 fontes (LNB + GE + Surto Olímpico), todas com
imagem real. Google News foi removido — não trazia imagem e era lento.
"""

import logging
import re
import unicodedata
from datetime import datetime, timezone

from app.models import League, ListaNoticias, Noticia
from app.sources.ge.client import GEClient
from app.sources.lnb.client import LNBClient
from app.sources.surto_olimpico.client import SurtoOlimpicoClient

log = logging.getLogger(__name__)

_CHAVE_LEN = 60


def _normalizar_titulo(titulo: str) -> str:
    t = titulo.lower()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _chave_dedup(n: Noticia) -> str:
    return _normalizar_titulo(n.titulo)[:_CHAVE_LEN]


def _ordenar_por_data(noticias: list[Noticia]) -> list[Noticia]:
    epoch_zero = datetime(1970, 1, 1, tzinfo=timezone.utc)

    def chave(n: Noticia) -> datetime:
        d = n.publicado_em or epoch_zero
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d

    return sorted(noticias, key=chave, reverse=True)


def _deduplicar(listas_em_ordem: list[list[Noticia]]) -> list[Noticia]:
    """Funde listas preservando prioridade (primeira lista vence)."""
    vistas: dict[str, Noticia] = {}
    for lista in listas_em_ordem:
        for n in lista:
            k = _chave_dedup(n)
            if k not in vistas:
                vistas[k] = n
    return list(vistas.values())


def _buscar_fonte(nome: str, fn, erros: list[str]) -> list[Noticia]:
    """Wrapper que captura exceções e anota o erro."""
    try:
        return fn()
    except Exception as e:
        log.warning("Falha %s: %s", nome, e)
        erros.append(f"{nome}: {e}")
        return []


def ultimas_noticias_nbb(
    lnb: LNBClient,
    ge: GEClient,
    surto: SurtoOlimpicoClient,
    liga: League = League.NBB,
    limite: int = 5,
) -> ListaNoticias:
    """Radar NBB: funde LNB + GE + Surto Olímpico.

    Prioridade em caso de duplicata: LNB > GE > Surto.
    """
    erros: list[str] = []

    # Prioridade: LNB (oficial) > GE (grande cobertura) > Surto (cobertura de nicho)
    noticias_lnb = _buscar_fonte("lnb", lambda: lnb.noticias(liga), erros)
    noticias_ge = _buscar_fonte("ge", lambda: ge.nbb(liga), erros)
    noticias_surto = _buscar_fonte("surto", lambda: surto.buscar(liga), erros)

    fundidas = _deduplicar([noticias_lnb, noticias_ge, noticias_surto])
    ordenadas = _ordenar_por_data(fundidas)
    recorte = ordenadas[:limite]

    erro_final = "; ".join(erros) if (erros and not recorte) else None
    return ListaNoticias(liga=liga, noticias=recorte, erro=erro_final)


def ultimas_noticias_ldb(
    lnb: LNBClient,
    limite: int = 5,
) -> ListaNoticias:
    """Radar LDB: só LNB (por enquanto)."""
    try:
        noticias = lnb.noticias(League.LDB)
    except Exception as e:
        log.warning("Falha LNB (LDB): %s", e)
        return ListaNoticias(liga=League.LDB, noticias=[], erro=f"lnb: {e}")

    ordenadas = _ordenar_por_data(noticias)
    return ListaNoticias(liga=League.LDB, noticias=ordenadas[:limite])


def ultimas_noticias_ouro(
    lnb: LNBClient,
    limite: int = 5,
) -> ListaNoticias:
    """Radar Liga Ouro: só LNB."""
    try:
        noticias = lnb.noticias(League.OURO)
    except Exception as e:
        log.warning("Falha LNB (Ouro): %s", e)
        return ListaNoticias(liga=League.OURO, noticias=[], erro=f"lnb: {e}")

    ordenadas = _ordenar_por_data(noticias)
    return ListaNoticias(liga=League.OURO, noticias=ordenadas[:limite])


def ultimas_noticias_google(
    google,
    query: str,
    liga: League = League.GERAL,
    limite: int = 5,
) -> ListaNoticias:
    """Mantido para /api/noticias e /api/nba (NBA ainda usa Google News)."""
    try:
        noticias = google.buscar(query, liga)
    except Exception as e:
        log.warning("Falha ao buscar notícias (query=%s): %s", query, e)
        return ListaNoticias(liga=liga, noticias=[], erro=f"google_news: {e}")

    ordenadas = _ordenar_por_data(noticias)
    return ListaNoticias(liga=liga, noticias=ordenadas[:limite])