# BASQUETELEIRO — Snapshot do Projeto

> Arquivo de contexto para retomar o desenvolvimento em qualquer chat novo.
> Cole este arquivo inteiro e diga o que quer fazer — a IA já vai entender tudo.
> **Última atualização:** 2026-10-13

---

## 1. O que é

**Basqueteleiro** — agregador de notícias de basquete brasileiro e americano.
Wrapper/scraper de múltiplas fontes que normaliza num formato único e expõe
via API própria + site.

Slogan: **"Uma dose diária de basquete"**

Cobertura: **NBB, Liga Ouro, LDB, NBA**. Radar NBB é multi-fonte (LNB + GE +
Surto Olímpico); os outros ainda usam poucas fontes.

---

## 2. Stack

### Backend
- **Python 3.12.7** (venv em `.venv/`)
- **FastAPI** + **uvicorn** — servidor HTTP
- **requests** + **beautifulsoup4** + **lxml** — scraping HTML
- **pydantic** + **pydantic-settings** — modelos e leitura de `.env`
- **tzdata** — fusos horários no Windows (obrigatório)

### Frontend
- **HTML + CSS + JavaScript puro** (sem framework, sem bundler)
- **Bootstrap 5.3** (CDN) — grid, utilidades
- **Motion One** (`@motionone/dom`, CDN) — animações
- **Live Server do VSCode** — serve o `index.html` local (porta 5500)

### Fontes de dados ativas
- **LNB** (`lnb.com.br/noticias/categoria/{nbb,liga-ouro,ldb}`) — HTML server-side
- **GE** (`ge.globo.com/basquete/nbb/`) — HTML server-side
- **Surto Olímpico** — API pública do Supabase (JSON)
- **Google News RSS** — usado só em `/api/noticias` (agregado) e `/api/nba/noticias`

---

## 3. Identidade visual

Paleta (verde + amarelo + laranja, da logo):
```
--verde-escuro:  #0B3D2E   (fundo principal)
--verde-medio:   #114A38   (cards)
--verde-claro:   #1B5E48   (bordas)
--verde-brilho:  #2E8B67   (hover / LDB)
--amarelo:       #F2C10E   (NBB / destaque)
--amarelo-suave: #FFD84D
--laranja:       #F26B21   (NBA / live)
--laranja-suave: #FF8A4C
--branco:        #FFFFFF
```

Fontes:
- **Anton** (títulos grandes / display)
- **Inter** (corpo de texto)

Cores por liga:
- **NBB** → amarelo
- **Liga Ouro** → dourado `#D4AF37`
- **LDB** → verde-brilho `#2E8B67`
- **NBA** → laranja
- **Geral/BR** → cinza-verde

Regra de ouro: **todo texto é branco** (`#FFFFFF !important`).

Assets em `frontend/src/assets/`:
- `hero-bg.png` — imagem de fundo do hero
- `logo.png` — logo (hero + favicon)
- `logo.svg`, `times/` — resquícios, não usados pelo HTML atual

---

## 4. Arquitetura

```
fontes externas → sources/ → services/ → api/ → frontend/
 (LNB, GE,       scrapers    regras     FastAPI   HTML
  Surto, Google) + parsers   + dedup
```

### Camadas (dependências só apontam para baixo)

```
api/        rotas HTTP, schemas, tradução de erros → status
services/   regras de negócio (fusão, dedup, ordenação)
sources/    clientes HTTP + parsers puros
core/       infra (BaseAPI, cache, rate limit, exceptions, config)
models/     formato único (pydantic)
```

### Fluxo do Radar NBB

```
GET /api/nbb/noticias?limite=5
  → routes/nbb.py::noticias()
  → services/noticias.py::ultimas_noticias_nbb()
      → LNBClient.noticias(NBB)              → lnb.com.br (HTML)
      → GEClient.nbb()                       → ge.globo.com (HTML)
      → SurtoOlimpicoClient.buscar(NBB)      → Supabase (JSON)
      → _deduplicar([lnb, ge, surto])        (LNB > GE > Surto)
      → _ordenar_por_data()
      → [:limite]
  → JSON: { liga, noticias: [...], erro }
```

---

## 5. Árvore de arquivos atual

