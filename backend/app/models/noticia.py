from datetime import datetime

from pydantic import BaseModel

from app.models.enums import League


class Noticia(BaseModel):
    """Notícia de qualquer liga, num formato único."""

    id: str
    liga: League
    titulo: str
    url: str
    resumo: str | None = None
    imagem_url: str | None = None
    categoria: str | None = None
    data_iso: str | None = None
    data_texto: str | None = None
    publicado_em: datetime | None = None


class ListaNoticias(BaseModel):
    liga: League
    noticias: list[Noticia]
    erro: str | None = None
