from app.core.base import BaseAPI
from app.models import League, Noticia
from app.sources.ge import parsers


class GEClient(BaseAPI):
    """Cliente do GE (ge.globo.com) — basquete."""

    name = "ge"
    base_url = "https://ge.globo.com"
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, *, rate: float = 0.5, **kwargs):
        super().__init__(rate=rate, **kwargs)

    def nbb(self, liga: League = League.NBB) -> list[Noticia]:
        """Notícias de NBB no GE."""
        html = self.get_text("/basquete/nbb/")
        return parsers.parse_noticias(html, liga)