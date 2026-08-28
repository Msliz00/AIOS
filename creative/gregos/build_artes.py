#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GREGO'S — feed Instagram 1080x1350.
Sistema calcado na peca de referencia enviada pelo cliente:
fundo vinho radial, tipografia creme arredondada, wordmark bubbly
sobre blob vermelho, selo estrela e faixa xadrez no rodape.
"""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

S = "/tmp/claude-0/-home-user-AIOS/6f054a58-1907-5469-9055-58632a643f99/scratchpad"
FOTOS, FONTS, OUT = S + "/fotos/", S + "/fonts/", S + "/artes2/"
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350
M = 72

WINE_HI = (138, 21, 35)
WINE_LO = (86, 12, 22)
RED     = (232, 35, 42)
RED_DK  = (176, 20, 28)
CREAM   = (246, 240, 225)
INK     = (44, 8, 12)

F_HEAD = FONTS + "Nunito900.ttf"        # headline (match da referencia)
F_MARK = FONTS + "Chewy.ttf"            # wordmark / selos bubbly
F_SUB  = FONTS + "Baloo700.ttf"         # apoio
F_UI   = FONTS + "Inter700.ttf"
F_UIM  = FONTS + "Inter500.ttf"


# ------------------------------------------------------------------ texto
def font(p, s):
    return ImageFont.truetype(p, s)


def tw(d, t, f, tk=0):
    return d.textlength(t, font=f) + tk * max(len(t) - 1, 0)


def tracked(d, xy, t, f, fill, tk=0, right=False, **kw):
    x, y = xy
    if right:
        x -= tw(d, t, f, tk)
    for ch in t:
        d.text((x, y), ch, font=f, fill=fill, **kw)
        x += d.textlength(ch, font=f) + tk
    return x


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


def adv_of(f, lines, size, extra=0.13):
    ct = f.getbbox("H")[1]; cb = f.getbbox("H")[3]
    rise = max(0, ct - min(f.getbbox(l)[1] for l in lines))
    drop = max(0, max(f.getbbox(l)[3] for l in lines) - cb)
    return (cb - ct) + rise + drop + extra * size


def fit(d, t, path, maxw, maxh, hi, lo, extra=0.16, max_lines=3):
    for s in range(hi, lo - 1, -2):
        f = font(path, s)
        ls = wrap(d, t, f, maxw)
        if len(ls) > max_lines:
            continue
        a = adv_of(f, ls, s, extra)
        blk = a * (len(ls) - 1) + (f.getbbox("H")[3] - f.getbbox("H")[1])
        if blk <= maxh and all(d.textlength(l, font=f) <= maxw for l in ls):
            return f, ls, s, a, blk
    f = font(path, lo); ls = wrap(d, t, f, maxw)
    a = adv_of(f, ls, lo, extra)
    return f, ls, lo, a, a * (len(ls) - 1) + (f.getbbox("H")[3] - f.getbbox("H")[1])


def put_lines(d, x, ytop, lines, f, fill, adv, center=None, **kw):
    ct = f.getbbox("H")[1]
    y = ytop
    for l in lines:
        px = x if center is None else center - d.textlength(l, font=f) / 2
        d.text((px, y - ct), l, font=f, fill=fill, **kw)
        y += adv
    return y - adv + (f.getbbox("H")[3] - ct)


# -------------------------------------------------------------- graficos
def wine_bg():
    """Fundo vinho radial, como no cartaz de referencia."""
    g = Image.new("RGB", (W, H), WINE_LO)
    px = g.load()
    cx, cy, mx = W * 0.5, H * 0.30, math.hypot(W * 0.5, H * 0.72)
    for y in range(H):
        for x in range(0, W, 3):
            t = min(1.0, math.hypot(x - cx, y - cy) / mx) ** 1.25
            c = tuple(int(WINE_HI[i] + (WINE_LO[i] - WINE_HI[i]) * t) for i in range(3))
            for k in range(3):
                if x + k < W:
                    px[x + k, y] = c
    return g


def cover(path, bw, bh, fx=0.5, fy=0.5, zoom=1.0):
    im = Image.open(path).convert("RGB")
    sw, sh = im.size
    sc = max(bw / sw, bh / sh) * zoom
    im = im.resize((math.ceil(sw * sc), math.ceil(sh * sc)), Image.LANCZOS)
    nw, nh = im.size
    im = im.crop((int((nw - bw) * fx), int((nh - bh) * fy),
                  int((nw - bw) * fx) + bw, int((nh - bh) * fy) + bh))
    im = ImageEnhance.Color(im).enhance(1.16)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))


def round_panel(img, photo, box, radius=44, ring=8):
    """Cola a foto num painel de cantos arredondados com anel creme."""
    x0, y0, x1, y1 = box
    m = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], radius=radius, fill=255)
    if ring:
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle([x0 - ring, y0 - ring, x1 + ring, y1 + ring],
                            radius=radius + ring, fill=CREAM + (255,))
    img.paste(photo, (x0, y0), m)


def checker(d, y, h=34, cell=45, color=CREAM, offset=0):
    """Faixa xadrez — elemento de assinatura da marca."""
    n = W // cell + 2
    for i in range(n):
        if (i + offset) % 2 == 0:
            d.rectangle([i * cell, y, i * cell + cell, y + h], fill=color)


def star_badge(img, cx, cy, r, lines, points=12, fill=RED, ink=CREAM, rot=0.0):
    """Selo estrela (tipo 'NOVO MENU' da referencia)."""
    d = ImageDraw.Draw(img, "RGBA")
    pts = []
    for i in range(points * 2):
        a = rot + i * math.pi / points
        rr = r if i % 2 == 0 else r * 0.80
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=CREAM + (255,))
    pts2 = [(cx + (p[0] - cx) * 0.93, cy + (p[1] - cy) * 0.93) for p in pts]
    d.polygon(pts2, fill=fill)
    fs = int(r * 0.34)
    f = font(F_MARK, fs)
    tot = len(lines) * fs * 1.02
    y = cy - tot / 2
    for l in lines:
        d.text((cx - d.textlength(l, font=f) / 2, y - f.getbbox("H")[1] * 0.6), l,
               font=f, fill=ink)
        y += fs * 1.02


def wordmark(img, x, y, size, blob=True):
    """GREGO'S bubbly: letras creme com contorno vermelho sobre blob vermelho."""
    d = ImageDraw.Draw(img, "RGBA")
    f = font(F_MARK, size)
    t = "GREGO'S"
    tw_ = d.textlength(t, font=f)
    if blob:
        pad_x, pad_y = size * 0.36, size * 0.24
        d.rounded_rectangle([x - pad_x - 7, y - pad_y - 7, x + tw_ + pad_x + 7, y + size * 1.06 + pad_y + 7],
                            radius=int(size * 0.72), fill=CREAM)
        d.rounded_rectangle([x - pad_x, y - pad_y, x + tw_ + pad_x, y + size * 1.06 + pad_y],
                            radius=int(size * 0.66), fill=RED)
        d.text((x, y), t, font=f, fill=CREAM, stroke_width=max(2, int(size * 0.045)),
               stroke_fill=RED_DK)
    else:
        d.text((x, y), t, font=f, fill=CREAM)
    return tw_


