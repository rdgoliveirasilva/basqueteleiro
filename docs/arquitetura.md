# Arquitetura

## Camadas (e quem pode depender de quem)

```
api/        HTTP: rotas, schemas, tradução de erros → status        depende de services, models
services/   regras de negócio: agregar ligas, ordenar, isolar falha  depende de sources/registry, models
sources/    um pacote por fonte: client (I/O) + parsers (puros)       depende de core, models
core/       infraestrutura: HTTP base, retry, rate limit, cache, erros   não depende de nada do projeto
models/     formato único de dados (pydantic)                         não depende de nada
```

Dependências só apontam para baixo. Por isso dá para testar cada camada isolada.

## Decisões principais

**1. `client` faz I/O, `parser` é função pura.** O parser recebe JSON/HTML e devolve modelos; os
testes usam fixtures e não precisam de rede. Quando uma fonte muda de formato, o conserto é um
parser + uma fixture nova.

**2. Contrato único (`sources/base.py: Source`).** Toda liga implementa `games(day)` e, se puder,
`standings()` / `box_score()`. O que a fonte não oferece levanta `NotSupportedError` → HTTP 501.
Os services nunca sabem qual liga estão atendendo.

**3. NBB e LDB compartilham código (`sources/lnb/`).** As duas ligas vivem no mesmo site da LNB;
`nbb/` e `ldb/` só definem `league`, `name` e `slug`. Consequência boa: **um único rate limiter**
para o host `lnb.com.br`, em vez de um por liga.

**4. `BaseAPI` concentra o que é chato e repetido:** session com keep-alive, User-Agent
identificável, retry com backoff (429/5xx), rate limit (token bucket), cache TTL e tradução de
falhas para a hierarquia de `exceptions.py`. Cache hit não gasta rate limit.

**5. Falhas parciais.** `/api/home` consulta as ligas em paralelo; se uma cai, ela volta com
`error` preenchido e as outras seguem. Erros de fontes viram 502 com corpo explicativo; formato
inesperado vira `ParseError` (via `@parse_guard`), nunca um 500 com stack trace.

**6. Fuso por liga.** "Dia do jogo" é no fuso da liga: NBA = America/New_York (como a própria NBA
agrupa), NBB/LDB = America/Sao_Paulo. Datas são sempre UTC na saída; o frontend converte.

**7. Injeção de dependência pelo `SourceRegistry`.** Rotas e services recebem o registry; os
testes de API injetam fontes falsas (`app.dependency_overrides`). Nada de globais escondidas
(exceto o singleton `get_registry()`, usado só na ponta).

**8. Seletores isolados.** Todo conhecimento do HTML da LNB está em `lnb/selectors.py`.

## Como adicionar uma liga/fonte nova (ex.: WNBA, Euroliga)

1. `models/enums.py`: novo valor em `League`.
2. `sources/<liga>/`: `client.py` (herda `BaseAPI` + `Source`), `parsers.py`, `endpoints.py`.
3. `sources/registry.py`: uma linha em `default_factories`.
4. `api/routes/<liga>.py`: `router = build_league_router(League.XXX)` + `include_router` em `routes/__init__.py`.
5. Fixture em `tests/fixtures/` + `tests/test_<liga>.py`.
6. Frontend: `services/<liga>.js`, `pages/<LIGA>/`, uma linha em `router.js` e na `Navbar`.

## Limites conhecidos / próximos passos

- Cache em memória, por processo. Com vários workers do uvicorn, cada um tem o seu; para
  compartilhar, implemente a mesma interface de `core/cache.py` sobre Redis.
- Sem proteção contra *cache stampede* (várias requisições idênticas ao mesmo tempo, com cache
  vazio, fazem várias idas à fonte). Resolver com lock por chave quando o tráfego justificar.
- Clientes são síncronos (`requests`); o FastAPI os executa em threadpool. Se precisar de muito
  paralelismo, migrar `BaseAPI` para `httpx.AsyncClient` mexe só no core e nos clients.
- Retries do urllib3 não passam pelo rate limiter (têm backoff próprio).
- Banco de dados: hoje não há. Para histórico (temporadas, estatísticas acumuladas), o próximo
  degrau natural é persistir `Game`/`Standings` (SQLite/Postgres) com um job agendado.
