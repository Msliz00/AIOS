#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GREGO'S — feed Instagram 1080x1350, fundo vermelho.

Mesma estrutura da peca de referencia do perfil ("Hoje pede Grego's."),
com o preto trocado pelo degrade vermelho da marca.

A foto nao e recortada do fundo. Em vez disso as sombras dela sao
tingidas com o vinho da marca (split-tone), entao a imagem se integra ao
degrade como se tivesse sido iluminada assim. E o que evita o halo e a
mancha de um recorte por mascara.
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

S = "/tmp/claude-0/-home-user-AIOS/6f054a58-1907-5469-9055-58632a643f99/scratchpad"
FOTOS, FONTS, OUT = S + "/fotos/", S + "/fonts/", S + "/artes5/"
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350

RED_HOT  = (226, 28, 15)      # vermelho vivo da marca
RED_MID  = (150, 20, 30)
RED_DEEP = (74, 9, 15)        # vinho das bordas e das sombras
CREAM    = (245, 239, 226)
RED_INK  = (206, 26, 22)      # texto dentro da pilula creme

F_HEAD = FONTS + "Poppins700.ttf"
F_MARK = FONTS + "Chewy.ttf"
F_UI   = FONTS + "Inter700.ttf"
F_UIM  = FONTS + "Inter500.ttf"


# ------------------------------------------------------------------ texto
def font(p, s):
    return ImageFont.truetype(p, s)


def wrap(d, t, f, maxw):
    out, cur = [], ""
    for wd in t.split():
        cand = (cur + " " + wd).strip()
        if d.textlength(cand, font=f) <= maxw or not cur:
            cur = cand
        else:
            out.append(cur); cur = wd
    if cur:
        out.append(cur)
    return out


def adv_of(f, lines, size, extra=0.20):
    """Entrelinha que respeita acentos e descidas reais (á, ç, g, p)."""
    at = f.getbbox("Ah")[1]
    ab = f.getbbox("Ah")[3]
    rise = max(0, at - min(f.getbbox(l)[1] for l in lines))
    drop = max(0, max(f.getbbox(l)[3] for l in lines) - ab)
    return (ab - at) + rise + drop + extra * size


def fit(d, t, path, maxw, maxh, hi, lo, extra=0.20, max_lines=3):
    for s in range(hi, lo - 1, -2):
        f = font(path, s)
        ls = wrap(d, t, f, maxw)
        if len(ls) > max_lines:
            continue
        a = adv_of(f, ls, s, extra)
        blk = a * (len(ls) - 1) + (f.getbbox("Ah")[3] - f.getbbox("Ah")[1])
        if blk <= maxh and all(d.textlength(l, font=f) <= maxw for l in ls):
            return f, ls, s, a, blk
    f = font(path, lo); ls = wrap(d, t, f, maxw)
    a = adv_of(f, ls, lo, extra)
    return f, ls, lo, a, a * (len(ls) - 1) + (f.getbbox("Ah")[3] - f.getbbox("Ah")[1])


def put_centered(d, ytop, lines, f, fill, adv):
    top = f.getbbox("Ah")[1]
    y = ytop
    for l in lines:
        d.text((W / 2 - d.textlength(l, font=f) / 2, y - top), l, font=f, fill=fill)
        y += adv
    # base real da ultima linha, contando descendentes (g, p, q, j)
    return y - adv + (max(f.getbbox(lines[-1])[3], f.getbbox("Ah")[3]) - top)


def tracked_center(d, y, t, f, fill, tk):
    total = d.textlength(t, font=f) + tk * max(len(t) - 1, 0)
    x = W / 2 - total / 2
    for ch in t:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + tk


# ----------------------------------------------------------------- foto
def cover(path, bw, bh, fx=0.5, fy=0.5, zoom=1.0):
    im = Image.open(path).convert("RGB")
    sw, sh = im.size
    sc = max(bw / sw, bh / sh) * zoom
    im = im.resize((math.ceil(sw * sc), math.ceil(sh * sc)), Image.LANCZOS)
    nw, nh = im.size
    l, t = int((nw - bw) * fx), int((nh - bh) * fy)
    im = im.crop((l, t, l + bw, t + bh))
    im = ImageEnhance.Color(im).enhance(1.14)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=58, threshold=3))


