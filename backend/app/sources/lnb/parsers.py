"""HTML da LNB -> modelos. Funções puras, sem I/O — fáceis de testar."""

import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup, Tag

from app.core.exceptions import ParseError
from app.models import League, Noticia
from app.sources.lnb.selectors import SELECTORS, LNBSelectors

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


def _parse_data_br(texto: str | None) -> tuple[Optional[str], Optional[datetime]]:
    if not texto:
        return None, None
    texto = texto.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            dt = datetime.strptime(texto, fmt)
            return dt.strftime("%Y-%m-%d"), dt
        except ValueError:
            continue
    return None, None


def _slug_da_url(url: str) -> str:
    partes = [p for p in url.rstrip("/").split("/") if p]
    return partes[-1] if partes else url


def _parse_card(card: Tag, liga: League) -> Optional[Noticia]:
    link_el = card.select_one(SELECTORS.link)
    if not link_el or not link_el.get("href"):
        return None
    url = str(link_el["href"]).strip()

    titulo = _extrair_texto(card, SELECTORS.titulo)
    if not titulo:
        return None

    img_el = card.select_one(SELECTORS.imagem)
    imagem_url = None
    if img_el is not None:
        src = img_el.get(SELECTORS.imagem_src_attr)
        if src:
            imagem_url = str(src).strip()

    data_texto = _extrair_texto(card, SELECTORS.data)
    data_iso, dt = _parse_data_br(data_texto)

    return Noticia(
        id=_slug_da_url(url),
        liga=liga,
        titulo=titulo,
        url=url,
        resumo=_extrair_texto(card, SELECTORS.resumo),
        imagem_url=imagem_url,
        categoria=_extrair_texto(card, SELECTORS.categoria),
        data_texto=data_texto,
        data_iso=data_iso,
        publicado_em=dt,
    )


def parse_noticias(
    html: str,
    liga: League = League.NBB,
    selectors: LNBSelectors = SELECTORS,
) -> list[Noticia]:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select(selectors.card)
    if not cards:
        raise ParseError(
            f"{liga.value}: nenhum card de notícia encontrado — "
            "os seletores em sources/lnb/selectors.py estão desatualizados?"
        )

    noticias: list[Noticia] = []
    for card in cards:
        n = _parse_card(card, liga)
        if n is not None:
            noticias.append(n)
    return noticias
