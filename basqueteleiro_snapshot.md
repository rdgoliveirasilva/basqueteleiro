# BASQUETELEIRO — Snapshot do Projeto

> Arquivo de contexto para retomar o desenvolvimento em qualquer chat novo.
> Cole este arquivo inteiro e diga o que quer fazer — a IA já vai entender tudo.
> **Última atualização:** 2026-10-12

---

## 1. O que é

**Basqueteleiro** — agregador de notícias de basquete brasileiro e americano.
Wrapper/scraper de múltiplas fontes que normaliza num formato único e expõe
via API própria + site.

Slogan: **"Uma dose diária de basquete"**

Cobertura: **NBB, Liga Ouro, LDB, NBA** — todos com dados reais.

---

## 2. Stack

### Backend
- **Python 3.12.7** (venv em `.venv/`)
- **FastAPI** + **uvicorn** — servidor HTTP
- **requests** + **beautifulsoup4** + **lxml** — scraping
- **pydantic** — modelos de dados
- **tzdata** — fusos horários no Windows (obrigatório)

### Frontend
- **HTML + CSS + JavaScript puro** (sem framework, sem bundler)
- **Bootstrap 5.3** (CDN) — grid, utilidades
- **Motion One** (`@motionone/dom`, CDN) — animações
- **Live Server do VSCode** — serve o `index.html` local (porta 5500)

### Fontes de dados
- **LNB** (`lnb.com.br/noticias/categoria/{nbb,liga-ouro,ldb}`) — HTML server-side
- **Google News RSS** (`news.google.com/rss/search?q=...&hl=pt-BR&gl=BR&ceid=BR:pt-419`) — XML público

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
Exceções: badges, links em hover, "vencedor" (amarelo), botões com fundo claro
(texto verde-escuro).

Assets esperados em `frontend/src/assets/`:
- `hero-bg.png` — imagem de fundo do hero (jogadores)
- `logo.png` — logo do Basqueteleiro (usado no hero e favicon)

---

## 4. Arquitetura

```
fontes externas → sources/ → services/ → api/ → frontend/
 (LNB, Google)   scrapers    regras     FastAPI   HTML
```

### Camadas do backend (dependências só apontam para baixo)

```
api/        rotas HTTP, schemas, tradução de erros → status
services/   regras de negócio (fusão, dedup, ordenação)
sources/    clientes HTTP + parsers puros
core/       infra (BaseAPI, cache, exceptions)
models/     formato único (pydantic)
```

### Fluxo de uma requisição (ex: Radar NBB)

```
GET /api/nbb/noticias?limite=5
  → routes/nbb.py::noticias()
  → services/noticias.py::ultimas_noticias()
      → LNBClient.noticias(League.NBB)         → lnb.com.br/noticias/categoria/nbb
      → GoogleNewsClient.buscar("nbb")         → news.google.com/rss/search?q=nbb
      → _deduplicar([lnb, google])             (LNB vence duplicatas)
      → _ordenar_por_data()                    (mais recentes primeiro)
      → [:limite]
  → JSON: { liga, noticias: [...], erro }
```

---

## 5. Árvore de arquivos atual

