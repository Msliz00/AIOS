# 🤝 HandOff — Projeto **Garimpo** (painel de desapego)

> **Para:** o novo chat que vai cuidar da **parte pensante** (estratégia, produto, modelagem de dados, decisões).
> **De:** sessão de build (Claude Code). Este documento é a fonte de contexto — leia inteiro antes de agir.
> **Data do handoff:** 2026-10-13

---

## 0) Como usar este handoff
Cole este arquivo inteiro no novo chat e diga: *"Você é o responsável pela parte pensante do projeto Garimpo. Leia o handoff e assuma."*
O arquivo vive em `docs/HANDOFF-garimpo.md` (repositório `Msliz00/sem-pino`), então o novo chat pode abri-lo direto.

---

## 1) O que é o projeto (em uma frase)
Um **painel operacional single-file (HTML)** para gerir **grupos de desapego** (venda de usados / brechó em comunidades de Telegram/Instagram/WhatsApp). O dono (**00BABY**, matheussliznegocios29@gmail.com) acompanha, por grupo e consolidado, o resultado financeiro, o funil e a produção de criativos.

**Importante:** o projeto **acabou de migrar de mercado**. Ele nasceu como painel de uma operação de **iGaming/apostas (REALS Bingo)** e foi **100% rebrandeado** para o nicho de **desapego** na marca **Garimpo**. Nada do mercado antigo deve reaparecer.

---

## 2) Estado atual (o que já existe e funciona)
Arquivo canônico: **`docs/painel-central-experts.html`** (~1030 linhas, SPA single-file) + dados em **`docs/painel-dados.js`** (`window.DADOS = {...}`).

- **Marca Garimpo**: logo de texto com gema dourada + "painel de desapego".
- **Paleta**: violeta `#7c3aed` (primária) + dourado `#f2b23a` (acento) sobre ameixa profunda `#0c0a12`. Verde `#34d399` / vermelho `#ef4444` só como **semântica de resultado** (lucro/prejuízo), não como marca.
- **Fontes**: Bricolage Grotesque (display) + Fraunces (acento serif itálico) + Inter (corpo) + JetBrains Mono (números). Carregadas via Google Fonts.
- **6 páginas navegáveis** (router JS por `.page`/`.active`):
  1. **Central** — hero de resultado, KPIs, gráficos (resultado diário, custo×receita), ranking por grupo, destaques, funil, donut de composição da receita.
  2. **Dashboard** — 14 KPIs completos vs período anterior + cartões de "acessos do grupo" (Planilha/Instagram/Telegram/Grupo/Live).
  3. **Telegram** — placeholder "em construção".
  4. **Upload** — formulário mock de envio de relatório (planilha/manual/drive).
  5. **Criativos** — produção de peças de divulgação por grupo na última semana (KPIs, barras, donut, planilhas).
  6. **Gestão** — lista de grupos e campanhas (mock de CRUD).
- **Filtro de datas**: presets (7/15/30/90/Tudo) + botão **Personalizado** (popover de/até).
- **Seletor de grupos**: botão único com dropdown.
- **Login**: aceita celular/usuário/e-mail com detecção automática, "salvar neste aparelho" (localStorage `garimpo_login`/`garimpo_email`), PasswordCredential API, botões placeholder (Google / esqueci a senha). **Ainda sem validação real** — é só tela.
- **Motion**: reveals por IntersectionObserver, count-up nos números, draw dos gráficos.
- Publicado via **GitHub Pages**: `https://msliz00.github.io/sem-pino/painel-central-experts.html`.

---

## 3) ⚠️ Dados são de EXEMPLO (placeholder)
Decisão explícita do dono: usar **dados fictícios realistas** por enquanto; os reais entram depois.
`docs/painel-dados.js` tem **5 grupos ativos + 1 em implantação**, 3 meses de histórico diário (JUL/AGO/SET 2026):

| key | Grupo | Categoria | Status |
|---|---|---|---|
| fashion | Garimpo Fashion | moda | ativo (líder) |
| baby | Baby & Kids Desapego | infantil | ativo |
| casa | Casa & Decoração | casa | ativo |
| tech | Tech Seminovos | tech | ativo |
| vintage | Vintage & Coleções | vintage | ativo |
| luxo | Luxo Desapego | luxo | **pendente** (em implantação) |

Os links em `acessos` (`https://drive.google.com/.../EXEMPLO-...`, `instagram.com/garimpo.<key>`, `t.me/garimpo_<key>`) são **fictícios**.

---

## 4) Modelo de dados (crucial para a parte pensante)
Para evitar reescrever a matemática, o rebrand **manteve a forma do JSON** e só **relabelou** os significados. Cada dia é `[dia, g, le, r, f, d, n]`:

| chave | significado (desapego) | papel antigo (iGaming) |
|---|---|---|
| `g`  | **Custo** (operação + divulgação) | Gasto |
| `le` | **Membros** (novos membros/dia) | Leads |
| `r`  | **Anúncios** (listings publicados) | Registros |
| `f`  | **Vendas** (itens vendidos) | FTD |
| `d`  | **GMV** (valor total vendido) | Depósitos |
| `n`  | **Receita** (comissão + taxas do operador) | NGR |

Derivadas em `met()` (JS): `resultado = n − g`, `roi = (n−g)/g`, `margem`, `custo/membro`, `custo/anúncio (cpa)`, `custo/venda`, `membro→anúncio`, `anúncio→venda`, `ticket = d/f`.
Fórmula de exemplo usada no gerador: `receita = GMV×0,15 + anúncios×1,6` e `custo` como base/dia. **Esses pressupostos são chutes plausíveis — revisar com o dono.**

