# Relatório semanal de criativos (modelo expert)

`gerar_relatorio_semanal(expert, data_inicio, data_fim) -> Path` — baixa as duas
planilhas do expert no Drive, soma o diário na janela, cruza com a aba semanal de
criativos e escreve um HTML pronto pra mandar. Experts configurados: **marques** e **suh**. Outro expert =
trocar dois IDs em `config.py` (e o regex de produção própria se o padrão de nome for outro).

## Uso

```bash
pip install -r relatorio_semanal/requirements.txt
export GOOGLE_SERVICE_ACCOUNT_FILE=/caminho/service-account.json   # leitura nas 2 planilhas

# semana explícita
python -m relatorio_semanal marques 2026-08-24 2026-08-31
# sem datas = semana anterior (segunda→domingo) — é o que o agendador chama
python -m relatorio_semanal marques
# sem Drive: lê <dir>/marques_operacao.xlsx e <dir>/marques_criativos.xlsx
python -m relatorio_semanal marques 2026-08-24 2026-08-31 --xlsx-dir relatorio_semanal/tests/fixtures
```

```python
from datetime import date
from relatorio_semanal import gerar_relatorio_semanal
html = gerar_relatorio_semanal("marques", date(2026, 8, 24), date(2026, 8, 31))
```

Saída: `relatorio_semanal/out/<expert>-relatorio-semanal-sNN.html`
(`-sem-midia` no nome quando o gate de gasto zero dispara). `RELATORIO_OUT_DIR` e
`RELATORIO_CACHE_DIR` mudam as pastas.

## Ordem de execução (gerar.py)

1. `drive.baixar_xlsx` × 2 (ou XLSX locais via `xlsx_dir`).
2. `operacao.ler_janela` na janela e na janela −7 dias (cruza abas de mês).
3. **Gate:** gasto == 0 → relatório "semana sem mídia", sem leitura de criativo.
4. `criativos.ler_semana` — match tolerante da aba (semana ISO, senão range no título).
5. `analise.analisar` — famílias × multiplicador, 4 respostas, top 10, cobertura, régua.
6. `textos.montar` → `render.renderizar` (Jinja2, `templates/relatorio.html.j2`).

## Arquivos

| Arquivo | Função |
|---|---|
| `config.py` | IDs por expert, regex de família/produção própria/CTA/oferta, régua, tema (tokens CSS) |
| `drive.py` | Download via service account + `decodificar_download_mcp` (gotcha do base64 aninhado) |
| `operacao.py` | Diário: header linha 2, dados linha 3, colunas por índice, soma entre meses |
| `criativos.py` | Aba semanal: header por nome (tolera layout antigo), match tolerante do título |
| `analise.py` | Agregação, ranking por FTD + C/FTD, cobertura, atribuição furada, deltas |
| `textos.py` | Frases do relatório (regra-based; declara "sem base" em vez de inventar) |
| `templates/relatorio.html.j2` | Hero · 01 cards · 02 quatro `.q` · 03 `.tbl` · 04 alerta · 05 próximo passo · footer |
| `tests/` | Critério de pronto (Marques) + regressão Suh S36, sobre snapshot XLSX das planilhas (09/09/2026) |

## Critério de pronto (tests/test_marques.py)

```bash
python -m pytest relatorio_semanal/tests -q
```

1. `("marques", 2026-08-24, 2026-08-31)` → Gasto R$ 21.206,62 · C/Lead R$ 45,70 · C/FTD R$ 1.247 · 17 FTD · top 10 = 10/10 próprios. Aba `S35 · 24–3008` achada por semana ISO; cobertura 81%; atribuição 5/17 FTD sinalizada.
2. `("marques", 2026-07-27, 2026-08-02)` → gate de gasto zero, cruza JULHO+AGOSTO, relatório de semana sem mídia, FTD/depósito rotulados como cohort antigo.
3. Config isolada: `get_expert("marques")` carrega os dois IDs; expert desconhecido dá erro claro.

## Decisões registradas

- **Template canônico não estava disponível** (`marques-relatorio-semanal-s35.html` não está no repo nem no Drive). O `relatorio.html.j2` foi construído a partir da estrutura e dos tokens descritos no handoff (laranja `#FF6B00`, Space Grotesk + Inter, animação de entrada). Todos os tokens são variáveis CSS alimentadas por `Tema` no config. Se o original aparecer, é só trocar o `<style>`.
- **Semana anterior = janela deslocada −7 dias**, como no handoff. Janela de 8 dias (24–31) gera comparação com 17–24 (sobrepõe o dia 24). Se preferir semanas fechadas, passar sempre segunda→domingo.
- **Régua:** C/Lead ≤45 verde / ≤55 âmbar; C/Reg ≤430 / ≤525 (proporcional); C/FTD ≤900 / ≤1500; NGR−Gasto ≥0.
- **Base mínima pra ler CTA:** ≥3 peças com marcador no nome e ≥25% do invest. Abaixo disso: "sem base", com recomendação de remarcar o nome.
- **Coerência da aba:** se o invest da aba > 1,5× o gasto do diário (ou diário zerado com aba cheia), a aba é ignorada e o aviso aparece no relatório. Evita ler aba de outro período por match de range.
- **Produção própria (Marques):** nomes começando com `AD_N`, `AD N -`, `CXL_ADnn`, `ADnn_`. O resto é marcado como "não identificado" (não como "externo").
- **Aba com vários candidatos** (`S27 (Jun)` / `S27 (Jul)` / `sem filtro`): prefere sem "sem filtro", maior sobreposição de datas, mês em que a semana termina.
- Diário: `#DIV/0!`, `None` e texto contam como 0; linha `TOTAL` e vazias são puladas por `isinstance(date)`.

## Agendador (n8n · Fluxo de Cortes)

Schedule Trigger `0 8 * * 1` (segunda 8h) → Execute Command
`python -m relatorio_semanal marques` → lê o caminho impresso no stdout → Read Binary File →
envia pro canal. A função é pura (retorna Path), o nó só repassa o arquivo.

## Pendências

| Pendência | Dono | Próximo passo |
|---|---|---|
| Service account com leitura nas 2 planilhas do Marques | 00BABY | Criar SA no GCP, compartilhar as planilhas com o e-mail da SA, apontar `GOOGLE_SERVICE_ACCOUNT_FILE` |
| Template original S35 (se existir) | 00BABY | Anexar o HTML; trocar o `<style>` do `.j2` mantendo as variáveis |
| Nó n8n de segunda 8h | 00BABY / n8n | Montar o fluxo acima depois da SA funcionar |
| Produção própria da Suh é hipótese (`JOGADA_50X_SUH_VARn` / `50X VARn`) | 00BABY | Confirmar quais nomes são lote nosso e ajustar `producao_propria` no bloco `suh` |
| Belodi, Iris, Lucas | 00BABY | Copiar o bloco `marques` em `EXPERTS`, trocar IDs e, se o nome dos criativos mudar, o regex de produção própria |
| Marcador de CTA/oferta no nome dos criativos | Operação Marques | Sem isso, respostas 02 e 03 continuam "sem base" — é o dado que falta, não a função |