def footer(img, cta=True):
    """Rodape: faixa xadrez + wordmark + CTA/praças."""
    d = ImageDraw.Draw(img, "RGBA")
    bar = 150
    y0 = H - bar
    d.rectangle([0, y0, W, H], fill=WINE_LO)
    checker(d, H - 34, h=34, cell=45)
    f1 = font(F_UI, 27)
    f2 = font(F_UIM, 20)
    tracked(d, (M, y0 + 30), "PEÇA PELO LINK DA BIO", f1, CREAM, tk=1.3)
    tracked(d, (M, y0 + 68), "CAMPO LIMPO PAULISTA · VÁRZEA PAULISTA · JUNDIAÍ",
            f2, (246, 240, 225, 205), tk=0.8)
    fm = font(F_MARK, 46)
    d.text((W - M - d.textlength("GREGO'S", font=fm), y0 + 28), "GREGO'S", font=fm, fill=CREAM)


def topmark(img):
    wordmark(img, M + 6, M - 6, 46, blob=True)


# --------------------------------------------------------------- layouts
def L_cartaz(c):
    """Vinho + headline creme no topo + painel de foto — igual a referencia."""
    img = wine_bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    fh, hl, hs, ha, hh = fit(d, c["head"], F_HEAD, W - 2 * M - 40, 300, 118, 60)
    ytop = 150
    put_lines(d, 0, ytop, hl, fh, CREAM, ha, center=W / 2)

    fs = font(F_SUB, 34)
    sl = wrap(d, c["sub"], fs, W - 2 * M - 250)
    ysub = ytop + hh + 30
    for l in sl:
        d.text((W / 2 - d.textlength(l, font=fs) / 2, ysub), l, font=fs, fill=(246, 240, 225, 215))
        ysub += 42

    ptop = int(ysub + 40)
    pbot = H - 150 - 44
    ph = cover(FOTOS + c["foto"], W - 2 * M, pbot - ptop, *c.get("focus", (0.5, 0.5)), zoom=c.get("zoom", 1.0))
    round_panel(img, ph, (M, ptop, W - M, pbot), radius=48, ring=9)

    star_badge(img, W - M - 34, ptop - 6, 104, c["badge"], rot=0.2)
    footer(img)
    return img.convert("RGB")


