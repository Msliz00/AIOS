# CONTINUIDADE — IGAMING-MASTER-FLOW

Ultima atualizacao: 2026-09-22

---

## 1. BEKAS S36 — links de midia  ✅ CONCLUIDO

Planilha: `ANALISE DE CRIATIVOS EXPERTS - BEKAS`
ID: `1IpISy5pq1vimkKGqx-KNfj3QX-CKg786vfSy6XW_l2g`

| Aba | ID | Linhas | Resultado |
|---|---|---|---|
| MEDIANO E EXCELENTE S36 · 31/08–06/09 -> MARQUES | 552723389 | 26 | 6 corrigidos, 18 ja corretos, 2 fora do mapa |
| MARQUES | 2106965851 | 58 | 16 novos, 6 corrigidos, 18 ja corretos, 18 fora do mapa |

Total gravado: 16 novos + 12 corrigidos. 55 de 58 linhas da MARQUES com link.

Script: `scripts/bekas_corrigir_links.gs`
Mapeamento: `scripts/rodri_midias_mapeamento.json` (40 midias, 4 subpastas)

### Decisoes tomadas
- Execucao via Apps Script **vinculado a planilha** (Extensoes > Apps Script). Terminal,
  n8n e conector do Drive nao conseguem gravar celula: credencial do n8n expirada desde
  11/09 e sem service account JSON.
- Abas identificadas por **sheet ID (gid)**, nao por nome. Os caracteres `·` e `–` do
  nome corrompem no copiar/colar.
- Sem `getUi().alert()`: ele bloqueia esperando clique e estoura o limite de 6 minutos
  do Apps Script. Usar `ss.toast()` + `Logger.log()`.
- Sobrescrita de link compara **file id do Drive**, nao o texto da URL.
- Celula com texto (headline) nunca e sobrescrita.

### Pendencia aceita (nao e bloqueio)
3 linhas da MARQUES seguem sem link, por decisao do operador em 16/09:
`AD 3 - 50X`, `AD 4 - 30X`, `AD 5 - 100X (23-07-26)`. Nao estao em nenhuma das 4
subpastas de FINALIZADOS RODRI. Dono: operador. Proximo passo: informar a pasta de
origem se um dia precisar fechar em 100%.

### ⚠️ Risco operacional aberto
Os links anteriores (mapeados via conector) apontavam para o arquivo errado — a variante
`_SL` e a nao-`_SL` compartilhavam o mesmo file id. Ids removidos da planilha:

| file id removido | estava em |
|---|---|
| `1dOYhOI2FO5a6eejM4QtUqLFzoWedtBQN` | CXL_AD02_SL |
| `1vO35FPjyEd5ZsIwwNDoMhuKTd6G0LWj7` | CXL_AD03, CXL_AD03_SL |
| `1ARIefT5xh6InKJiP92-C0PwFOPwX2FSV` | CXL_AD04 |
| `1SW15-dw_SQCzy3Ov9-Y-DoBKNELVlB4-` | CXL_AD05 |
| `12eoeF5dIkLpYGblGZ2ciD4RjGFPZzJNc` | CXL_AD08_SL |

Se algum criativo foi subido na semana de 31/08 usando esses links, foi ao ar o arquivo
errado. Dono: operador. Proximo passo: conferir o que entrou em campanha.

### Aguardando decisao
A coluna A da aba MEDIANO E EXCELENTE foi pintada (verde = com link, vermelho = sem).
Essa aba nao estava pintada antes e a pintura nao tinha sido pedida para ela.
Dono: operador. Proximo passo: dizer se mantem ou se limpa.

---

## 1b. BEKAS S38 — links via CRIAS MARQUES  ✅ CONCLUIDO

Aba: `S38 · 14–20/09 -> MARQUES`, gid **1229843098**
Fonte: `CRIAS MARQUES - LINK` (`1Pt8vO6bClfRH4Gx5BbNkYJUTHhxtlpsv1haw3unlXJ4`), A = nome, C = link
Conferencia: mapeamento do Drive (`18QuXwGwpkWiLd8CTojXdgOWN6j91U2J27A_5YCzH-yk`)
Script: `scripts/bekas_s38_crias.gs`

Resultado: 54 linhas, 54 com link. **100% preenchida.**
40 preenchidos | 14 ja tinham | 0 protegidos | **0 sem correspondencia**

