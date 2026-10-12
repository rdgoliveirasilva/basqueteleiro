import logging

from app.core.base import BaseAPI
from app.models import League, Noticia
from app.sources.google_news import parsers

log = logging.getLogger(__name__)


class GoogleNewsClient(BaseAPI):
    """Cliente do Google News RSS + resolutor de imagens.

    O link do RSS é opaco ('news.google.com/rss/articles/CBMi...') — para
    achar a imagem da matéria real, usamos googlenewsdecoder pra extrair a
    URL original, e daí buscamos o HTML e lemos a og:image.
    """

    name = "google_news"
    base_url = "https://news.google.com"
    user_agent = "basqueteleiro/0.1 (+https://github.com/SEU-USUARIO/basqueteleiro)"

    def __init__(self, *, rate: float = 0.5, **kwargs):
        super().__init__(rate=rate, **kwargs)

    def buscar(self, query: str, liga: League = League.NBB) -> list[Noticia]:
        params = {"q": query, "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"}
        xml = self.get_text("/rss/search", params=params)
        return parsers.parse_feed(xml, liga)

    def buscar_og_image(self, url_google_news: str) -> str | None:
        """Resolve o link do Google News e busca a og:image da matéria real."""
        try:
            from googlenewsdecoder import gnewsdecoder
        except ImportError:
            log.warning("googlenewsdecoder não instalado — imagens desativadas")
            return None

        try:
            resultado = gnewsdecoder(url_google_news, interval=0)
            if not resultado.get("status"):
                return None
            url_real = resultado["decoded_url"]

            html = self.get_text(url_real, ttl=900)
            return parsers.extrair_og_image(html)
        except Exception as e:
            log.debug("Falha ao resolver imagem de %s: %s", url_google_news[:60], e)
            return None