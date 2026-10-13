"""HTML do GE Basquete -> modelo Noticia.

Estrutura do site:
  <div class="bastian-feed-item" data-type="materia">
    <h2><a class="feed-post-link" href="..."><p>Título</p></a></h2>
    <div class="feed-post-body-resumo"><p>Resumo</p></div>
    <img class="bstn-fd-picture-image" src="...">
    <span class="feed-post-datetime">Há 7 dias</span>
  </div>
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.core.exceptions import ParseError
from app.models import League, Noticia
from app.sources.ge.selectors import SELECTORS, GESelectors

log = logging.getLogger(__name__)

BASE_URL = "https://ge.globo.com"

_RE_WS = re.compile(r"\s+")


def _normalizar(texto: str | None) -> str:
    return _RE_WS.sub(" ", texto or "").strip()


def _extrair_texto(node: Tag | None, seletor: str) -> Optional[str]:
    if node is None:
        return None
    el = node.select_one(seletor)
    if el is None:
        return None
    return _normalizar(el.get_text(" ")) or None


def _parse_data_relativa(texto: str | None) -> Optional[datetime]:
    """Converte 'Há 7 dias', 'Há 3 horas', 'Agora' em datetime UTC aproximado."""
    if not texto:
        return None

    t = texto.lower().strip()
    agora = datetime.now(timezone.utc)

    if "agora" in t or "poucos" in t:
        return agora

    m = re.search(r"há\s+(\d+)\s+(minuto|hora|dia|semana|mês|mes|ano)", t)
    if not m:
        return None

    n = int(m.group(1))
    unidade = m.group(2)

    if unidade.startswith("minuto"):
        return agora - timedelta(minutes=n)
    if unidade.startswith("hora"):
        return agora - timedelta(hours=n)
    if unidade.startswith("dia"):
        return agora - timedelta(days=n)
    if unidade.startswith("semana"):
        return agora - timedelta(weeks=n)
    if unidade in ("mês", "mes"):
        return agora - timedelta(days=30 * n)
    if unidade.startswith("ano"):
        return agora - timedelta(days=365 * n)
    return None


def _slug_da_url(url: str) -> str:
    partes = [p for p in url.rstrip("/").split("/") if p]
    return partes[-1].replace(".ghtml", "") if partes else url


def _parse_card(card: Tag, liga: League, base_url: str = BASE_URL) -> Optional[Noticia]:
    link_el = card.select_one(SELECTORS.link)
    if not link_el or not link_el.get("href"):
        return None

    href = str(link_el["href"]).strip()
    url = urljoin(base_url, href)

    titulo = _extrair_texto(card, SELECTORS.titulo) or _normalizar(link_el.get_text(" ")) or None
    if not titulo:
        return None

    img_el = card.select_one(SELECTORS.imagem)
    imagem_url = None
    if img_el is not None:
        src = img_el.get(SELECTORS.imagem_src_attr)
        if src:
            imagem_url = str(src).strip()

    data_texto = _extrair_texto(card, SELECTORS.data)
    dt = _parse_data_relativa(data_texto)

    return Noticia(
        id=_slug_da_url(url),
        liga=liga,
        titulo=titulo,
        url=url,
        resumo=_extrair_texto(card, SELECTORS.resumo),
        imagem_url=imagem_url,
        categoria="GE",
        data_iso=dt.isoformat() if dt else None,
        data_texto=data_texto,
        publicado_em=dt,
    )


def parse_noticias(
    html: str,
    liga: League = League.NBB,
    selectors: GESelectors = SELECTORS,
    base_url: str = BASE_URL,
) -> list[Noticia]:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select(selectors.card)
    if not cards:
        raise ParseError(
            f"ge: nenhum card encontrado — seletores desatualizados?",
            source="ge",
        )

    noticias: list[Noticia] = []
    for card in cards:
        n = _parse_card(card, liga, base_url)
        if n is not None:
            noticias.append(n)
    return noticias