# SPEC — Bot de Ofertas (envio nos grupos Telegram)

> Status: **rascunho — aguardando validação do 00BABY** (2026-11-27)
> Escopo: **apenas envio de mensagens**. Pagamento/planilha fora.

## Fluxo
```
Produto entra na fila → Painel (aprovar/editar) → Agente coleta dados → Bot posta nos grupos selecionados
```

## Campos da oferta (o que o agente precisa entregar)
| campo | exemplo | origem |
|---|---|---|
| `imagem` | foto do produto | página do produto |
| `titulo` | Mala de bordo 10kg | página do produto |
| `preco_de` | 361 | página do produto |
| `preco_pix` 💰 | 150 | página do produto |
| `preco_cartao` 💳 | 167 | página do produto |
| `desconto_pct` | **calculado**: (de − pix) / de | automático (nunca digitado) |
| `link_afiliado` | URL | plataforma de afiliado |
| `cupom` | 8ZYXWK-63T8 | plataforma / manual |
| `grupos[]` | ids dos grupos | seleção no painel |

## Template (HTML do Telegram)
```
🔥 OFERTA IMPERDÍVEL 🔥

🛒 {titulo}
💰 <s>R$ {preco_de}</s> <b>POR R$ {preco_pix}</b>
💳 <s>R$ {preco_de}</s> <b>POR R$ {preco_cartao}</b>
💎 <b>{desconto_pct}% DE DESCONTO</b>

🎁 <b>PRODUTO ABAIXO</b> 🎁
```

## Variantes A/B
| | A (grupo principal) | B (grupo secundário) |
|---|---|---|
| Link | "🔗 COMPRE AQUI" no texto | Botão **PRODUTO AQUI📌** → `url` = link afiliado |
| Cupom | "🎟 {cupom}" no texto | Botão **CUPOM AQUI🎟️** → `copy_text` = cupom |

Botão de copiar = `InlineKeyboardButton.copy_text` (Bot API nativa).

## Limitações técnicas
1. **Emojis Premium animados não saem pelo bot** (custom emoji em bot exige username comprado no Fragment). Bot usa emoji padrão. Alternativas: comprar username no Fragment, ou postar via conta de usuário Premium (userbot — risco de banimento).
2. **Telegram não conta cliques** em botão de link nem de copiar. Para medir o A/B: link passa por redirecionador próprio (conta clique) + relatório da plataforma de afiliado (conta venda).
3. Legenda de foto: máx. 1024 caracteres (template usa ~250).

## Bug no exemplo enviado
361 → 150 = **58%**, 361 → 167 = **54%**; a mensagem diz 34%. Desconto deve ser sempre calculado pelo sistema.
