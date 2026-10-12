from app.core.base import BaseAPI
from app.core.exceptions import SourceError
from app.models import League, Noticia
from app.sources.lnb import parsers


class LNBClient(BaseAPI):
    """Cliente da LNB. Notícias por categoria (NBB, Liga Ouro, LDB)."""

    name = "lnb"
    base_url = "https://lnb.com.br"
    user_agent = "basqueteleiro/0.1 (+https://github.com/SEU-USUARIO/basqueteleiro)"

    URLS_NOTICIAS = {
        League.NBB:  "/noticias/categoria/nbb",
        League.OURO: "/noticias/categoria/liga-ouro",
        League.LDB:  "/noticias/categoria/ldb",
    }

    def __init__(self, *, rate: float = 0.5, **kwargs):
        super().__init__(rate=rate, **kwargs)

    def noticias(self, liga: League = League.NBB) -> list[Noticia]:
        path = self.URLS_NOTICIAS.get(liga)
        if path is None:
            raise SourceError(
                f"lnb: liga sem URL de notícias: {liga.value}",
                source=self.name,
            )
        html = self.get_text(path)
        return parsers.parse_noticias(html, liga)