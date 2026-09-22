# FECHAMENTOS RIBAS & THIAGÃO — geradores

Scripts persistidos aqui porque o sandbox reseta entre sessões. Não recriar do zero: usar estes.

## Setup (1 comando)
```bash
pip install openpyxl pandas
export PYTHONPATH=$(pwd)   # dentro de fechamento-ribas/
```

## Trilhas

| Trilha | Script | Ciclo | Formato |
|---|---|---|---|
| Jean Vlogs (38579) | `jean.py` | all-time desde 13/05 | 10 col, SÓ métricas (sem comissão) |
| VT Unificado (38438+40271+38541) | `vt.py` | mensal | abas individuais 13 col (com comissão) + aba VT UNIFICADO 10 col |
| Semanal BINGO/REALS pendente | `pendente.py` | SEG→DOM, acumulado | `B <sem>` / `R <sem>` + `ÍNDICE` |

## Comandos

```bash
# Jean — exige export AFFILIATE (Affiliate=38579). Export Campaign é recusado.
python3 jean.py --input export_affiliate_38579.csv --out .

# VT — 3 exports diários, um por BTAG; filtra pelo mês
python3 vt.py --e38438 a.csv --e40271 b.csv --e38541 c.csv --mes 2026-09

# Semanal pendente — exports agregados por conta; --arquivo para acumular no xlsx vigente
python3 pendente.py --bingo exp_bingo.csv --reals exp_reals.csv \
  --inicio 2026-08-17 --fim 2026-08-23 \
  --arquivo FECHAMENTO_FINAL_PENDENTE_DESDE_290626_ATE_160826.xlsx
```

Sempre depois — validar as fórmulas:
```bash
python3 /mnt/skills/public/xlsx/scripts/recalc.py <arquivo.xlsx> 420   # esperar total_errors: 0
```
**Se o recalc estourar timeout mesmo com 420s**, o LibreOffice do container está quebrado
(dá para confirmar: um xlsx de 3 células também estoura). Nesse caso use o validador local,
que avalia as fórmulas em Python e reporta o mesmo `total_errors`:
```bash
pip install formulas
python3 validar.py <arquivo.xlsx>                      # total_errors: 0
python3 validar.py <arquivo.xlsx> --aba "VT UNIFICADO" --mostrar C21 F21
```

## Auditar uma pasta de fechamentos (`auditar_datas.py`)

Confere a **quantidade de material** por trilha e se o `DDMMAA` do **nome** bate com o
último dia REAL de dado dentro de cada planilha (lê a coluna `DIA` no Jean/VT e a coluna
`PERÍODO` nas abas semanais do pendente — nunca o título, que pode estar errado).
Também aponta duplicatas e arquivos sem `_ATE_` no nome.

```bash
pip install openpyxl
python3 auditar_datas.py "/caminho/da/pasta"             # só relata (dry-run)
python3 auditar_datas.py "/caminho/da/pasta" --aplicar   # renomeia os errados
```

## Regras de comissão (fixas)

**BINGO** — CPA R$40/FTD + 35% RevShare.
`COMISSÃO DIA = SE FTD=0 OU (CPA+RevShare)<0 → 0; senão CPA+RevShare`
BEKAS = RAW (sem zeragem). FINAL = com zeragem.

**REALS** — CPA R$30/FTD + RevShare.
35% só para `25945 Danielribas`, `10020 Danielribas11`, `21679 Danielribas2002`. 25% para as demais.
FINAL **mantém negativos**.

**Exclusões/casos fixos**
- `41738 wesley01`: excluído sempre, toda plataforma.
- `41735 TheuDados`: FINAL BINGO sim (9 linhas), FORA do BEKAS (8 linhas).
- `21757 Braidscinthia`: ausente do export REALS → entra 0/0 (o script já trata).
- `10020 Danielribas11`: alta volatilidade (+R$61k a −R$14k) — conferir sempre.

Roster completo em `roster.py` (9 BINGO + 53 REALS, assertados no import).

## Armadilhas já tratadas nos scripts
1. **Data do arquivo ≠ último dia com dado.** `checar_ultimo_dia()` compara com `Day.max()` e avisa.
2. **Export Campaign ≠ Affiliate.** `jean.py` recusa export Campaign (`UX-38579`).
3. **Vírgula decimal BR.** `parse_br()` trata `"1.234,56"`, `"R$ ..."`, `"(123,45)"`.
4. **Nome de arquivo com caixa variável.** Caminho é argumento — sem path montado por convenção.
5. **Lapso de data no pedido.** `--ate` é validado contra o export e corrigido com aviso.

## Visual (Play) — aplicado por `common.aplicar_estilo`
Fundo `#000000` · header/TOTAL dourado `#F4C430` com texto preto · fonte "Play" ·
NGR verde `#4ADE80` (≥0) / vermelho `#F87171` (<0) por formatação condicional ·
linha TOTAL rotulada `2026` · moeda `"R$ "#,##0.00`.

## Estado (18/09/2026)
- Jean: fechado até 17/09 (128 dias). **Pendente 00BABY:** vira ciclo mensal ou segue all-time?
- VT: agosto fechado 31/08 = R$ 11.673,82; setembro aberto, fechado até 17/09.
- Semanal pendente: última fechada 10/08→16/08 (7ª). Acumulado até 16/08 = R$ 280.703,17.
  **Próxima:** 17/08→23/08 — falta 00BABY enviar os exports agregados BINGO/REALS.
- Pagamento R$ 280.703,17 aguarda aval de Arthur Affonso.
- Análise Multiano (198 BINGO + 53 REALS): faltam os 6 exports de origem + 2 respostas.

## Checklist antes de entregar
- [ ] `Day.max()` confere com o dia pedido (senão fecha no real e avisa — o script imprime).
- [ ] Jean veio de export Affiliate.
- [ ] `recalc.py` → `total_errors: 0`.
- [ ] Totais batem: Jean (REG/FTD/DEP/NGR), VT (comissão = soma das 3 abas), pendente (ÍNDICE = soma das semanas).
- [ ] Formato por trilha: Jean 10 col sem comissão · VT 13/10 · pendente ROUND mantido.