def fundo_vermelho():
    """Degradê radial: vermelho vivo no centro-alto, vinho nas bordas."""
    cx, cy = W * 0.5, H * 0.30
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dmax = max(math.hypot(cx, cy), math.hypot(W - cx, cy),
               math.hypot(cx, H - cy), math.hypot(W - cx, H - cy))
    t = np.clip(np.hypot(xx - cx, yy - cy) / dmax, 0, 1) ** 1.10
    hot = np.array(RED_HOT, np.float32); mid = np.array(RED_MID, np.float32)
    deep = np.array(RED_DEEP, np.float32)
    meio = 0.44
    a = np.clip(t / meio, 0, 1)[..., None]
    b = np.clip((t - meio) / (1 - meio), 0, 1)[..., None]
    g = np.where(t[..., None] <= meio, hot + (mid - hot) * a, mid + (deep - mid) * b)
    return Image.fromarray(g.astype(np.uint8), "RGB")


def split_tone(im, expo=3.2):
    """Tinge as sombras da foto com o vinho da marca, preservando as altas-luzes.

    Sem máscara e sem limiar: a transição é contínua, então não há halo em
    volta do produto nem mancha na madeira — a foto inteira passa a viver
    sob a mesma luz vermelha do fundo.

    O expoente alto é o que salva o apetite: no preto puro o tingimento é
    total (a foto funde com o degradê), mas num meio-tom de 0,4 de
    luminância ele já cai para ~20%, então pão, queijo e carne seguem com
    a cor e o brilho de comida.
    """
    im = ImageEnhance.Brightness(im).enhance(1.05)
    a = np.asarray(im, np.float32)
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) / 255.0
    sombra = ((1.0 - lum) ** expo)[..., None]
    out = a + (np.array(RED_DEEP, np.float32) - a) * sombra
    out = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    return ImageEnhance.Color(out).enhance(1.06)


def photo_top(base, path, band_h, focus, zoom, fade=150):
    """Foto sangrando no topo, já tingida, dissolvendo no degradê."""
    ph = split_tone(cover(FOTOS + path, W, band_h, *focus, zoom=zoom)).convert("RGBA")
    m = Image.new("L", (W, band_h), 255)
    md = m.load()
    for y in range(band_h - fade, band_h):
        v = int(255 * (1 - (y - (band_h - fade)) / fade) ** 1.4)
        for x in range(W):
            md[x, y] = v
    ph.putalpha(m)
    base.alpha_composite(ph, (0, 0))


# ---------------------------------------------------------------- marca
def wordmark(d, y, size=48):
    f = font(F_MARK, size)
    t = "GREGO'S"
    d.text((W / 2 - d.textlength(t, font=f) / 2, y), t, font=f, fill=CREAM)


def cta_pill(base, cy, label="PEÇA PELO LINK DA BIO"):
    """Pílula creme, só tipografia. Nada de ícone desenhado nem UI falsa."""
    d = ImageDraw.Draw(base, "RGBA")
    f = font(F_UI, 29)
    tk = 2.1
    tw = d.textlength(label, font=f) + tk * (len(label) - 1)
    pad_x, ph = 52, 80
    pw = tw + pad_x * 2
    x0 = W / 2 - pw / 2
    d.rounded_rectangle([x0, cy - ph / 2, x0 + pw, cy + ph / 2],
                        radius=ph / 2, fill=CREAM)
    x = x0 + pad_x
    for ch in label:
        d.text((x, cy - 19), ch, font=f, fill=RED_INK)
        x += d.textlength(ch, font=f) + tk


