class BasqueteleiroError(Exception):
    """Base de todos os erros do projeto."""


class SourceError(BasqueteleiroError):
    """Algo deu errado ao falar com uma fonte externa."""

    def __init__(
        self,
        message: str,
        *,
        source: str | None = None,
        url: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.source = source
        self.url = url
        self.status_code = status_code


class SourceUnavailableError(SourceError):
    """Rede, timeout ou 5xx."""


class ParseError(SourceError):
    """A resposta chegou, mas o formato mudou."""
