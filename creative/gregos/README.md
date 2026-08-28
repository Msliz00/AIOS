# GREGO'S — gerador de artes para feed (Instagram 4:5)

Gera as 10 mídias 1080x1350 da campanha de captação da Grego's
(Campo Limpo Paulista · Várzea Paulista · Jundiaí).

## Padrão visual

Calcado no story de referência do próprio perfil, "Hoje pede Grego's.".
Estrutura igual nas 10 peças:

1. foto sangrando no topo (~59% da altura), dissolvendo num fade de
   210px até o preto — sem moldura, sem card;
2. wordmark `GREGO'S` pequeno e centralizado sobre a foto, com `®`;
3. headline creme, centralizada, em **caixa baixa** e terminada em
   **ponto final** — é a assinatura de voz da marca;
4. sub em cinza quente, uma linha;
5. pílula branca de CTA com ícone de corrente + `PEÇA AGORA!`;
6. as três praças em caixa alta, pequenas, no rodapé.

| Token | Hex | Uso |
|---|---|---|
| Preto | `#0D0D0D` | fundo |
| Creme | `#F2ECDD` | headline e wordmark |
| Cinza quente | `#968F82` | sub e praças |
| Branco | `#FFFFFF` | pílula de CTA |
| Vermelho Grego's | `#E8232A` | texto e ícone da pílula |

Tipografia: Nunito 900 (headline), Chewy (wordmark), Inter 500/700
(sub e CTA).

> O wordmark é reconstrução tipográfica — o arquivo oficial do logo não
> estava disponível. Substituir quando houver.

### Uma diferença proposital em relação ao story

No story, o `PEÇA AGORA!` é o sticker de link do Instagram: azul e
clicável. No feed esse botão não clica, então a pílula mantém a forma
mas usa o vermelho da marca no lugar do azul — fica na identidade sem
parecer um botão morto. Nos stories, use o sticker nativo por cima.

## Uso

```bash
pip install pillow
python3 build_artes.py       # escreve em artes4/
```

As fotos de origem ficam em `fotos/` e as fontes em `fonts/` (Google
Fonts). Para trocar foto, headline, sub ou enquadramento, edite a lista
`PECAS` no fim do script — cada peça aceita `foto`, `focus`, `zoom`,
`band`, `head`, `sub`, `cta` e `mark`.
