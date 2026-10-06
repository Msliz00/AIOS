# PROJETO DESAPEGO — marketplace em grupos

Criado: 2026-10-06
Atualizado: 2026-10-06
Status: Fase 1 (fundacao) — nao iniciada

---

## DECISOES TOMADAS (06/10/2026)

| Item | Decisao |
|---|---|
| Modelo de receita | Marketplace com comissao |
| Recorte | Segmentado por categoria |
| Primeiro publico | Base propria ja existente |
| Escala inicial | 3 a 5 grupos |

---

## FATOS QUE DEFINEM A ARQUITETURA

1. **Comissao so e capturavel com pagamento intermediado.** Em grupo, comprador e
   vendedor fecham no privado. Sem o dinheiro passando pela plataforma, a comissao
   depende de boa vontade e vaza quase inteira.

2. **WhatsApp nao automatiza grupo.** A Groups API oficial da Cloud API limita a
   8 participantes por grupo — serve para atendimento, nao para comunidade.
   Bibliotecas nao-oficiais (Baileys, whatsapp-web.js) funcionam mas violam os
   termos e levam a ban. Nao construir receita sobre elas.

3. **Telegram automatiza tudo.** Bot API completa e gratuita, grupos ate 200 mil
   membros, pagamento nativo no bot.

### Limites por plataforma

| | Telegram | WhatsApp |
|---|---|---|
| Papel | motor transacional | captacao e vitrine |
| Membros por grupo | 200.000 | 1.024 |
| Agrupamento | canais ilimitados | comunidade: ate 100 grupos |
| Bot | completo, gratuito | inviavel (teto de 8) |
| Pagamento | nativo | fora da plataforma |

**Regra de ouro:** o anuncio aparece nos dois, mas fecha sempre no bot do Telegram.
E la que o split acontece.

---

## RECEITA EM DUAS CAMADAS

### Camada 1 — taxa de publicacao
Vendedor paga para anunciar ou para subir ao topo. Captura garantida, sem disputa,
sem risco. Sustenta a operacao enquanto a camada 2 amadurece.

### Camada 2 — comissao via escrow
Comprador paga no bot, a plataforma retem ate a confirmacao de entrega e repassa
descontando a comissao. O vendedor adere porque o selo de pagamento protegido faz
vender mais, nao por obrigacao.

Gateways com split: Mercado Pago, Asaas, Pagar.me, Efi.
Com split, o arranjo de pagamento e do gateway. Reter dinheiro de terceiro em conta
propria e um problema regulatorio bem maior.

---

## CATEGORIAS (4 grupos)

| Categoria | Ticket | Razao |
|---|---|---|
| Celulares e eletronicos | R$ 300–2.000 | maior liquidez do mercado de usados |
| Games e informatica | R$ 200–3.000 | publico engajado, entende escrow |
| Bebe e infantil | R$ 50–500 | recorrencia alta: vendedor vira comprador |
| Ferramentas e equipamentos | R$ 100–1.500 | ticket alto, pouca concorrencia organizada |

Moda ficou fora de proposito: volume alto e ticket de R$30 nao paga o custo de
moderacao. Entra quando o custo marginal for zero.

---

## PROGRAMA DE INDICACAO — credito, nao sorteio

### Por que nao sorteio
Lei 5.768/1971: distribuicao gratuita de premios mediante sorteio depende de
autorizacao previa da SPA/MF. A Portaria SPA/MF 1.818/2026 regulamentou o regime
sancionador, entao a fiscalizacao apertou. Multa chega a 100% do valor dos premios.

Chamar de concurso cultural nao resolve: a isencao vale so para concurso
*exclusivamente* cultural, julgado por merito intelectual. Ranking de indicacoes e
desempenho, nao criatividade — cai na mesma lei.

### Por que credito e melhor, alem da lei

| | Sorteio | Credito |
|---|---|---|
| Autorizacao | SPA/MF, prazo e taxa | nenhuma |
| Recompensa | probabilistica | imediata e certa |
| Destino do dinheiro | sai da operacao | volta para dentro |
| Retencao | zero apos o sorteio | credito so vale aqui |

O credito resgatavel so na plataforma alimenta a camada 1: o indicador ganha R$10 e
gasta em taxa de publicacao ou destaque.

