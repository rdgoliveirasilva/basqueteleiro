# Fontes de dados

| Liga | Fonte | Tipo | Cobre | Status de validação |
|---|---|---|---|---|
| NBA | `cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json` | JSON estático | jogos de hoje, placar ao vivo | parser testado com fixture; **validar com resposta real** |
| NBA | `cdn.nba.com/static/json/staticData/scheduleLeagueV2.json` | JSON estático | calendário e resultados da temporada | idem |
| NBA | `cdn.nba.com/static/json/liveData/boxscore/boxscore_{id}.json` | JSON estático | box score por jogador | idem |
| NBA | `stats.nba.com/stats/leaguestandingsv3` | API não-oficial | classificação | idem; costuma exigir headers de navegador e **bloquear IPs de datacenter** |
| NBB | `lnb.com.br/nbb/…` | HTML (scraping) | jogos, classificação | ⚠️ **seletores e caminhos são suposições** (fixture sintética) |
| LDB | `lnb.com.br/ldb/…` | HTML (scraping) | jogos, classificação | ⚠️ idem |

Nenhuma delas é uma API oficial com contrato/SLA. Podem mudar ou sumir sem aviso.

## Calibrando NBB/LDB (o primeiro trabalho de verdade)

1. Abra a página real de jogos da LNB no navegador → **DevTools → Network → Fetch/XHR**.
   Se os jogos chegam por um endpoint JSON, prefira consumir o JSON (mais estável que HTML):
   crie um `parse_games_json` em `lnb/parsers.py` e troque `get_text` por `get_json` no client.
2. Se for HTML puro, inspecione o card de jogo e ajuste `lnb/selectors.py`.
3. Confirme os caminhos em `lnb/client.py` (`games_path`, `standings_path`).
4. Salve o HTML real em `tests/fixtures/` (substituindo/ao lado do sintético) e ajuste os testes.
5. `python scripts/check_sources.py --standings` para ver se está tudo vivo.

## Boas maneiras (e proteção do seu projeto)

- Leia os **termos de uso** e o `robots.txt` de cada fonte; alguns proíbem raspagem/redistribuição,
  principalmente para uso comercial.
- Mantenha os TTLs de cache e o rate limit conservadores (`.env`): `LNB_RATE=0.5` = 1 req a cada 2 s.
- Identifique-se no `USER_AGENT` com um contato.
- Não exponha a API publicamente sem cache/limite próprio: ela repassa carga para as fontes.