def L_full(c):
    """Foto sangrando + veu vinho + headline creme na base."""
    img = cover(FOTOS + c["foto"], W, H, *c.get("focus", (0.5, 0.42)), zoom=c.get("zoom", 1.0)).convert("RGBA")
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = Image.new("L", (1, H))
    gp = g.load()
    for y in range(H):
        t = y / (H - 1)
        a = 235 * (max(0.0, t - 0.24) / 0.76) ** 1.3 + 120 * max(0.0, 1 - t / 0.30)
        gp[0, y] = int(min(252, a))
    top.putalpha(g.resize((W, H)))
    top.paste(Image.new("RGB", (W, H), WINE_LO), (0, 0), top.split()[3])
    img.alpha_composite(top)
    d = ImageDraw.Draw(img, "RGBA")
    if c.get("mark", True):
        topmark(img)

    base = H - 150 - 54
    fs = font(F_SUB, 36)
    sl = wrap(d, c["sub"], fs, W - 2 * M - 30)
    sh = len(sl) * 44
    fh, hl, hs, ha, hh = fit(d, c["head"], F_HEAD, W - 2 * M, 380, 116, 58)
    y = base - sh - 26 - hh
    y = put_lines(d, M, y, hl, fh, CREAM, ha) + 26
    d.rounded_rectangle([M, y - 4, M + 104, y + 6], radius=5, fill=RED)
    for l in sl:
        d.text((M, y + 24), l, font=fs, fill=(246, 240, 225, 232))
        y += 44
    star_badge(img, W - M - 26, 208, 100, c["badge"], rot=0.18)
    footer(img)
    return img.convert("RGB")