### Mecanica
- Indicou -> o indicado publica o PRIMEIRO ANUNCIO -> os dois ganham credito
- Gatilho e o anuncio, nao o cadastro. Cadastro e vaidade, anuncio e inventario.
- **Trava anti-fraude:** credito so libera quando o anuncio do indicado passa no
  score minimo. Sem isso, paga-se por conta fantasma com foto tirada da internet.

Sorteio fica para depois, com autorizacao, dimensionado pelos numeros do piloto.

---

## ESTRUTURA DE AVALIACAO AUTOMATICA (bot)

E o mecanismo que transforma volume em qualidade. Anuncio ruim nao e bloqueado,
e enterrado no feed — o vendedor aprende sozinho.

### Camada A — score do anuncio (0-100), calculado na publicacao

| Criterio | Peso | Verificacao do bot |
|---|---|---|
| Fotos (quantidade, nitidez, fundo) | 30 | visao computacional |
| Descricao completa | 20 | campos e contagem de caracteres |
| Preco vs mediana da categoria | 25 | historico do banco |
| Estado declarado + evidencia | 15 | foto confere com o estado |
| Dados de entrega/retirada | 10 | campos preenchidos |

### Camada B — classificacao de estado
Menu fechado no bot, nunca texto livre:
`Novo lacrado` · `Seminovo` · `Usado — bom` · `Usado — com marcas` · `Com defeito`

### Camada C — score do vendedor
Vendas concluidas, avaliacao do comprador, disputas abertas, tempo de resposta.

### Ordem do feed
score do anuncio x score do vendedor x recencia

---

## NOMES CANDIDATOS (verificados por DNS em 06/10/2026)

"sem DNS" sugere disponivel mas nao garante: no .com.br muitos dominios ficam
registrados sem site. Confirmar no registro.br antes de comprar.

| Nome | .com.br | .com | Observacao |
|---|---|---|---|
| **REVIRA** | sem DNS | tomado | recomendado: aceita submarca por categoria |
| USADIN | sem DNS | sem DNS | direto, mas desvaloriza ticket alto |
| VIRALEVE | sem DNS | sem DNS | aspiracional, nao diz o que e |
| PASSA ADIANTE | sem DNS | sem DNS | cultural, 12 caracteres |
| GARIMPEI | sem DNS | tomado | fala so com o comprador |

REVIRA e o recomendado porque o recorte do projeto e por categoria, e so ele
suporta submarca sem travar: Revira Tech, Revira Baby, Revira Casa, Revira
Ferramentas.

Pendente de checagem manual (o proxy desta sessao bloqueia t.me e o Instagram
exige login): @ no Instagram, @ no Telegram, marca no INPI classe 35.

---

## ORDEM DE EXECUCAO

| Fase | Entrega | Estado |
|---|---|---|
| 1. Fundacao | marca, regras, bot do Telegram, 4 grupos nos dois apps | pendente |
| 2. Piloto | povoar com a base propria, 2 semanas sem monetizar, medir | pendente |
| 3. Camada 1 | taxa de publicacao e destaque | pendente |
| 4. Camada 2 | escrow com split, selo de vendedor verificado | pendente |
| 5. Escala | replicar playbook por categoria e regiao | pendente |

Nenhuma fase comeca sem a anterior validada.

---

## METRICAS DO PILOTO (fase 2)

Sem esses numeros nao se decide nada na fase 3:

- anuncios publicados por dia, por grupo
- taxa de resposta por anuncio
- negocios fechados por 100 anuncios
- ticket medio por categoria
- quantos membros saem na primeira semana

---

## RISCOS ABERTOS

| Risco | Impacto | Dono | Proximo passo |
|---|---|---|---|
| Base vem de iGaming; associacao pode queimar as duas marcas | alto | operador | marca separada, sem vinculo visivel |
| Vazamento da comissao antes do escrow existir | alto | operador | camada 1 sustenta ate a camada 2 subir |
| Moderacao manual no WhatsApp nao escala | medio | operador | WhatsApp so espelha; transacao vive no Telegram |
| Responsabilidade solidaria do marketplace (CDC) | medio | operador | consultar juridico antes da fase 4 |

---

## PENDENTE DE DEFINICAO

- Escolher entre os 5 candidatos e checar @ no Instagram/Telegram e marca no INPI
- Percentual da comissao e valor da taxa de publicacao
- Gateway escolhido
- Regiao de atuacao (nacional ou recorte)
