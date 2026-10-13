"""Rate limiter (token bucket) thread-safe."""

import threading
import time
from collections.abc import Callable


class RateLimiter:
    """Controla a vazão de requisições a um host.

    `rate` = fichas por segundo; `burst` = quantas podem sair "de uma vez".
    `acquire()` reserva uma ficha e dorme (fora do lock) se for preciso esperar.
    Relógio e sleep são injetáveis para testar sem esperar de verdade.
    """

    def __init__(
        self,
        rate: float,
        burst: int = 1,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if rate <= 0:
            raise ValueError("rate deve ser > 0")
        if burst < 1:
            raise ValueError("burst deve ser >= 1")
        self.rate = rate
        self.burst = burst
        self._clock = clock
        self._sleep = sleep
        self._tokens = float(burst)
        self._updated = clock()
        self._lock = threading.Lock()

    def acquire(self) -> float:
        """Bloqueia até poder prosseguir. Retorna quantos segundos esperou."""
        with self._lock:
            now = self._clock()
            self._tokens = min(
                self.burst,
                self._tokens + (now - self._updated) * self.rate,
            )
            self._updated = now
            self._tokens -= 1.0
            wait = -self._tokens / self.rate if self._tokens < 0 else 0.0
        if wait > 0:
            self._sleep(wait)
        return wait