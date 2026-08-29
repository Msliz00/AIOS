#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GREGO'S — troca o fundo preto das artes por degradê vermelho da marca.

O fundo das peças (e das fotos de estúdio) é praticamente preto, então em
vez de recortar o produto usamos um 'screen' ponderado pela escuridão:
onde a arte é escura, entra o degradê; onde é clara (produto, tipografia,
pílulas), a arte original é preservada. Isso troca o fundo sem tocar em
nada que já estava desenhado por cima.

Vermelhos tirados do próprio material da marca:
  #E21C0F  vermelho vivo (card "HOJE PEDE GREGO'S." do pacote)
  #8A1523  vinho médio   (cartaz "4 NOVOS GREGO'S")
  #4E0A10  vinho escuro  (bordas)
"""
import os, sys, glob
import numpy as np
from PIL import Image, ImageFilter

SRC = "zipin/export/ads"
DST = "export/ads"

RED_HOT  = np.array([226, 28, 15], dtype=np.float32)   # centro
RED_MID  = np.array([138, 21, 35], dtype=np.float32)   # meio
RED_DEEP = np.array([ 78, 10, 16], dtype=np.float32)   # bordas

# até onde a arte é considerada "fundo". Acima disso, preserva o original.
# Limiar baixo + curva dura mantém o produto intacto: só o preto vira vermelho.
LIMIAR = 74.0
CURVA  = 1.45


def gradiente(w, h):
    """Degradê radial: vermelho vivo no centro-alto, vinho nas bordas."""
    cx, cy = w * 0.5, h * 0.34
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # normaliza pela maior distância possível até um canto
    dmax = max(np.hypot(cx, cy), np.hypot(w - cx, cy),
               np.hypot(cx, h - cy), np.hypot(w - cx, h - cy))
    t = np.clip(np.hypot(xx - cx, yy - cy) / dmax, 0, 1) ** 1.15

    g = np.zeros((h, w, 3), dtype=np.float32)
    meio = 0.46
    a = np.clip(t / meio, 0, 1)[..., None]
    b = np.clip((t - meio) / (1 - meio), 0, 1)[..., None]
    g = np.where(t[..., None] <= meio,
                 RED_HOT + (RED_MID - RED_HOT) * a,
                 RED_MID + (RED_DEEP - RED_MID) * b)
    return g


def recolor(path_in, path_out):
    im = Image.open(path_in).convert("RGB")
    w, h = im.size
    a = np.asarray(im, dtype=np.float32)

    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    peso = np.clip((LIMIAR - lum) / LIMIAR, 0, 1) ** CURVA

    # Fechamento morfológico da silhueta do produto: sem isso, os vazios
    # escuros de dentro (recheio de carne, sombra entre os pães) também
    # virariam vermelho vivo.
    silhueta = Image.fromarray(((lum >= LIMIAR) * 255).astype(np.uint8), "L")
    for _ in range(5):
        silhueta = silhueta.filter(ImageFilter.MaxFilter(9))
    for _ in range(5):
        silhueta = silhueta.filter(ImageFilter.MinFilter(9))
    silhueta = silhueta.filter(ImageFilter.GaussianBlur(3))
    protegido = np.asarray(silhueta, dtype=np.float32) / 255.0
    peso = peso * (1.0 - protegido)
    peso[peso < 0.02] = 0.0          # pixel do produto sai idêntico ao original
    peso = peso[..., None]

    g = gradiente(w, h)
    # mistura direta, não screen: screen vazava luz vermelha para dentro do produto
    out = a * (1 - peso) + g * peso

    os.makedirs(os.path.dirname(path_out), exist_ok=True)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(
        path_out, quality=99, subsampling=0, optimize=True)


if __name__ == "__main__":
    alvos = sys.argv[1:] or sorted(glob.glob(f"{SRC}/*.jpg"))
    for p in alvos:
        out = os.path.join(DST, os.path.basename(p))
        recolor(p, out)
        print(out, os.path.getsize(out) // 1024, "KB")