Estrutura de cada grupo: `{key, nome, marcas:[categoria], cor, apelido?, pendente?, meses:{MES:{g,le,r,f,d,n,dias:[...]}}, campanhas:[], acessos:{planilha,instagram,telegram,grupo,live,criativos}, criativos:<int>}`.
Top-level: `{ano, meses:[...], mesAtual, mesAnterior, experts:[...], criativos:{label,periodo,porExpert,total}}`.
O gerador fica em `scratchpad/gen_desapego.py` (seed fixo 42) — reproduzível.

> Nota técnica: no código JS as variáveis ainda se chamam `EXPERTS`, `experts`, `buildExpertDD`, `dpills`, `pendente`, etc. São **nomes internos** herdados; a UI já diz "grupos". Não precisa renomear para funcionar, mas é dívida técnica a considerar.

---

## 5) Mapa de arquivos
- `docs/painel-central-experts.html` — **o painel** (canônico). Edite aqui.
- `docs/painel-dados.js` — dados (exemplo). `<script src>` carregado pelo painel.
- `docs/bingobet_junho_2026_scroll.html` — relatório Instagram antigo (iGaming). **Legado, não faz parte do Garimpo.**
- `docs/painel-preview-v8.html` — protótipo antigo. Legado.
- `docs/logo-reals-bingo.png` — logo do mercado antigo. **Não é mais referenciado** (agora o logo é texto+SVG). Pode ser removido.
- Branch de trabalho: **`claude/bingobet-instagram-report-june-sh9zlp`** (o nome é herança do início; todo o trabalho vai aqui). Pushes vão para essa branch.

---

## 6) Restrições e decisões já tomadas (respeitar)
- **Segurança:** NÃO guardar a senha/telefone real do dono no repositório público. O login real só com **autenticação server-side (Supabase Auth)** — ainda não implementado.
- **Mercado:** desapego (Garimpo). Rebrand do mercado antigo deve ficar invisível.
- **Dados:** exemplo por enquanto; trocar pelos reais quando o dono conectar as planilhas.
- **Entrega:** sempre validar (overflow 0 em 1440px e 375px, sem erro de console) e entregar o link do GitHub Pages quando o HTML mudar.
- **Idioma:** PT-BR. Tom direto.
- O painel é **single-file por opção** (fácil de hospedar no Pages). Qualquer migração para framework é decisão de produto, não suposição.

---

## 7) Perguntas abertas para a parte pensante decidir
Estas são as decisões "pensantes" que travam o próximo salto do projeto:

1. **Modelo de receita real.** Como o Garimpo ganha de fact? Comissão sobre venda? Taxa de anúncio em destaque? Mensalidade de membro? Revenda própria? Isso define `receita`, `custo` e `GMV` de verdade.
2. **Fonte de dados real.** De onde vêm os números por grupo? Planilha Google por grupo (como era no iGaming)? Export do Telegram/bot? Entrada manual? Define o parser e a página Upload.
3. **Quem são os grupos reais** e suas categorias/cores — substituir os 6 de exemplo.
4. **Métricas que importam de verdade** no desapego: faltam ideias como taxa de recompra, tempo médio até a venda, itens encalhados, ticket por categoria, membros ativos vs total, reputação/estorno. Priorizar.
5. **Autenticação & multiusuário.** Vai ter login por grupo/curador? Papéis (admin vs curador)? Isso puxa Supabase (Auth + tabelas).
6. **Telegram (página hoje placeholder):** o que medir — crescimento de membros, disparos, cliques, conversão membro→venda?
7. **Criativos:** hoje só conta quantidade/semana. Quer performance por peça (gasto, alcance, vendas atribuídas)?
8. **Nome/identidade final:** "Garimpo" e a paleta violeta+dourado foram escolha minha de build; confirmar com o dono ou ajustar (ele cogitou um visual mais "vintage/terroso").

---

## 8) Próximos passos sugeridos (ordem pensante → build)
1. Rodar com o dono o **modelo de negócio** (perguntas 1–4) e fechar o **dicionário de métricas** real.
2. Definir a **arquitetura de dados** (Supabase: tabelas `grupos`, `dias`, `criativos`, `campanhas`, `acessos`; RLS por usuário).
3. Especificar a **ingestão** (planilha/manual/bot) e validar com 1 grupo real piloto.
4. Só então trocar `painel-dados.js` por dados reais e ligar **Supabase Auth** no login.
5. Evoluir Telegram e Criativos conforme prioridade.

---

## 9) Ferramentas disponíveis nesta conta (para o novo chat)
- **Supabase MCP** (criar projeto, tabelas, migrations, Auth) — caminho natural para dados reais + login.
- **Google Drive MCP** (ler/baixar planilhas) — se a fonte for Google Sheets.
- **GitHub MCP** + `gh api` — repo `Msliz00/sem-pino`.
- **Gamma MCP** — se quiser gerar apresentação/deck do projeto.
- **n8n** — precisa ser autorizado (OAuth) antes de usar.
- Playwright (Chromium em `/opt/pw-browsers/...`) para validar o HTML.

---

### TL;DR para o novo chat
O build está pronto e bonito, **com dados de exemplo**. O que falta é **pensar o negócio**: modelo de receita, métricas que importam, fonte de dados real e autenticação. Comece pelas perguntas da seção 7 com o dono, feche o dicionário de métricas, depois desenhe Supabase. Não reintroduza o mercado antigo (iGaming). Branch: `claude/bingobet-instagram-report-june-sh9zlp`.
