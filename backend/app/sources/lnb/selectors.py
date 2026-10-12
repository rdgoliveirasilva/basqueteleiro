"""Seletores CSS do site da LNB. ÚNICO lugar que conhece o HTML.
Se o site mudar, só este arquivo muda.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LNBSelectors:
    card: str = ".noticias_jogadores"
    link: str = "a[href]"
    imagem: str = ".noticias_jogadores_img img"
    imagem_src_attr: str = "src"
    categoria: str = ".cat_nbb a strong"
    titulo: str = ".titulo_noticias_jogadores b"
    resumo: str = ".conteudo_noticias_jogadores"
    data: str = ".date_cat"


SELECTORS = LNBSelectors()
