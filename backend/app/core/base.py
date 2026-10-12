"""BaseAPI: HTTP client reutilizável com retry, rate limit e user-agent."""

import logging
import time
from collections.abc import Mapping
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.exceptions import SourceError, SourceUnavailableError

log = logging.getLogger(__name__)


class BaseAPI:
    name: str = "base"
    base_url: str = ""
    user_agent: str = "basqueteleiro/0.1"

    def __init__(
        self,
        *,
        rate: float = 1.0,
        timeout: float = 15.0,
        retries: int = 3,
    ) -> None:
        self.timeout = timeout
        self._min_interval = 1.0 / rate if rate > 0 else 0.0
        self._last_call = 0.0

        retry = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            }
        )

    def close(self) -> None:
        self.session.close()

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.monotonic()

    def get_text(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        """GET + devolve o corpo como texto (utf-8 garantido)."""
        self._throttle()
        url = self._url(path)
        log.debug("%s: GET %s", self.name, url)
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise SourceUnavailableError(
                f"{self.name}: falha de rede ({exc.__class__.__name__})",
                source=self.name,
                url=url,
            ) from exc

        if resp.status_code >= 500:
            raise SourceUnavailableError(
                f"{self.name}: fonte indisponível ({resp.status_code})",
                source=self.name,
                url=url,
                status_code=resp.status_code,
            )
        if resp.status_code >= 400:
            raise SourceError(
                f"{self.name}: HTTP {resp.status_code}",
                source=self.name,
                url=url,
                status_code=resp.status_code,
            )

        if "charset" not in resp.headers.get("content-type", "").lower():
            resp.encoding = "utf-8"
        return resp.text

    def _url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
