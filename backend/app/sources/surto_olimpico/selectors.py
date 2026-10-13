"""Seletores CSS do site Surto Olímpico (surtoolimpico.com.br)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SurtoSelectors:
    card: str = "article.card-lift"
    link: str = "h3 > a.headline-link"
    titulo: str = "h3 > a.headline-link"
    imagem: str = "img[src]"
    imagem_src_attr: str = "src"
    resumo: str = "p.line-clamp-2"
    data_iso: str = "time[datetime]"
    data_iso_attr: str = "datetime"
    autor: str = "span.font-medium.text-foreground\\/80"


SELECTORS = SurtoSelectors()