```
basqueteleiro/
├── .env.example
├── .gitignore
├── README.md
├── basqueteleiro_snapshot.md    ← ESTE ARQUIVO
│
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py              (FastAPI + CORS)
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── base.py          (BaseAPI: session, retry, throttle)
│       │   └── exceptions.py    (hierarquia de erros)
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── enums.py         (League: NBB, LDB, OURO, NBA, GERAL)
│       │   └── noticia.py       (Noticia, ListaNoticias)
│       │
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── lnb/
│       │   │   ├── __init__.py
│       │   │   ├── client.py    (LNBClient — 3 URLs: nbb, liga-ouro, ldb)
│       │   │   ├── parsers.py   (parse_noticias)
│       │   │   └── selectors.py (LNBSelectors)
│       │   └── google_news/
│       │       ├── __init__.py
│       │       ├── client.py    (GoogleNewsClient — busca livre por query)
│       │       └── parsers.py   (parse_feed + extrair_og_image)
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   └── noticias.py      (5 funções: ultimas_noticias,
│       │                         ultimas_noticias_google,
│       │                         ultimas_noticias_lnb,
│       │                         ultimas_noticias_ldb + helpers de dedup)
│       │
│       └── api/
│           ├── __init__.py
│           ├── schemas.py
│           └── routes/
│               ├── __init__.py  (registra noticias, nbb, ouro, ldb, nba)
│               ├── noticias.py  (GET /api/noticias — Google News "basquete")
│               ├── nbb.py       (GET /api/nbb/noticias — LNB + Google "nbb")
│               ├── ouro.py      (GET /api/ouro/noticias — só LNB liga-ouro)
│               ├── ldb.py       (GET /api/ldb/noticias — LNB + Google "LDB basquete")
│               └── nba.py       (GET /api/nba/noticias — só Google "NBA basquete")
│
└── frontend/
    ├── index.html                (site único)
    └── src/
        └── assets/
            ├── hero-bg.png
            └── logo.png
```

**Removidos** (limpeza feita):
- `scraper_lnb.py` e `scraper_google_news.py` — antigos scripts standalone
- `backend/test_*.py` — arquivos temporários de teste
- `RADAR_MOCK` e funções associadas no `index.html` — agora tudo real

---

## 6. Estado atual (o que funciona)

### Backend — rotas (todas com dados reais)
- ✅ `/api/noticias?limite=N` — Google News RSS query `basquete`
- ✅ `/api/nbb/noticias?limite=N` — LNB `categoria/nbb` + Google News `nbb`
- ✅ `/api/ouro/noticias?limite=N` — só LNB `categoria/liga-ouro`
- ✅ `/api/ldb/noticias?limite=N` — LNB `categoria/ldb` + Google News `LDB basquete`
- ✅ `/api/nba/noticias?limite=N` — só Google News `NBA basquete`
- ✅ `/` — rota raiz de health-check
- ✅ CORS liberado (`allow_origins=["*"]`) — restringir em produção

### Backend — infra
- ✅ Deduplicação por título normalizado (60 chars, LNB vence)
- ✅ Ordenação por data desc
- ✅ Cache em memória por URL (TTL) — reseta com o servidor
- ✅ Retry + rate limit no `BaseAPI`
- ✅ Parser da LNB reaproveitado entre NBB, Liga Ouro e LDB
- ✅ Cliente do Google News com busca livre por query

### Frontend
- ✅ Hero com `hero-bg.png` + logo `logo.png` animada + 2 caixas laterais
- ✅ Navbar com dropdowns por liga (times hardcoded)
- ✅ **Últimas Notícias** — Google News (`/api/noticias`)
- ✅ **Radar NBB** — LNB + Google News (`/api/nbb/noticias`)
- ✅ **Radar Liga Ouro** — LNB (`/api/ouro/noticias`)
- ✅ **Radar LDB** — LNB + Google News (`/api/ldb/noticias`)
- ✅ **Radar NBA** — Google News (`/api/nba/noticias`)
- ✅ Motion One nas animações (com fallback se CDN falhar)
- ✅ Placeholder colorido com sigla quando notícia não tem imagem

### UX
- Hero esquerdo: "Uma dose diária de basquete" (Bem-vindo)
- Hero direito: "O jogo não para" (Seu basquete sempre em dia)
- Título da aba: "Basqueteleiro - Uma dose diária de basquete"
- Favicon: `logo.png`

---

## 7. Como rodar

### Pré-requisitos (Windows)
- Python 3.12.x instalado e no PATH
- Git Bash (não cmd/PowerShell)
- VSCode com Live Server

### Primeira vez
```bash
cd C:/Users/Rodrigo/Downloads/basqueteleiro/basqueteleiro
python -m venv .venv
source .venv/Scripts/activate
pip install requests beautifulsoup4 lxml
pip install fastapi "uvicorn[standard]" pydantic pydantic-settings tzdata
```

