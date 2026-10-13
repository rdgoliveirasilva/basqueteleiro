"""Cache em memória com TTL e limite de tamanho (LRU)."""

import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

# MARCADOR: distingue "não está no cache" de "o valor cacheado é None"
MISSING = object()


class TTLCache:
    def __init__(
        self,
        maxsize: int = 512,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.maxsize = maxsize
        self._clock = clock
        self._data: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return default
            expires_at, value = item
            if expires_at <= self._clock():
                del self._data[key]
                return default
            self._data.move_to_end(key)
            return value

    def set(self, key: str, value: Any, ttl: float) -> None:
        if ttl <= 0:
            return
        with self._lock:
            self._data[key] = (self._clock() + ttl, value)
            self._data.move_to_end(key)
            while len(self._data) > self.maxsize:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        return len(self._data)