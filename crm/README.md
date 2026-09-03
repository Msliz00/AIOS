# CRM v2 — lead_id (ponte telefone ↔ telegram)

Estado em 03/09/2026. Projeto Supabase **experts-painel** (`jqfpfkublwshpgtqkmeo`),
região sa-east-1.

## O problema que isto resolve

O CRM identifica o lead por **telefone**. O Telegram identifica por **telegram_id**.
O Telegram não expõe o telefone dos inscritos — canal broadcast não entrega lista de
membros a ninguém, nem admin, nem via MTProto (verificado em 25/08 nos 8 canais).
Sem chave comum, os dois mundos nunca se cruzam.

O `lead_id` é essa chave. Ela não é descoberta: ela **nasce de um opt-in**. O lead
recebe um link com token único, dá `/start` no bot, e o token amarra o `telegram_id`
que chegou ao telefone que originou o disparo.

## Números da base (03/09/2026)

| | |
|---|---|
| leads | 176.428 |
| com telefone | 154.605 |
| com telegram_id | 21.824 |
| **ponte completa** (os dois) | **1** |
| disparáveis por SMS | 41.394 |
| sem consentimento de marketing | 113.096 |

Os 113.096 entram cadastrados mas **não disparáveis** — é o consentimento que veio
do dado de origem, não um erro de import. Os 21.824 do Telegram entram como contato
conhecido, **nunca como opt-in**: esse consentimento só nasce do `/start`.

## Tabelas

### `leads_master`
O lead único. `lead_id UUID` é a chave que liga os dois mundos.

- `telefone` + `telefone_norm` (gerada, E.164 BR via `normalizar_telefone`)
- `telegram_id`, `telegram_username`
- `email`, `nome`, `origem`, `origem_detalhe`
- consentimento: `optin_sms`, `optin_ligacao`, `optin_telegram`, `data_optin`,
  `optin_fonte`, `optout_em`

Unicidade parcial em `telefone_norm`, `telegram_id` e `lower(email)` — um lead pode
existir só com telefone, só com telegram, ou com ambos.

### `optin_tokens`
O payload do deep-link. Token url-safe de 24 chars (limite do Telegram: 64).

Um token vivo por lead: gerar um novo mata o anterior, então só o último link
enviado vale. Guarda `canal`, `campanha`, `expira_em`, `usado_em`, `tentativas`.

### `telegram_grupos`
Os 8 canais broadcast, com contagem de inscritos e a grafia usada na base antiga
(`nome_base`), para o join da cobertura.

### `staging_crm` / `staging_telegram`
Área de pouso do import. Descartáveis.

## Funções (todas service_role only)

| função | o que faz |
|---|---|
| `normalizar_telefone(text)` | E.164 BR. 10-11 dígitos ganham `55`; corrige `55 + 0DDD` |
| `registrar_lead(telefone, nome, email, origem)` | upsert por telefone normalizado |
| `gerar_optin_token(lead_id, canal, campanha, dias)` | token novo, mata o anterior |
| `gerar_link_optin(telefone, ...)` | telefone → `{lead_id, token, link}` pronto |
| `gerar_links_lote(jsonb, ...)` | array de leads → uma linha por link |
| `resolver_optin(token, telegram_id, username)` | chamada pelo bot no `/start` |
| `promover_staging()` | staging → `leads_master`, idempotente |

### `resolver_optin` — os estados

| status | quando |
|---|---|
| `ok` | vínculo criado |
| `fundido` | lead só-Telegram absorvido pelo lead do telefone |
| `ja_vinculado` | mesmo usuário reclicou o próprio link |
| `token_usado` | outro telegram_id tentou um token já consumido |
| `token_expirado` | passou de `expira_em` |
| `token_invalido` | token inexistente |
| `telegram_de_outro_lead` | conflito real: outro telefone já tem esse telegram_id |

O `fundido` existe porque 21.824 leads vieram dos grupos **sem telefone**. Sem o
merge, todo lead que já está num grupo e recebe SMS bateria em
`telegram_de_outro_lead` e teria o vínculo **recusado** — o caso mais comum.
Conflito real (dois telefones disputando o mesmo telegram) continua sendo recusado:
a função não decide isso sozinha.

## Views

- `optin_funil` — leads, com_telegram, com_optin, ponte_completa, tokens gerados/usados
- `cobertura_grupos` — membros × leads conhecidos por grupo

## Fluxo n8n

`FLUXO START BOT NO TELEGRAM - BEKAS` (`MLg8oNfpLhsr3hDQ`), ativo.

```
Telegram /start → Extrair Payload → Tem Payload?
   ├─ sim → Resolver Opt-in (RPC) → Rotear Status
   │            ├─ vinculado (ok | fundido)
   │            ├─ ja_vinculado
   │            ├─ link_invalido
   │            └─ falha_tecnica
   └─ não → "use o link que você recebeu"
```

Credenciais: `Telegram account` (telegramApi) e `Custom Auth account`
(httpCustomAuth, headers `apikey` + `Authorization: Bearer <service_role>`).

O gateway do Supabase **exige o header `apikey`** — só `Authorization` retorna
"No API key found in request".

## Segurança

Toda tabela: RLS habilitado **e** forçado, zero policies, `REVOKE` de anon e
authenticated. Só `service_role` (que faz bypass de RLS) enxerga.

Funções: `SECURITY DEFINER` com `search_path = ''` e todo objeto qualificado com
`public.`. `EXECUTE` revogado de public/anon/authenticated, concedido só a
service_role. Views: `security_invoker = true` + REVOKE.

## Migrations

| arquivo | conteúdo |
|---|---|
| `0001_leads_master.sql` | a tabela base |
| `0002_optin_tokens.sql` | tokens + `gerar_optin_token` + `resolver_optin` |
| `0003_gerar_links.sql` | `registrar_lead`, `gerar_link_optin`, lote, `optin_funil` |
| `0004_normalizar_telefone_e164.sql` | corrige duplicação de telefone com/sem DDI |
| `0005_resolver_optin_merge.sql` | merge do lead só-Telegram + `55 + 0DDD` |

Aplicadas nesta ordem. As de 0003 em diante dependem das anteriores.

## ETL

`etl/preparar_import.py <dir_backup> [dir_saida]` converte o backup do CRM antigo
nos dois CSVs de import. Dedup por telefone normalizado mantendo o registro mais
completo; `optin_*` só é `true` com `consent_marketing` e sem `opt_out`.

Carga: `COPY` para staging, depois `promover_staging()`, que usa
`ON CONFLICT DO NOTHING` — rodar duas vezes não duplica nem sobrescreve.

## O que falta

- **Captura nos grupos.** 46.000 membros em 3 canais nunca tiveram um lead
  capturado (grupos 6, 7 e 8 — o 7 sozinho tem 31 mil, mais que toda a base de
  Telegram atual). O caminho é postar o link do bot dentro dos próprios grupos,
  com payload por grupo, e pedir o telefone via `request_contact` — que devolve o
  número verificado pelo Telegram.
- **Painel.** Depois que os números da captura existirem.
