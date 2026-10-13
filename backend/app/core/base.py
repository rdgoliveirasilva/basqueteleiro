"""BaseAPI: HTTP client reutilizável com retry, rate limit e user-agent."""

import json
import logging
import time
from collections.abc import Mapping
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.cache import MISSING, TTLCache
from app.core.exceptions import (
    ParseError,
    SourceError,
    SourceUnavailableError,
)
from app.core.ratelimit import RateLimiter

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
        cache: TTLCache | None = None,
        limiter: RateLimiter | None = None,
    ) -> None:
        self.timeout = timeout
        self.cache = cache if cache is not None else TTLCache()
        self.limiter = limiter if limiter is not None else RateLimiter(rate, burst=1)
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
                "Accept": "application/json, text/html, application/xml;q=0.9, */*;q=0.8",
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

    def _url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    @staticmethod
    def _cache_key(kind: str, url: str, params: Mapping[str, Any] | None) -> str:
        import json as _json
        p = _json.dumps(params, sort_keys=True, default=str) if params else ""
        return f"{kind}|{url}|{p}"

    def _fetch(
        self,
        kind: str,
        path: str,
        params: Mapping[str, Any] | None,
        ttl: float,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        url = self._url(path)
        key = self._cache_key(kind, url, params)

        if ttl > 0:
            hit = self.cache.get(key, MISSING)
            if hit is not MISSING:
                log.debug("%s: cache hit %s", self.name, url)
                return hit

        self._throttle()
        log.debug("%s: GET %s", self.name, url)
        try:
            resp = self.session.get(
                url, params=params, headers=headers, timeout=self.timeout
            )
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

        if kind == "json":
            try:
                value: Any = resp.json()
            except ValueError as exc:
                raise ParseError(
                    f"{self.name}: resposta não é JSON válido",
                    source=self.name,
                    url=url,
                ) from exc
        else:
            if "charset" not in resp.headers.get("content-type", "").lower():
                resp.encoding = "utf-8"
            value = resp.text

        if ttl > 0:
            self.cache.set(key, value, ttl)
        return value

    def get_text(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        *,
        ttl: float = 0,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        """GET + devolve o corpo como texto (utf-8 garantido)."""
        return self._fetch("text", path, params, ttl, headers)

    def get_json(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        *,
        ttl: float = 0,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """GET + devolve o corpo como JSON (dict/list)."""
        return self._fetch("json", path, params, ttl, headers)