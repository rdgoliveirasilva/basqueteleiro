# Uso

## Configuração (`.env`)

Veja `.env.example`. Principais variáveis: `CORS_ORIGINS`, `USER_AGENT`, `HTTP_TIMEOUT`,
`HTTP_RETRIES`, `NBA_RATE`, `LNB_RATE` (req/s) e `CACHE_TTL_*` (segundos).

## Exemplos

```bash
curl "http://127.0.0.1:8000/api/nba/jogos?data=2025-10-22"
curl  http://127.0.0.1:8000/api/nbb/classificacao
curl  http://127.0.0.1:8000/api/home
```

Resposta de `/jogos` (resumida):

```json
{
  "league": "nba", "day": "2025-10-22", "count": 3, "error": null,
  "games": [{
    "id": "0022500002", "league": "nba", "status": "live",
    "start_time": "2025-10-23T02:00:00Z", "status_text": "Q3 5:12", "period": 3, "clock": "05:12",
    "venue": null,
    "home": {"team": {"id": "1610612747", "name": "Lakers", "short_name": "LAL", "...": "..."},
             "score": 72, "record": "0-0", "periods": [25, 24, 23]},
    "away": {"team": {"...": "..."}, "score": 70, "record": "0-0", "periods": [22, 26, 22]}
  }]
}
```

`status`: `scheduled | live | final | postponed | canceled`. `start_time` é sempre UTC.

## Usando como biblioteca (sem HTTP)

```python
from datetime import date
from app.sources.registry import SourceRegistry
from app.models import League

registry = SourceRegistry()
for g in registry.get(League.NBA).games(date(2025, 10, 22)):
    print(g.away.team.name, g.away.score, "@", g.home.team.name, g.home.score)
```

## Testes e qualidade

```bash
cd backend
pytest              # sem rede: tudo mockado com `responses` + fixtures
ruff check . && ruff format --check .
python ../scripts/check_sources.py --standings   # COM rede: testa as fontes reais
```
