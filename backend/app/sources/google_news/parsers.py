"""Parse do RSS do Google News.

O Google News devolve um XML com <item>s. Cada item tem:
  <title>       Título — Fonte
  <link>        URL do Google News (opaca, precisa ser decodificada)
  <pubDate>     Data em formato RFC 822
  <source>      Nome do site original (LNB, GE, ESPN...)
  <description> Trecho da matéria (às vezes com HTML)

Para imagens, usamos googlenewsdecoder + og:image da matéria real.
"""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.models import League, Noticia


def _id_do_link(url: str) -> str:
    partes = [p for p in url.rstrip("/").split("/") if p]
    return partes[-1][:80] if partes else url


def _limpar_html(texto: str | None) -> str | None:
    if not texto:
        return None
    soup = BeautifulSoup(texto, "html.parser")
    limpo = soup.get_text(" ", strip=True)
    return limpo or None


def _separar_titulo_fonte(titulo_completo: str) -> tuple[str, str | None]:
    if " — " in titulo_completo:
        t, f = titulo_completo.rsplit(" — ", 1)
        return t.strip(), f.strip()
    if " - " in titulo_completo:
        t, f = titulo_completo.rsplit(" - ", 1)
        return t.strip(), f.strip()
    return titulo_completo.strip(), None


def _parse_pubdate(texto: str | None) -> tuple[Optional[str], Optional[str], Optional[datetime]]:
    if not texto:
        return None, None, None
    try:
        dt_utc = parsedate_to_datetime(texto)
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        dt_utc = dt_utc.astimezone(timezone.utc)
        dt_br = dt_utc.astimezone(ZoneInfo("America/Sao_Paulo"))
        return dt_utc.isoformat(), dt_br.strftime("%d/%m/%Y %H:%M"), dt_utc
    except (TypeError, ValueError):
        return None, None, None


def parse_feed(xml_text: str, liga: League = League.NBB) -> list[Noticia]:
    soup = BeautifulSoup(xml_text, "xml")
    itens = soup.find_all("item")
    noticias: list[Noticia] = []

    for item in itens:
        titulo_el = item.find("title")
        link_el = item.find("link")
        pubdate_el = item.find("pubDate")
        source_el = item.find("source")
        desc_el = item.find("description")

        titulo_completo = titulo_el.get_text(strip=True) if titulo_el else ""
        if not titulo_completo:
            continue
        titulo, fonte_do_titulo = _separar_titulo_fonte(titulo_completo)

        url = link_el.get_text(strip=True) if link_el else ""
        if not url:
            continue

        fonte = source_el.get_text(strip=True) if source_el else fonte_do_titulo
        data_iso, data_texto, dt = _parse_pubdate(
            pubdate_el.get_text(strip=True) if pubdate_el else None
        )

        noticias.append(
            Noticia(
                id=_id_do_link(url),
                liga=liga,
                titulo=titulo,
                url=url,
                resumo=_limpar_html(desc_el.get_text() if desc_el else None),
                imagem_url=None,
                categoria=fonte,
                data_iso=data_iso,
                data_texto=data_texto,
                publicado_em=dt,
            )
        )

    return noticias


# ============================================================
# IMAGENS
# ============================================================

# palavras comuns em nomes de arquivo de logo/placeholder
_PALAVRAS_LOGO = ("logo", "default", "share", "card", "og-default",
                  "placeholder", "fallback", "sprite", "avatar")

# domínios do Google que servem logo/branding, não imagem de matéria
_DOMINIOS_GOOGLE = ("googleusercontent.com", "gstatic.com",
                    "google.com/images", "google.com/logos")


def _url_parece_logo(url: str) -> bool:
    u = url.lower()
    if any(d in u for d in _DOMINIOS_GOOGLE):
        return True
    nome = u.rsplit("/", 1)[-1].split("?", 1)[0]
    return any(p in nome for p in _PALAVRAS_LOGO)


def extrair_og_image(html: str) -> str | None:
    """Extrai a melhor candidata a og:image do HTML de uma matéria.

    Coleta todas as og:image e twitter:image, descarta as que parecem logo,
    e devolve a última que sobrou (a específica costuma vir depois da genérica).
    """
    soup = BeautifulSoup(html, "html.parser")
    candidatas: list[str] = []

    for attr in ("property", "name"):
        for meta in soup.find_all("meta", attrs={attr: "og:image"}):
            c = (meta.get("content") or "").strip()
            if c:
                candidatas.append(c)

    for attr in ("property", "name"):
        for meta in soup.find_all("meta", attrs={attr: "twitter:image"}):
            c = (meta.get("content") or "").strip()
            if c:
                candidatas.append(c)

    if not candidatas:
        return None

    boas = [u for u in candidatas if not _url_parece_logo(u)]
    if boas:
        return boas[-1]

    return candidatas[0]