### Rodar backend (terminal 1)
```bash
cd C:/Users/Rodrigo/Downloads/basqueteleiro/basqueteleiro
source .venv/Scripts/activate
cd backend
python -m uvicorn app.main:app --port 8000
```
Testar em: http://127.0.0.1:8000/docs

### Rodar frontend (terminal 2 ou Live Server do VSCode)
Opção A — Live Server: botão direito no `frontend/index.html` → "Open with Live Server".
Opção B — Python:
```bash
cd C:/Users/Rodrigo/Downloads/basqueteleiro/basqueteleiro/frontend
python -m http.server 5500
```
Abrir em: http://127.0.0.1:5500/index.html

### Importante
- **Reiniciar o uvicorn sempre que criar arquivo NOVO** (ele só detecta mudanças em arquivos já carregados).
- Se der erro estranho, matar o `python.exe` no Gerenciador de Tarefas e subir de novo.

---

## 8. Convenções

- **Idioma**: comentários, docstrings, docs e UI em **português**.
- **Modelos**: pydantic v2. `Noticia` é o formato único entre fontes.
- **Fusos**: "dia do jogo" no fuso da liga; datas de saída sempre UTC.
- **Erros de fonte**: levantam `SourceError`/`SourceUnavailableError`/`ParseError`
  do `core/exceptions.py`. Só `api/errors.py` traduz para HTTP.
- **Parsers**: funções puras (recebem HTML/XML, devolvem modelos). Zero I/O.
- **Clients**: herdam de `BaseAPI`, fazem I/O, respeitam rate limit.
- **Adicionar liga nova**: criar `sources/<liga>/` com client+parsers+selectors,
  registrar no `services`, expor rota em `api/routes/`, adicionar no
  `routes/__init__.py` e no `URLS_NOTICIAS` do `LNBClient` (se for da LNB).
- **Frontend**: HTML + JS vanilla. Sem `innerHTML` com dados de API (usa `el()`).

---

## 9. Pendências conhecidas

### Altas
- *(nenhuma — cobertura de todas as 4 ligas está funcionando)*

### Médias
- [ ] **Imagens do Google News** — o RSS não traz imagem e o Google bloqueia o
      redirect via `requests`. Tentativa com `googlenewsdecoder` falhou.
      Hoje: notícias do Google ficam com placeholder colorido (sigla).
- [ ] **Dedup mais esperto** — hoje compara só os 60 primeiros chars do título
      normalizado. Pode melhorar com URL/slug.
- [ ] **Cobertura da NBA** — hoje é só Google News `NBA basquete`. Pode
      melhorar com scraper dedicado (NBA.com/brasil, ESPN Brasil) para ter
      boxscores, tabela de classificação e estatísticas.

### Baixas
- [ ] **Cache persistente** — hoje em memória (reseta com o servidor).
      Migrar pra SQLite ou arquivo JSON.
- [ ] **Enriquecer LNB com RSS oficial** — `lnb.com.br/feed/` (WordPress)
      traz imagem em `<media:content>`, mais estável que scraping HTML.
- [ ] **Deploy** — quando o projeto estiver redondo, subir backend
      (Render/Railway) + frontend (Vercel/Netlify). Precisa ajustar:
      `API_BASE` no `index.html`, CORS restrito, `Dockerfile`/`Procfile`.

---

## 10. Histórico de decisões

- **Venv na raiz**: `basqueteleiro/.venv/` — ativação via `source .venv/Scripts/activate`.
- **Python 3.12** (não 3.15): o 3.15 não tem wheels prontas pra várias libs
  no Windows (erro de compilação do `pyyaml`). 3.12 é o sweet spot.
- **Live Server em vez de bundler**: sem Vite/Webpack por enquanto —
  HTML+JS vanilla serve até o projeto crescer.
