# Fontes de documentos gerados

HTML de origem dos PDFs entregues. Para regerar:

```bash
/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
  --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf=SAIDA.pdf docs/fontes/ARQUIVO.html
```

Os erros de `dbus` no console sao ruido do Chromium sem sessao grafica e nao
afetam o PDF.

| Arquivo | PDF | Paginas |
|---|---|---|
| `projeto_desapego.html` | PROJETO_DESAPEGO.pdf | 8 |