### Decisoes tomadas
- `PREFERIR_DRIVE = true`. A CRIAS carrega os mesmos file ids errados que ja tinham
  sido corrigidos na MARQUES da S36, entao o link real do Drive vence. As 6 linhas
  afetadas: C2 CXL_AD08_SL, C4 CXL_AD05, C32 CXL_AD02_SL, C45 CXL_AD03,
  C48 CXL_AD04, C55 CXL_AD03_SL.
- Aba identificada por gid, nao por nome.
- Casamento de nome em duas passadas (normalizado e so-alfanumerico). A segunda nunca
  foi exercida: a nomenclatura da CRIAS e da BEKAS bate 100% na forma exata.

### ⚠️ A CRIAS MARQUES continua com os 6 links errados
Corrigimos o destino, nao a origem. A proxima semana que puxar da CRIAS sem o
`PREFERIR_DRIVE` herda o erro de novo.
Dono: operador. Proximo passo: corrigir a coluna C da CRIAS, ou manter
`PREFERIR_DRIVE = true` como padrao em toda execucao futura.

---

## 2. Mapeamento FINALIZADOS RODRI  ✅ CONCLUIDO

Pasta: `1-qfbrM3y_wuuVXQlU2i5atNWPzcZ343T`
Planilha gerada: `18QuXwGwpkWiLd8CTojXdgOWN6j91U2J27A_5YCzH-yk`

40 arquivos em 4 subpastas:

| Subpasta | ID | Arquivos |
|---|---|---|
| CAIXINHA | `1ZyJZh3qhm8y6PHaicVrYPtBB-EnGoRwt` | 16 |
| AD 14 - GRAVACAO DE TELA 20X | `1Li4I1OYR-9gvYzvdevMz4I-p23cXaREH` | 8 |
| AD 13 - NARRACAO 100X - HOOK CAIXINHA | `14hMWsWHyqms2P7QF76Di0gDmZt0ty9og` | 8 |
| AD 12 - NARRACAO 50X | `19vOXBhE2H1qpt3R1-h0wRyLZjOVywhtl` | 8 |

Resolveu o problema que durou uma semana: o conector do Drive reportava essas subpastas
como vazias e nunca listou a AD 12. O Apps Script, rodando com a permissao do proprio
operador, achou os 40 arquivos.

Nomes no Drive usam `/` (`31/ago`); na planilha aparecem com `-` (`31-ago`). A funcao
`chave()` normaliza isso.

---

## 3. Cruzamento ADS WILL x S37  ⏸ INTERROMPIDO

Pasta: `FINZALIZADOS ADS WILL - 04/08/2026 ofc` (`1STDMANS4_hI0TqrMgZmGIWlTjU3CdPCR`), 18 arquivos
Planilha: `[@MarquesAviator] ANALISES CRIATIVOS` (`1fBzEB4QtncHeTrRP5D3JzUoTti6sXEVB3B_cTU-omWc`)
Aba: `S37 · 07–13/09` (ID 1567161386), 56 linhas

Resultado preliminar, **nao validado**: 14 dos 18 arquivos `AD_XX_CORTE` aparecem na S37.
Fora: `AD_6`, `AD_3`, `Cortedelive_20X_ALPHA`, `PS_cortedelive_meet`.

Dono: Claude. Proximo passo: refazer a varredura pelo Apps Script (o conector nao e
confiavel para ler subpasta, ver item 2) e gerar o arquivo isolando essas midias.

---

## 4. Assistente de metricas no WhatsApp  ⏸ NAO INICIADO

Guia entregue: `Assistente_Metricas_WhatsApp.pdf` (4 paginas).

Recomendacao: **Apps Script com gatilho diario**, nao n8n. O n8n so acrescenta uma peca
que ja esta quebrada (credencial Google expirada) para um fluxo de um passo so.

Dono: operador. Proximo passo: registrar o numero na Meta (WhatsApp Business Cloud API)
e aprovar o template — mensagem iniciada pelo negocio exige template pre-aprovado.

---

## 5. Infra — pendencias que travam automacao

| Item | Estado | Dono | Proximo passo |
|---|---|---|---|
| Credencial Google do n8n | Expirada desde 11/09 | operador | Reconectar no n8n, ou abandonar o n8n |
| n8n HTTP Request | Bloqueado por config da credencial | operador | Liberar a flag, ou abandonar |
| Service account JSON | Nunca fornecido | operador | Criar no GCP e compartilhar a planilha com o e-mail da SA |

Enquanto isso, **Apps Script vinculado a planilha e o unico caminho que grava**.