def L_split(c):
    """Painel de foto no topo + bloco vinho com headline."""
    img = wine_bg().convert("RGBA")
    ph_h = 716
    ph = cover(FOTOS + c["foto"], W, ph_h, *c.get("focus", (0.5, 0.5)), zoom=c.get("zoom", 1.0))
    img.paste(ph, (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    checker(d, ph_h - 30, h=30, cell=45, offset=1)
    if c.get("mark", True):
        topmark(img)

    fs = font(F_SUB, 36)
    sl = wrap(d, c["sub"], fs, W - 2 * M)
    top, bot = ph_h + 46, H - 150 - 40
    room = (bot - top) - len(sl) * 44 - 46
    fh, hl, hs, ha, hh = fit(d, c["head"], F_HEAD, W - 2 * M, room, 116, 56)
    total = hh + 22 + 24 + len(sl) * 44
    y = top + max(0, ((bot - top) - total) / 2)
    y = put_lines(d, M, y, hl, fh, CREAM, ha) + 22
    d.rounded_rectangle([M, y - 4, M + 104, y + 6], radius=5, fill=RED)
    for l in sl:
        d.text((M, y + 24), l, font=fs, fill=(246, 240, 225, 225))
        y += 44
    star_badge(img, W - M - 30, ph_h - 74, 100, c["badge"], rot=0.18)
    footer(img)
    return img.convert("RGB")


LAY = {"cartaz": L_cartaz, "full": L_full, "split": L_split}

PECAS = [
    dict(n="01_grego_classico", lay="cartaz", foto="037_sirio.jpg", focus=(0.40, 0.52), zoom=1.45,
         badge=["O", "CLÁSSICO"], head="O GREGO DA CASA",
         sub="Carne no espeto, vinagrete e queijo maçaricado no pão crocante."),
    dict(n="02_gregao_queijo", lay="split", foto="foto gregos 16.jpg", focus=(0.46, 0.54), zoom=1.15,
         badge=["O", "GREGÃO"], head="QUEIJO ATÉ A BORDA",
         sub="O maior da casa, maçaricado de ponta a ponta."),
    dict(n="03_macarico", lay="full", foto="foto gregos 06.jpg", focus=(0.50, 0.44),
         badge=["FEITO", "NA HORA"], head="MAÇARICADO NA SUA FRENTE",
         sub="O queijo derrete na hora do pedido. Sem atalho, sem vitrine."),
    dict(n="04_espeto", lay="split", foto="foto gregos 04.jpg", focus=(0.56, 0.48),
         badge=["BASTI-", "DORES"], head="CORTADO DIRETO DO ESPETO",
         sub="Churrasco grego de verdade, fatiado só quando você pede."),
    dict(n="05_combo", lay="cartaz", foto="039_sirio.jpg", focus=(0.50, 0.50), zoom=1.28,
         badge=["COMBO", "COMPLETO"], head="O COMBO QUE RESOLVE",
         sub="Grego + batata + bebida. Fome resolvida sem pensar muito."),
    dict(n="06_mesa_farta", lay="cartaz", foto="059_mesa-completa-frontal.jpg", focus=(0.50, 0.44), zoom=1.12,
         badge=["PRA", "GALERA"], head="PEDIU, CHEGOU",
         sub="Mesa farta pra dividir com todo mundo. Ou não dividir nada."),
    dict(n="07_primeira_mordida", lay="full", foto="108_modelo-sirio.jpg", focus=(0.50, 0.28),
         badge=["EXPERI-", "MENTA"], head="A PRIMEIRA MORDIDA EXPLICA",
         sub="Difícil de descrever. Muito fácil de repetir."),
    dict(n="08_toda_noite_enche", lay="split", foto="foto gregos 18.jpg", focus=(0.47, 0.62), mark=False,
         badge=["CAMPO", "LIMPO"], head="TODA NOITE ENCHE",
         sub="E não é por acaso. Vem entender o motivo pessoalmente."),
    dict(n="09_nossa_casa", lay="split", foto="foto gregos 09.jpg", focus=(0.50, 0.50),
         badge=["NOSSA", "CASA"], head="LUGAR PRA SENTAR E COMER BEM",
         sub="Salão novo, climatizado e com espaço pra família inteira."),
    dict(n="10_montagem", lay="cartaz", foto="foto gregos 05.jpg", focus=(0.44, 0.52), zoom=1.20,
         badge=["MON-", "TAGEM"], head="VINAGRETE POR CIMA, CARNE POR DENTRO",
         sub="A montagem que fez a fama do Grego's na região."),
]

if __name__ == "__main__":
    for p in PECAS:
        img = LAY[p["lay"]](p)
        path = f"{OUT}GREGOS_{p['n']}.jpg"
        img.save(path, quality=93, subsampling=0, optimize=True)
        print(path, os.path.getsize(path) // 1024, "KB")
