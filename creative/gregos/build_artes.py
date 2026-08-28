#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GREGO'S — feed Instagram 1080x1350.

Padrao da peca de referencia do proprio perfil ("Hoje pede Grego's."):
fundo preto, foto sangrando no topo com fade, wordmark pequeno e
centralizado, headline creme em caixa baixa terminada em ponto, e
botao-pilula branco de CTA. Sem adesivo, sem manuscrito, sem xadrez.
"""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

S = "/tmp/claude-0/-home-user-AIOS/6f054a58-1907-5469-9055-58632a643f99/scratchpad"
FOTOS, FONTS, OUT = S + "/fotos/", S + "/fonts/", S + "/artes4/"
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350

BLACK  = (13, 13, 13)
CREAM  = (242, 236, 221)
WHITE  = (255, 255, 255)
RED    = (232, 35, 42)
MUTED  = (150, 143, 130)

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


def photo_top(base, path, band_h, focus, zoom, fade=170):
    """Foto sangrando no topo, dissolvendo no preto — como na referência."""
    ph = cover(FOTOS + path, W, band_h, *focus, zoom=zoom).convert("RGBA")
    a = Image.new("L", (W, band_h), 255)
    ad = a.load()
    for y in range(band_h - fade, band_h):
        v = int(255 * (1 - (y - (band_h - fade)) / fade) ** 1.5)
        for x in range(W):
            ad[x, y] = v
    # leve escurecida no topo, para o wordmark respirar
    dark = Image.new("RGBA", (W, band_h), (0, 0, 0, 0))
    g = Image.new("L", (1, band_h), 0); gp = g.load()
    for y in range(band_h):
        gp[0, y] = int(120 * max(0.0, 1 - y / 240) ** 1.4)
    dark.putalpha(g.resize((W, band_h)))
    dark.paste(Image.new("RGB", (W, band_h), (0, 0, 0)), (0, 0), dark.split()[3])
    ph.alpha_composite(dark)
    ph.putalpha(a)
    base.alpha_composite(ph, (0, 0))


# ---------------------------------------------------------------- marca
def wordmark(d, y, size=46):
    f = font(F_MARK, size)
    t = "GREGO'S"
    x = W / 2 - d.textlength(t, font=f) / 2
    d.text((x, y), t, font=f, fill=CREAM)
    # registro ®, como na peca da marca
    fr = font(F_UIM, int(size * 0.30))
    d.text((x + d.textlength(t, font=f) + 8, y + size * 0.18), "®", font=fr, fill=CREAM)


def link_icon(base, cx, cy, s, color):
    """Icone de corrente (dois elos na diagonal), desenhado em camada propria."""
    S4 = 4                                   # supersampling, pra borda limpa
    box = int(s * 2.0) * S4
    lay = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    w = max(2, int(s * 0.105)) * S4
    elo_w, elo_h = s * 0.70 * S4, s * 0.34 * S4
    shift = elo_w * 0.58                     # elos colineares que se cruzam
    c = box / 2
    for sign in (-1, 1):
        x0 = c + sign * shift / 2 - elo_w / 2
        y0 = c - elo_h / 2
        dl.rounded_rectangle([x0, y0, x0 + elo_w, y0 + elo_h],
                             radius=elo_h / 2, outline=color + (255,), width=w)
    lay = lay.rotate(-45, resample=Image.BICUBIC)
    lay = lay.resize((int(box / S4), int(box / S4)), Image.LANCZOS)
    base.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))


def cta_pill(base, cy, label="PEÇA AGORA!"):
    """Pílula branca de CTA — mesma forma da referência, cor da marca."""
    d = ImageDraw.Draw(base, "RGBA")
    f = font(F_UI, 33)
    tk = 1.6
    tw = d.textlength(label, font=f) + tk * (len(label) - 1)
    icon = 52
    inner = icon + 20 + tw
    pad_x, ph = 46, 86
    pw = inner + pad_x * 2
    x0, y0 = W / 2 - pw / 2, cy - ph / 2
    d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=ph / 2, fill=WHITE)
    link_icon(base, x0 + pad_x + icon / 2, cy, icon, RED)
    x = x0 + pad_x + icon + 20
    for ch in label:
        d.text((x, cy - 22), ch, font=f, fill=RED)
        x += d.textlength(ch, font=f) + tk


# --------------------------------------------------------------- montagem
def build(c):
    img = Image.new("RGBA", (W, H), BLACK + (255,))
    band = c.get("band", 800)
    photo_top(img, c["foto"], band, c.get("focus", (0.5, 0.5)), c.get("zoom", 1.0))
    d = ImageDraw.Draw(img, "RGBA")

    if c.get("mark", True):
        wordmark(d, 54)

    fh, hl, hs, ha, hh = fit(d, c["head"], F_HEAD, W - 150, 250, 88, 50, extra=0.14)
    fs = font(F_UIM, 29)
    sl = wrap(d, c["sub"], fs, W - 230) if c.get("sub") else []

    bloco = hh + (30 + len(sl) * 36 if sl else 0) + 84 + 43
    topo, base_y = band - 40, H - 130
    ytop = topo + max(0, ((base_y - topo) - bloco) / 2)

    yb = put_centered(d, ytop, hl, fh, CREAM, ha)
    for l in sl:
        d.text((W / 2 - d.textlength(l, font=fs) / 2, yb + 30), l, font=fs, fill=MUTED)
        yb += 36

    cta_pill(img, yb + 84, c.get("cta", "PEÇA AGORA!"))

    f2 = font(F_UIM, 21)
    tracked_center(d, H - 72, "CAMPO LIMPO PAULISTA · VÁRZEA PAULISTA · JUNDIAÍ",
                   f2, (150, 143, 130), 1.1)
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
