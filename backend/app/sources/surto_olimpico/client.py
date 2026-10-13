"""Cliente do Surto Olímpico via API pública do Supabase.

O site surtoolimpico.com.br usa Supabase por trás. A API REST deles é
pública (chave 'anon' exposta no frontend). A gente consome direto,
sem scraping de HTML.
"""

import logging
from datetime import datetime, timezone

from app.core.base import BaseAPI
from app.core.config import get_settings
from app.models import League, Noticia

log = logging.getLogger(__name__)

QUERIES_POR_LIGA = {
    League.NBB: "nbb",
    League.LDB: "ldb",
    League.OURO: "liga ouro",
    League.NBA: "nba",
}


class SurtoOlimpicoClient(BaseAPI):
    name = "surto_olimpico"
    user_agent = "basqueteleiro/0.1 (+https://github.com/SEU-USUARIO/basqueteleiro)"

    def __init__(self, *, rate: float = 1.0, **kwargs):
        # Lê as credenciais do .env (via pydantic-settings)
        settings = get_settings()
        self.base_url = settings.surto_supabase_url
        self.apikey = settings.surto_supabase_key

        if not self.base_url or not self.apikey:
            log.warning(
                "surto_olimpico: SURTO_SUPABASE_URL/KEY não configurados — cliente desabilitado"
            )

        super().__init__(rate=rate, **kwargs)

    def habilitado(self) -> bool:
        return bool(self.base_url and self.apikey)

    def buscar(
        self,
        liga: League = League.NBB,
        query: str | None = None,
        limite: int = 24,
    ) -> list[Noticia]:
        if not self.habilitado():
            log.debug("surto_olimpico: cliente desabilitado (env ausente)")
            return []

        q = query or QUERIES_POR_LIGA.get(liga, "nbb")

        params = {
            "select": (
                "id,slug,title,excerpt,author,image_url,"
                "published_at,categories,subcategories,sport_slug"
            ),
            "status": "eq.published",
            "order": "published_at.desc",
            "limit": str(limite),
            "or": f"(title.ilike.%{q}%,excerpt.ilike.%{q}%,plain_text.ilike.%{q}%)",
        }
        headers = {
            "apikey": self.apikey,
            "accept-profile": "public",
        }

        try:
            data = self.get_json("/rest/v1/articles", params=params, headers=headers)
        except Exception as e:
            log.warning("surto_olimpico: falha na API (%s)", e)
            return []

        if not isinstance(data, list):
            log.warning("surto_olimpico: resposta inesperada (não é lista)")
            return []

        return [self._adaptar(item, liga) for item in data]

    def _adaptar(self, item: dict, liga: League) -> Noticia:
        slug = item.get("slug") or ""
        url = f"https://surtoolimpico.com.br/artigo/{slug}"

        publicado_em = None
        data_iso = None
        data_texto = None
        pub = item.get("published_at")
        if pub:
            try:
                dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt = dt.astimezone(timezone.utc)
                publicado_em = dt
                data_iso = dt.isoformat()
                data_texto = dt.strftime("%d/%m/%Y %H:%M")
            except (ValueError, TypeError):
                pass

        return Noticia(
            id=slug,
            liga=liga,
            titulo=item.get("title") or "",
            url=url,
            resumo=item.get("excerpt") or None,
            imagem_url=item.get("image_url") or None,
            categoria="Surto Olímpico",
            data_iso=data_iso,
            data_texto=data_texto,
            publicado_em=publicado_em,
        )