#!/usr/bin/env python3
"""Smoke test das fontes reais: cada liga responde? O parser ainda entende o formato?

    python scripts/check_sources.py            # jogos de hoje, todas as ligas
    python scripts/check_sources.py --standings

Sai com código 1 se alguma fonte falhar. Rode de vez em quando (ou num cron/CI agendado):
é o alarme para "o site mudou o layout e o parser quebrou".
(Substitui o `check_api_key.py` do rascunho: as fontes atuais não usam API key.)
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.exceptions import BasqueteleiroError  # noqa: E402
from app.sources.registry import SourceRegistry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--standings", action="store_true", help="também testa a classificação"
    )
    args = parser.parse_args()

    registry = SourceRegistry()
    failures = 0
    for league in registry.leagues():
        source = registry.get(league)
        checks = [("jogos", lambda s=source: f"{len(s.games(s.today()))} jogo(s) hoje")]
        if args.standings:
            checks.append(
                (
                    "classificação",
                    lambda s=source: (
                        f"{sum(len(g.rows) for g in s.standings().groups)} times"
                    ),
                )
            )
        for label, fn in checks:
            started = time.monotonic()
            try:
                detail, ok = fn(), True
            except BasqueteleiroError as exc:
                detail, ok = f"{type(exc).__name__}: {exc}", False
            failures += not ok
            print(
                f"{'OK  ' if ok else 'FAIL'} {league.value:<4} {label:<14} "
                f"{time.monotonic() - started:5.1f}s  {detail}"
            )
    registry.close()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
