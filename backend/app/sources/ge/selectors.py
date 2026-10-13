"""Seletores CSS do GE (ge.globo.com)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GESelectors:
    card: str = ".bastian-feed-item"
    link: str = "h2 > a.feed-post-link"
    titulo: str = "h2 > a.feed-post-link p"
    imagem: str = ".bstn-fd-picture-image"
    imagem_src_attr: str = "src"
    resumo: str = ".feed-post-body-resumo p"
    data: str = ".feed-post-datetime"


SELECTORS = GESelectors()