- **Motion One em vez de GSAP**: GSAP quebrou com `--reload` do uvicorn
  (opacity 0 travado) e é pesado. Motion One é leve (~5 kB) e tem fallback.
- **Google News RSS em vez de scraping da SERP**: scraping do Google viola
  ToS e dá CAPTCHA. RSS é público, permitido e estável.
- **Dedup: LNB vence Google**: LNB tem imagem + resumo + URL direta.
  Google só tem título + link.
- **Placeholder colorido com sigla**: quando não tem imagem, o card mostra
  fundo colorido por liga + sigla (NBB, LNB, ge, etc.). Visualmente aceitável.
- **Parser da LNB reaproveitado**: NBB, Liga Ouro e LDB usam o mesmo
  `parse_noticias` porque o HTML é idêntico (mesma classe `.noticias_jogadores`).
- **Dedup entre seções: aceita duplicação**: uma notícia que aparece no
  Radar NBB pode aparecer também em Últimas Notícias. Decisão consciente —
  cada seção tem escopo declarado.
- **Cobertura da NBA via Google News**: como a LNB não cobre NBA e um
  scraper dedicado é trabalhoso, usamos só Google News `NBA basquete`.
  Suficiente para radar de notícias (não para dados estruturados).

---

## 11. Comandos úteis

```bash
# Ativar venv
source .venv/Scripts/activate

# Rodar backend
cd backend && python -m uvicorn app.main:app --port 8000

# Testar todos os endpoints
curl "http://127.0.0.1:8000/api/noticias?limite=5"
curl "http://127.0.0.1:8000/api/nbb/noticias?limite=5"
curl "http://127.0.0.1:8000/api/ouro/noticias?limite=5"
curl "http://127.0.0.1:8000/api/ldb/noticias?limite=5"
curl "http://127.0.0.1:8000/api/nba/noticias?limite=5"

# Medir tempo de resposta
curl -w "\nTempo: %{time_total}s\n" "http://127.0.0.1:8000/api/nbb/noticias?limite=5"
```

---

## 12. Instruções para a IA (quem lê este snapshot)

- Você está continuando um projeto que já está em andamento.
- **Todos os radares (NBB, Liga Ouro, LDB, NBA) e a seção Últimas Notícias
  estão com dados reais.** Não sugira voltar mocks.
- **Não sugira refazer do zero** o que já funciona (LNB scraper, backend FastAPI,
  hero, navbar, radares, dedup).
- **Pergunte antes de mudanças grandes** — refatorações de estrutura, troca de
  libs, mudanças de contrato de API.
- **Sempre entregue arquivos completos** quando pedir pra "corrigir" —
  edições parciais confundem mais do que ajudam neste estágio.
- **Português** nos comentários e docstrings.
- **Prefira soluções simples** — o projeto está em fase de protótipo.
- **Não invente URLs/endpoints** — se precisa de um novo, confirme com o usuário.
- **Reinicie o uvicorn** sempre que criar arquivo novo — o FastAPI não
  recarrega automaticamente (só se estiver com `--reload`).
```

---

## O que mudou em relação à versão anterior

| Seção | Mudança |
|---|---|
| **1** | Cobertura: agora **NBB + Liga Ouro + LDB + NBA** todos reais |
| **5** | Adicionado `nba.py` na árvore de rotas. Removida menção a `scraper_*.py` e `test_*.py` (limpeza feita). Marcado que `RADAR_MOCK` foi removido. |
| **6** | Rota `/api/nba/noticias` listada. Radar NBA agora é real. |
| **9** | Pendência "Radar NBA" **removida**. Seção Altas agora está vazia. Adicionada pendência "Cobertura da NBA" em Médias (pra quando quiser scraper dedicado). Adicionada pendência "Deploy" em Baixas. |
| **10** | Adicionada decisão: "Cobertura da NBA via Google News". |
| **11** | Adicionado `curl` do endpoint NBA. |
| **12** | Adicionada instrução: "todos os radares estão com dados reais". |
