"""Serviço de notícias: funde fontes, deduplica, ordena.

Duas funções públicas:
- `ultimas_noticias(lnb, google, liga, limite)` — Radar NBB (LNB + Google News).
- `ultimas_noticias_google(google, query, liga, limite)` — Agregado geral
  (só Google News, query livre tipo 'basquete').

Regra de deduplicação:
1. Normalizar o título (minúsculas, sem acentos, sem pontuação).
2. Pegar os primeiros 60 caracteres como "impressão digital".
3. Se duas notícias compartilham a impressão, mantém a de MAIOR prioridade.
4. Prioridade: LNB > Google News.

Ordenação: por `publicado_em` desc (mais recentes primeiro).
"""

import logging
import re
import unicodedata
from datetime import datetime, timezone

from app.models import League, ListaNoticias, Noticia
from app.sources.google_news.client import GoogleNewsClient
from app.sources.lnb.client import LNBClient

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
    vistas: dict[str, Noticia] = {}
    for lista in listas_em_ordem:
        for n in lista:
            k = _chave_dedup(n)
            if k not in vistas:
                vistas[k] = n
    return list(vistas.values())


def ultimas_noticias(
    lnb: LNBClient,
    google: GoogleNewsClient,
    liga: League,
    limite: int = 4,
) -> ListaNoticias:
    """Funde LNB + Google News, deduplica, ordena e corta.

    Notícias da LNB vêm com imagem (scraper direto do HTML).
    Notícias do Google News vêm sem imagem — o frontend mostra um placeholder
    colorido com a sigla da liga.
    """
    noticias_lnb: list[Noticia] = []
    noticias_google: list[Noticia] = []
    erros: list[str] = []

    try:
        noticias_lnb = lnb.noticias(liga)
    except Exception as e:
        log.warning("Falha ao buscar notícias da LNB: %s", e)
        erros.append(f"lnb: {e}")

    try:
        noticias_google = google.buscar("nbb", liga)
    except Exception as e:
        log.warning("Falha ao buscar notícias do Google News: %s", e)
        erros.append(f"google_news: {e}")

    fundidas = _deduplicar([noticias_lnb, noticias_google])
    ordenadas = _ordenar_por_data(fundidas)
    recorte = ordenadas[:limite]

    erro_final = "; ".join(erros) if (erros and not recorte) else None
    return ListaNoticias(liga=liga, noticias=recorte, erro=erro_final)


def ultimas_noticias_google(
    google: GoogleNewsClient,
    query: str,
    liga: League = League.GERAL,
    limite: int = 5,
) -> ListaNoticias:
    """Busca notícias do Google News por query livre.

    Usado pelo agregado geral da seção "Últimas Notícias" (ex: query='basquete').
    Ordena por data desc e corta no limite.
    """
    try:
        noticias = google.buscar(query, liga)
    except Exception as e:
        log.warning("Falha ao buscar notícias (query=%s): %s", query, e)
        return ListaNoticias(liga=liga, noticias=[], erro=f"google_news: {e}")

    ordenadas = _ordenar_por_data(noticias)
    return ListaNoticias(liga=liga, noticias=ordenadas[:limite])

def ultimas_noticias_lnb(
    lnb: LNBClient,
    liga: League,
    limite: int = 5,
) -> ListaNoticias:
    """Busca notícias só da LNB (scraping direto). Sem Google News.

    Usado por ligas que ainda não têm cobertura boa no Google News
    (ex: Liga Ouro).
    """
    try:
        noticias = lnb.noticias(liga)
    except Exception as e:
        log.warning("Falha LNB (%s): %s", liga.value, e)
        return ListaNoticias(liga=liga, noticias=[], erro=f"lnb: {e}")

    ordenadas = _ordenar_por_data(noticias)
    return ListaNoticias(liga=liga, noticias=ordenadas[:limite])

def ultimas_noticias_ldb(
    lnb: LNBClient,
    google: GoogleNewsClient,
    liga: League = League.LDB,
    limite: int = 5,
) -> ListaNoticias:
    """Funde LNB (categoria LDB) + Google News (query 'LDB basquete').

    Mesma lógica do NBB: dedup com LNB vencendo.
    """
    noticias_lnb: list[Noticia] = []
    noticias_google: list[Noticia] = []
    erros: list[str] = []

    try:
        noticias_lnb = lnb.noticias(liga)
    except Exception as e:
        log.warning("Falha LNB (%s): %s", liga.value, e)
        erros.append(f"lnb: {e}")

    try:
        noticias_google = google.buscar("LDB basquete", liga)
    except Exception as e:
        log.warning("Falha Google News (LDB): %s", e)
        erros.append(f"google_news: {e}")

    fundidas = _deduplicar([noticias_lnb, noticias_google])
    ordenadas = _ordenar_por_data(fundidas)
    recorte = ordenadas[:limite]

    erro_final = "; ".join(erros) if (erros and not recorte) else None
    return ListaNoticias(liga=liga, noticias=recorte, erro=erro_final)