```
basqueteleiro/
├── .env                          ← LOCAL (no .gitignore)
├── .env.example                  ← vai pro Git (com placeholders)
├── .gitignore
├── README.md
├── basqueteleiro_snapshot.md     ← ESTE ARQUIVO
├──
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py               (FastAPI + CORS)
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── base.py           (BaseAPI: session, retry, throttle, headers)
│       │   ├── cache.py          (TTLCache + MISSING)
│       │   ├── config.py         (Settings lê .env)
│       │   ├── exceptions.py     (hierarquia de erros)
│       │   └── ratelimit.py      (RateLimiter token bucket)
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── enums.py          (League: NBB, LDB, OURO, NBA, GERAL)
│       │   └── noticia.py        (Noticia, ListaNoticias)
│       │
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── lnb/              (NBB, Ouro, LDB via HTML)
│       │   │   ├── client.py
│       │   │   ├── parsers.py
│       │   │   └── selectors.py
│       │   ├── ge/               (NBB via HTML)
│       │   │   ├── client.py
│       │   │   ├── parsers.py
│       │   │   └── selectors.py
│       │   ├── surto_olimpico/   (NBB, LDB, Ouro, NBA via API Supabase)
│       │   │   └── client.py
│       │   └── google_news/      (usado só em /api/noticias e /api/nba)
│       │       ├── client.py
│       │       └── parsers.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   └── noticias.py       (funções por liga + helpers de dedup)
│       │
│       └── api/
│           ├── __init__.py
│           ├── schemas.py
│           └── routes/
│               ├── __init__.py   (registra todos os routers)
│               ├── noticias.py   (GET /api/noticias — Google News "basquete")
│               ├── nbb.py        (GET /api/nbb/noticias — LNB + GE + Surto)
│               ├── ouro.py       (GET /api/ouro/noticias — LNB)
│               ├── ldb.py        (GET /api/ldb/noticias — LNB)
│               └── nba.py        (GET /api/nba/noticias — Google News "NBA basquete")
│
└── frontend/
    ├── index.html                (site único)
    └── src/
        └── assets/
            ├── hero-bg.png
            ├── logo.png
            └── times/            (.gitkeep)
```

---

## 6. Estado atual (o que funciona)

### Backend — rotas
- ✅ `/api/noticias?limite=N` — Google News RSS `basquete` (agregado geral)
- ✅ `/api/nbb/noticias?limite=N` — **LNB + GE + Surto Olímpico** (dedup LNB>GE>Surto)
- ✅ `/api/ouro/noticias?limite=N` — só LNB
- ✅ `/api/ldb/noticias?limite=N` — só LNB
- ✅ `/api/nba/noticias?limite=N` — só Google News `NBA basquete`
- ✅ `/` — health-check
- ✅ CORS liberado (`allow_origins=["*"]`) — restringir em produção

### Backend — infra
- ✅ `BaseAPI` com session, retry, throttle, cache TTL, **headers customizados**
- ✅ `Settings` (pydantic-settings) lê `.env` corretamente
- ✅ Deduplicação por título normalizado (60 chars)
- ✅ Prioridade de dedup: LNB > GE > Surto
- ✅ Cache em memória (TTLCache, reseta com servidor)
- ✅ **3 clientes funcionando:** LNB (HTML), GE (HTML), Surto (API JSON)

### Frontend
- ✅ Hero com `hero-bg.png` + `logo.png` + 2 caixas laterais
- ✅ Navbar com dropdowns por liga (times hardcoded)
- ✅ **Últimas Notícias** — Google News (`/api/noticias`)
- ✅ **Radar NBB** — 3 fontes com imagem garantida
- ✅ **Radar Liga Ouro** — LNB
- ✅ **Radar LDB** — LNB
- ✅ **Radar NBA** — Google News (placeholder colorido nas imagens)
- ✅ Motion One nas animações (com fallback)
- ✅ `Promise.all` no `renderTudo` — 5 seções carregam em paralelo

### UX
- Hero esquerdo: "Uma dose diária de basquete"
- Hero direito: "O jogo não para"
- Título da aba: "Basqueteleiro - Uma dose diária de basquete"
- Favicon: `logo.png`

---

## 7. Como rodar

### Pré-requisitos (Windows)
- Python 3.12.x no PATH
- Git Bash (não cmd/PowerShell)
- VSCode com Live Server
- `pip install requests beautifulsoup4 lxml fastapi "uvicorn[standard]" pydantic pydantic-settings tzdata`

### Rodar backend
```bash
cd C:/Users/Rodrigo/Downloads/basqueteleiro/basqueteleiro
source .venv/Scripts/activate
cd backend
python -m uvicorn app.main:app --port 8000
```
Testar: http://127.0.0.1:8000/docs

### Rodar frontend
Live Server (botão direito no `index.html`) OU:
```bash
cd frontend && python -m http.server 5500
```
Abrir: http://127.0.0.1:5500/index.html

### Importante
- **Reiniciar o uvicorn** sempre que criar arquivo NOVO.
- **Fechar e reabrir o terminal** se criar dependência nova.
- O `.env` **não vai pro Git** — contém a chave do Supabase do Surto.

---

## 8. Convenções

