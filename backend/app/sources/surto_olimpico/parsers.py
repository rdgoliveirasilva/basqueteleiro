"""HTML do Surto Olímpico -> modelo Noticia.

Estrutura do site (Tailwind):
  <article class="card-lift ...">
    <a href="/artigo/slug"> <img src="..."> </a>
    <h3><a class="headline-link" href="/artigo/slug">Título</a></h3>
    <p class="line-clamp-2">Resumo</p>
    <time datetime="2026-10-12T19:30:00+00:00">5 h</time>
    <span>Autor</span>
  </article>
"""

import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.core.exceptions import ParseError
from app.models import League, Noticia
from app.sources.surto_olimpico.selectors import SELECTORS, SurtoSelectors

BASE_URL = "https://surtoolimpico.com.br"

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


def _parse_iso_data(texto: str | None) -> tuple[Optional[str], Optional[datetime]]:
    """Converte '2026-10-12T19:30:00+00:00' -> ISO + datetime UTC."""
    if not texto:
        return None, None
    try:
        dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        return dt.isoformat(), dt
    except (ValueError, TypeError):
        return None, None


def _slug_da_url(url: str) -> str:
    partes = [p for p in url.rstrip("/").split("/") if p]
    return partes[-1] if partes else url


def _parse_card(card: Tag, liga: League, base_url: str = BASE_URL) -> Optional[Noticia]:
    link_el = card.select_one(SELECTORS.link)
    if not link_el or not link_el.get("href"):
        return None

    href = str(link_el["href"]).strip()
    url = urljoin(base_url, href)

    titulo = _normalizar(link_el.get_text(" ")) or None
    if not titulo:
        return None

    # imagem
    img_el = card.select_one(SELECTORS.imagem)
    imagem_url = None
    if img_el is not None:
        src = img_el.get(SELECTORS.imagem_src_attr)
        if src:
            imagem_url = str(src).strip()

    # data ISO
    data_iso_el = card.select_one(SELECTORS.data_iso)
    data_iso = None
    dt = None
    if data_iso_el is not None:
        data_iso, dt = _parse_iso_data(data_iso_el.get(SELECTORS.data_iso_attr))

    return Noticia(
        id=_slug_da_url(url),
        liga=liga,
        titulo=titulo,
        url=url,
        resumo=_extrair_texto(card, SELECTORS.resumo),
        imagem_url=imagem_url,
        categoria="Surto Olímpico",
        data_iso=data_iso,
        data_texto=None,
        publicado_em=dt,
    )


def parse_noticias(
    html: str,
    liga: League = League.NBB,
    selectors: SurtoSelectors = SELECTORS,
    base_url: str = BASE_URL,
) -> list[Noticia]:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select(selectors.card)
    if not cards:
        raise ParseError(
            f"surto_olimpico: nenhum card encontrado — seletores desatualizados?",
            source="surto_olimpico",
        )

    noticias: list[Noticia] = []
    for card in cards:
        n = _parse_card(card, liga, base_url)
        if n is not None:
            noticias.append(n)
    return noticias