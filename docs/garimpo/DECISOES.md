# Garimpo — Registro de Decisões e Continuidade

> Fonte de verdade da parte pensante. Atualizar ao fim de cada sessão.
> Código do painel: `Msliz00/sem-pino` (`docs/painel-central-experts.html`). Contexto de origem: `HANDOFF-garimpo.md`.

## Fase atual: 1 — Modelo de negócio (em andamento)

| Fase | Entrega | Status |
|---|---|---|
| 1. Modelo de negócio | Receita, grupos, dicionário de métricas, nome | 🟡 em andamento |
| 2. Arquitetura de dados | Supabase: tabelas + RLS | ⏳ bloqueada pela 1 |
| 3. Ingestão | Planilha (piloto) → bot + link com split | ⏳ |
| 4. Painel com dados reais + login | Trocar `painel-dados.js`, Supabase Auth | ⏳ |
| 5. Telegram + Criativos | Evolução das páginas | ⏳ |

## Decisões tomadas

| # | Data | Decisão | Implicação |
|---|---|---|---|
| D1 | 2026-10-13 | **Operação começa do zero** (nenhum grupo rodando). | Desenho parte de hipótese; piloto valida. Dados de exemplo seguem até o piloto. |
| D2 | 2026-10-13 | **Receita = comissão sobre venda + VIP futuro.** | Grupos **gratuitos** agora. VIP só quando houver volume (gatilho a definir). |
| D3 | 2026-10-13 | **Comissão capturada via link de pagamento com split** (Asaas/Mercado Pago) no destino final. | Comprador paga no link do Garimpo; split repassa ao vendedor; webhook registra a venda. Comissão real e autônoma. |
| D4 | 2026-10-13 | **Fonte de dados: planilha agora, bot depois.** | No piloto a comissão é **autodeclarada** (risco de subdeclaração, aceito). Migração para bot + split na Fase 3. |
| D5 | 2026-10-13 | **Projeto terá outro nome.** | "Garimpo" é provisório. Dono vai enviar linha de sugestões. Paleta atual segue até o nome sair. |

## Diagnósticos registrados

- **Venda invisível:** em grupo Telegram/WhatsApp o operador não vê a transação → GMV/comissão só são confiáveis com split (D3).
- **Funil misturado:** o modelo herdado do iGaming junta oferta (vendedor/anúncio) e demanda (membro/venda). O dicionário de métricas deve separar os dois lados.
- **Fase de volume:** com grupos gratuitos e comissão autodeclarada, a métrica-norte do piloto é **volume** (membros, anúncios, vendas), não receita. O hero do painel deve refletir isso.

## Pendências

| Pendência | Dono | Próximo passo |
|---|---|---|
| Nome do projeto | 00BABY | Enviar linha de sugestões de nome |
| Gatilho do VIP (qual volume libera a cobrança) | Parte pensante → 00BABY valida | Propor após dicionário de métricas |
| % de comissão | Parte pensante → 00BABY valida | Propor faixa com benchmark |
| Grupos/categorias do piloto | 00BABY | Definir 1º grupo piloto |
| Dicionário de métricas (oferta × demanda) | Parte pensante | Rascunhar após nome |
| Adicionar repo `sem-pino` à sessão | Parte pensante | Na hora do build (Fase 2+) |
