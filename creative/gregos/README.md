# GREGO'S — gerador de artes para feed (Instagram 4:5)

Gera as 10 mídias 1080x1350 da campanha de captação da Grego's
(Campo Limpo Paulista · Várzea Paulista · Jundiaí).

## Sistema visual

Calcado na peça de referência da marca ("4 NOVOS GREGO'S"):

| Token | Hex | Uso |
|---|---|---|
| Vinho claro | `#8A1523` | centro do fundo radial |
| Vinho escuro | `#560C16` | bordas do fundo, rodapé |
| Vermelho Grego's | `#E8232A` | blob do wordmark, selo estrela |
| Vermelho escuro | `#B0141C` | contorno do wordmark |
| Creme | `#F6F0E1` | toda a tipografia |

Elementos de assinatura: fundo vinho radial, wordmark bubbly sobre blob
vermelho, selo estrela de 12 pontas, faixa xadrez e painel de foto com
cantos arredondados.

Tipografia: Nunito 900 (headline), Chewy (wordmark/selo), Baloo 2 700
(apoio), Inter (CTA).

> O wordmark é reconstrução tipográfica — o arquivo oficial do logo não
> estava disponível. Substituir por `logo_oficial.png` quando houver.

## Layouts

- `cartaz` — vinho + headline centralizada no topo + painel de foto
- `split` — foto no topo + faixa xadrez + bloco vinho com headline
- `full` — foto sangrando + véu vinho + headline na base

## Uso

```bash
pip install pillow
python3 build_artes.py       # escreve em artes2/
```

As fotos de origem ficam em `fotos/` e as fontes em `fonts/` (Google
Fonts). Para trocar headline, foto, selo ou recorte, edite a lista
`PECAS` no fim do script — cada peça aceita `foto`, `focus`, `zoom`,
`badge`, `head`, `sub`, `lay` e `mark`.
