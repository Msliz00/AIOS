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
vermelho, selo estrela de 12 pontas, faixa xadrez e card de foto com
cantos arredondados.

Tipografia: Nunito 900 (headline), Chewy (wordmark/selo), Baloo 2 700
(apoio), Caveat 700 (manuscrito), Inter (CTA).

## Camada humanizada

O que impede o conjunto de parecer template:

- recado manuscrito em cada peça, escrito torto;
- traço de marcador sob a headline — três passadas com tremido e ponta
  que escapa, em vez de uma barra reta;
- selo estrela colado torto (-11° a +9°), como adesivo;
- card de foto girado 1 a 2 graus, preso por fita adesiva translúcida
  nos cantos.

Nenhum eixo fica perfeitamente alinhado, de propósito. As peças 07 e 09
usam clientes reais da loja no lugar do modelo de estúdio.

> O wordmark é reconstrução tipográfica — o arquivo oficial do logo não
> estava disponível. Substituir por `logo_oficial.png` quando houver.

## Layouts

- `cartaz` — vinho + headline centralizada no topo + card de foto com fita
- `split` — foto no topo + faixa xadrez + bloco vinho com headline
- `full` — foto sangrando + véu vinho + headline na base

## Uso

```bash
pip install pillow
python3 build_artes.py       # escreve em artes3/
```

As fotos de origem ficam em `fotos/` e as fontes em `fonts/` (Google
Fonts). Para trocar headline, foto, selo ou recorte, edite a lista
`PECAS` no fim do script — cada peça aceita `foto`, `focus`, `zoom`,
`tilt`, `badge`, `badge_rot`, `head`, `hand`, `hand_rot`, `sub`, `lay`
e `mark`.