- **Idioma**: comentários, docstrings e UI em **português**.
- **Modelos**: pydantic v2. `Noticia` é o formato único entre fontes.
- **Fusos**: datas sempre UTC aware.
- **Erros de fonte**: levantam `SourceError`/`SourceUnavailableError`/`ParseError`.
- **Parsers**: funções puras (recebem HTML/JSON, devolvem modelos). Zero I/O.
- **Clients**: herdam de `BaseAPI`. `get_text` (HTML), `get_json` (API REST).
- **Adicionar fonte nova**: criar `sources/<nome>/` com client + parsers + selectors,
  registrar no `services`, expor rota em `api/routes/`.
- **Frontend**: HTML + JS vanilla. `el()` para criar DOM seguro.

---

## 9. Pendências conhecidas

### Altas
- *(nenhuma — os 4 radares estão funcionando com dados reais)*

### Médias
- [ ] **Liga Ouro e LDB com mais fontes** — hoje só LNB. GE e Surto também cobrem? Investigar.
- [ ] **Radar NBA com imagem** — hoje usa Google News (sem imagem). Alternativa: usar Surto Olímpico pra NBA, ou fonte dedicada (NBA.com/brasil).
- [ ] **Deploy** — subir backend (Render/Railway) + frontend (Vercel/Netlify).
      Ajustes necessários: `API_BASE` no `index.html`, CORS restrito, `Dockerfile`/`Procfile`.

### Baixas
- [ ] **Cache persistente** — hoje em memória (reseta com servidor).
- [ ] **Deduplicação mais esperta** — hoje compara 60 chars do título normalizado.
- [ ] **Páginas internas** — clicar numa notícia abre direto na fonte (poderia ter página própria).
- [ ] **Busca** — input de busca por time/jogador.

---

## 10. Histórico de decisões

- **Venv na raiz**: `basqueteleiro/.venv/`.
- **Python 3.12** (não 3.15): wheels prontas pra todas as libs no Windows.
- **Motion One em vez de GSAP**: leve (~5 kB), tem fallback se CDN falhar.
- **HTML+JS vanilla**: sem bundler por enquanto.
- **Google News RSS na primeira fase**: rápido pra começar, mas **sem imagem**.
- **Migração pra fontes diretas** (LNB + GE + Surto): resolve imagem, cota e latência.
  O Google News ficou **só no agregado geral** (`/api/noticias`) e na NBA.
- **Microlink foi tentado e descartado** — lento (~3s/req), cota 50/dia, dependência externa.
- **Surto Olímpico via API Supabase** — descoberto via DevTools (Network). Chave `anon`
  pública, aceita no `.env`. Sem scraping de HTML (o site é JS).
- **Dedup: LNB > GE > Surto** — LNB tem conteúdo oficial; GE tem imagem boa;
  Surto é cobertura de nicho. Prioridade reflete autoridade/qualidade.
- **Parser da LNB reaproveitado** entre NBB, Liga Ouro e LDB (mesmo template HTML).
- **`BaseAPI` agora aceita `headers=`** — pra suportar API do Supabase com `apikey`.
- **Config via `pydantic-settings`** — `.env` na raiz, lido por `get_settings()`.
  Evita `os.getenv` que não lê `.env` automaticamente.

---

## 11. Comandos úteis

```bash
# Ativar venv
source .venv/Scripts/activate

# Rodar backend
cd backend && python -m uvicorn app.main:app --port 8000

# Testar endpoints
curl "http://127.0.0.1:8000/api/noticias?limite=5"
curl "http://127.0.0.1:8000/api/nbb/noticias?limite=5"
curl "http://127.0.0.1:8000/api/ouro/noticias?limite=5"
curl "http://127.0.0.1:8000/api/ldb/noticias?limite=5"
curl "http://127.0.0.1:8000/api/nba/noticias?limite=5"

# Medir tempo
curl -w "\nTempo: %{time_total}s\n" "http://127.0.0.1:8000/api/nbb/noticias?limite=5"

# Limpar cache Python (quando algo estranho acontecer)
find backend/app -name "__pycache__" -type d -exec rm -rf {} +
```

---

## 12. Instruções para a IA (quem lê este snapshot)

- Você está continuando um projeto **em andamento**.
- **Todos os radares estão com dados reais.** Não sugira voltar mocks.
- **Google News foi descontinuado** como fonte principal. Ainda é usado em
  `/api/noticias` (agregado) e `/api/nba/noticias`. Não reintroduza no Radar NBB.
- **Microlink foi tentado e descartado** — não sugira de novo.
- **`googlenewsdecoder` foi tentado e falhou** — não sugira de novo.
- **Não sugira refazer do zero** o que já funciona (parsers, dedup, frontend).
- **Pergunte antes de mudanças grandes** (refatorações, trocas de libs).
- **Sempre entregue arquivos completos** quando pedir pra "corrigir".
- **Português** nos comentários e docstrings.
- **Reinicie o uvicorn** sempre que criar arquivo novo.
- **Não invente URLs/endpoints** — confirme com o usuário.