# 🏀 Basqueteleiro

Wrapper/crawler de dados de basquete — **NBA, NBB e LDB** — que normaliza fontes diferentes
num único formato e expõe uma API própria (estilo SportRadar, em pequeno), mais um site
que consome essa API.

```
fontes externas ──► sources/ (clientes + parsers) ──► services/ ──► api/ (FastAPI) ──► frontend/
  cdn.nba.com          dados brutos → models/          regras         JSON único      Vite + JS
  stats.nba.com        (formato único)                 de negócio
  lnb.com.br
```

## Rodando

```bash
cp .env.example .env

# backend
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                                                # 48 testes, sem rede
uvicorn app.main:app --reload                         # http://127.0.0.1:8000/docs

# frontend (outro terminal)
cd frontend && npm install && npm run dev             # http://localhost:5173

# ou os dois juntos
./scripts/dev.sh
```

## Endpoints

| Rota | O que devolve |
|---|---|
| `GET /api/home?data=` | jogos de todas as ligas (falha de uma liga não derruba as outras) |
| `GET /api/{nba\|nbb\|ldb}/jogos?data=YYYY-MM-DD` | jogos do dia (padrão: hoje no fuso da liga) |
| `GET /api/{liga}/classificacao` | tabela de classificação |
| `GET /api/{liga}/times` | times (derivados da classificação) |
| `GET /api/{liga}/jogos/{id}/boxscore` | estatísticas por jogador (hoje só NBA; demais → 501) |
| `GET /api/health` | status |

Erros sempre no formato `{"error": {"type": "...", "message": "..."}}`.

## ⚠️ Antes de confiar nos dados

- **NBA**: endpoints não-oficiais (`cdn.nba.com/static/json` e `stats.nba.com`). Os parsers foram
  escritos a partir do formato conhecido desses JSONs e testados com fixtures; **valide contra a
  resposta real** com `python scripts/check_sources.py --standings`.
- **NBB/LDB**: os seletores em `backend/app/sources/lnb/selectors.py` e os caminhos em
  `lnb/client.py` são **suposições** calibradas numa fixture sintética. É a primeira coisa a ajustar.
- Confira os termos de uso e o `robots.txt` de cada fonte antes de publicar o projeto.

Detalhes em [`docs/`](docs): [arquitetura](docs/arquitetura.md) · [fontes](docs/fontes.md) · [uso](docs/uso.md).