# --------------------------------------------------------------- montagem
def build(c):
    img = fundo_vermelho().convert("RGBA")
    band = c.get("band", 800)
    photo_top(img, c["foto"], band, c.get("focus", (0.5, 0.5)), c.get("zoom", 1.0))
    d = ImageDraw.Draw(img, "RGBA")

    if c.get("mark", True):
        wordmark(d, 52)

    fh, hl, hs, ha, hh = fit(d, c["head"], F_HEAD, W - 150, 250, 86, 50, extra=0.14)
    fs = font(F_UIM, 29)
    sl = wrap(d, c["sub"], fs, W - 250) if c.get("sub") else []

    bloco = hh + (34 + len(sl) * 37 if sl else 0) + 92 + 40
    topo, base_y = band - 24, H - 132
    ytop = topo + max(0, ((base_y - topo) - bloco) / 2)

    yb = put_centered(d, ytop, hl, fh, CREAM, ha)
    for l in sl:
        d.text((W / 2 - d.textlength(l, font=fs) / 2, yb + 34), l, font=fs,
               fill=CREAM + (185,))
        yb += 37

    cta_pill(img, yb + 92, c.get("cta", "PEÇA PELO LINK DA BIO"))

    tracked_center(d, H - 74, "CAMPO LIMPO PAULISTA · VÁRZEA PAULISTA · JUNDIAÍ",
                   font(F_UIM, 20), CREAM + (150,), 1.5)
    return img.convert("RGB")


PECAS = [
    dict(n="01_grego_de_sempre", foto="037_sirio.jpg", focus=(0.40, 0.54), zoom=1.75,
         band=930, head="O grego de sempre.",
         sub="Carne no espeto, vinagrete e queijo maçaricado."),

    dict(n="02_gregao_queijo", foto="foto gregos 16.jpg", focus=(0.46, 0.55), zoom=1.42,
         band=930, head="Queijo até a borda.",
         sub="O Gregão vem maçaricado de ponta a ponta."),

    dict(n="03_macarico", foto="foto gregos 06.jpg", focus=(0.50, 0.47), zoom=1.28,
         band=930, head="Maçaricado na sua frente.",
         sub="O queijo derrete na hora do pedido."),

    dict(n="04_espeto", foto="foto gregos 04.jpg", focus=(0.56, 0.48), zoom=1.22,
         band=930, head="Cortado na hora, do espeto.",
         sub="Churrasco grego de verdade, fatiado só quando você pede."),

    dict(n="05_combo", foto="039_sirio.jpg", focus=(0.50, 0.52), zoom=1.55,
         band=930, head="Resolve a noite inteira.",
         sub="Grego + batata + bebida gelada."),

    dict(n="06_mesa_farta", foto="059_mesa-completa-frontal.jpg", focus=(0.50, 0.46), zoom=1.22,
         band=940, head="Hoje pede Grego's.",
         sub="Mesa farta pra dividir com todo mundo."),

    dict(n="07_primeira_mordida", foto="foto gregos 29.jpg", focus=(0.46, 0.20), zoom=1.18,
         band=930, head="A primeira mordida explica.",
         sub="Difícil de descrever. Fácil de repetir."),

    dict(n="08_toda_noite_enche", foto="foto gregos 18.jpg", focus=(0.47, 0.62), zoom=1.14, mark=False,
         band=930, head="Toda noite enche.",
         sub="E não é por acaso. Vem entender o motivo."),

    dict(n="09_cabe_todo_mundo", foto="foto gregos 13.jpg", focus=(0.50, 0.47), zoom=1.32,
         band=930, head="Aqui cabe todo mundo.",
         sub="Salão novo, com espaço pra sentar sem pressa."),

    dict(n="10_montagem", foto="foto gregos 05.jpg", focus=(0.44, 0.53), zoom=1.45,
         band=930, head="O segredo tá na montagem.",
         sub="Pão aberto, carne fatiada na hora e vinagrete por cima."),
]

if __name__ == "__main__":
    for p in PECAS:
        img = build(p)
        path = f"{OUT}GREGOS_{p['n']}.jpg"
        img.save(path, quality=93, subsampling=0, optimize=True)
        print(path, os.path.getsize(path) // 1024, "KB")
