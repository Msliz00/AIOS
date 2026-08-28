#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GREGO'S — feed Instagram 1080x1350 (versao humanizada).

Mesma identidade da peca de referencia (vinho, creme, blob vermelho,
selo estrela, xadrez), mas com o grid quebrado de proposito: adesivos
tortos, traco de marcador feito a mao, recado manuscrito e foto colada
levemente torta. Duas pecas trocam o modelo de estudio por cliente real.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

S = "/tmp/claude-0/-home-user-AIOS/6f054a58-1907-5469-9055-58632a643f99/scratchpad"
FOTOS, FONTS, OUT = S + "/fotos/", S + "/fonts/", S + "/artes3/"
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350
M = 72

WINE_HI = (138, 21, 35)
WINE_LO = (86, 12, 22)
RED     = (232, 35, 42)
RED_DK  = (176, 20, 28)
CREAM   = (246, 240, 225)

F_HEAD = FONTS + "Nunito900.ttf"
F_MARK = FONTS + "Chewy.ttf"
F_SUB  = FONTS + "Baloo700.ttf"
F_HAND = FONTS + "Caveat700.ttf"     # recado manuscrito
F_UI   = FONTS + "Inter700.ttf"
F_UIM  = FONTS + "Inter500.ttf"


# ------------------------------------------------------------------ texto
def font(p, s):
    return ImageFont.truetype(p, s)


def tw(d, t, f, tk=0):
    return d.textlength(t, font=f) + tk * max(len(t) - 1, 0)


def tracked(d, xy, t, f, fill, tk=0, right=False):
    x, y = xy
    if right:
        x -= tw(d, t, f, tk)
    for ch in t:
        d.text((x, y), ch, font=f, fill=fill)
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


def adv_of(f, lines, size, extra=0.16):
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


def put_lines(d, x, ytop, lines, f, fill, adv, center=None):
    ct = f.getbbox("H")[1]
    y = ytop
    for l in lines:
        px = x if center is None else center - d.textlength(l, font=f) / 2
        d.text((px, y - ct), l, font=f, fill=fill)
        y += adv
    return y - adv + (f.getbbox("H")[3] - ct)


# ------------------------------------------------------------ mao / textura
def paste_rot(base, layer, center, angle):
    """Cola uma camada girada — e o que tira o ar de template."""
    rl = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(rl, (int(center[0] - rl.width / 2),
                              int(center[1] - rl.height / 2)))


def rough_line(d, x0, y0, x1, color=RED, weight=11, rng=None):
    """Traco de marcador: varias passadas com tremido, nao uma barra reta."""
    rng = rng or random.Random(7)
    span = x1 - x0
    for p in range(3):
        pts = []
        n = 16
        for i in range(n + 1):
            t = i / n
            x = x0 + span * t
            y = y0 + math.sin(t * 3.1 + p) * 1.9 + rng.uniform(-1.6, 1.6) + p * 0.9
            pts.append((x, y))
        d.line(pts, fill=color, width=max(3, weight - p * 3), joint="curve")
    # ponta que escapa, como caneta de verdade
    d.line([(x1, y0 + 2), (x1 + span * 0.05, y0 - 2)], fill=color, width=4)


def hand_note(base, x, y, text, size=52, color=CREAM, angle=-3.0, anchor="left"):
    """Recado manuscrito — como se alguem tivesse escrito na arte."""
    f = font(F_HAND, size)
    tmp = Image.new("RGBA", (1, 1))
    wpx = int(ImageDraw.Draw(tmp).textlength(text, font=f)) + 40
    lay = Image.new("RGBA", (wpx, int(size * 1.9)), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((20, size * 0.25), text, font=f, fill=color)
    cx = x + wpx / 2 if anchor == "left" else x - wpx / 2
    paste_rot(base, lay, (cx, y + size * 0.9), angle)
    return wpx


def sticker_star(base, cx, cy, r, lines, angle=-9.0, fill=RED, ink=CREAM):
    """Selo estrela colado torto, como adesivo."""
    pad = int(r * 1.5)
    lay = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pts, pts_in = [], []
    for i in range(24):
        a = i * math.pi / 12
        rr = r if i % 2 == 0 else r * 0.79
        pts.append((pad + rr * math.cos(a), pad + rr * math.sin(a)))
    d.polygon(pts, fill=CREAM + (255,))
    for p in pts:
        pts_in.append((pad + (p[0] - pad) * 0.92, pad + (p[1] - pad) * 0.92))
    d.polygon(pts_in, fill=fill)
    fs = int(r * 0.35)
    f = font(F_MARK, fs)
    y = pad - len(lines) * fs * 1.02 / 2
    for l in lines:
        d.text((pad - d.textlength(l, font=f) / 2, y - f.getbbox("H")[1] * 0.62),
               l, font=f, fill=ink)
        y += fs * 1.02
    paste_rot(base, lay, (cx, cy), angle)


def tape(base, cx, cy, w=132, h=38, angle=-24.0):
    """Fita adesiva translucida segurando a foto no lugar."""
    lay = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle([4, 4, w + 3, h + 3], fill=(252, 248, 236, 128))
    d.line([(4, 4), (w + 3, 4)], fill=(255, 255, 255, 150), width=2)
    d.line([(4, h + 3), (w + 3, h + 3)], fill=(120, 90, 70, 60), width=2)
    paste_rot(base, lay.filter(ImageFilter.GaussianBlur(0.5)), (cx, cy), angle)


# -------------------------------------------------------------- graficos
def wine_bg():
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
    l, t = int((nw - bw) * fx), int((nh - bh) * fy)
    im = im.crop((l, t, l + bw, t + bh))
    im = ImageEnhance.Color(im).enhance(1.16)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))


def photo_card(base, photo, center, angle=-1.6, radius=34, border=16):
    """Foto colada meio torta, com borda creme — cara de foto impressa."""
    pw, ph = photo.size
    lay = Image.new("RGBA", (pw + border * 2, ph + border * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, lay.width - 1, lay.height - 1],
                        radius=radius + border, fill=CREAM + (255,))
    m = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=radius, fill=255)
    lay.paste(photo, (border, border), m)
    paste_rot(base, lay, center, angle)


def checker(d, y, h=30, cell=45, color=CREAM, offset=0):
    for i in range(W // cell + 2):
        if (i + offset) % 2 == 0:
            d.rectangle([i * cell, y, i * cell + cell, y + h], fill=color)


def wordmark_blob(base, x, y, size, angle=-2.5):
    """GREGO'S bubbly no blob vermelho, levemente torto."""
    f = font(F_MARK, size)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    wpx = tmp.textlength("GREGO'S", font=f)
    px, py = size * 0.36, size * 0.24
    lay = Image.new("RGBA", (int(wpx + px * 2 + 22), int(size * 1.06 + py * 2 + 22)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, lay.width - 1, lay.height - 1],
                        radius=int(size * 0.72), fill=CREAM)
    d.rounded_rectangle([11, 11, lay.width - 12, lay.height - 12],
                        radius=int(size * 0.66), fill=RED)
    d.text((11 + px, 11 + py), "GREGO'S", font=f, fill=CREAM,
           stroke_width=max(2, int(size * 0.045)), stroke_fill=RED_DK)
    paste_rot(base, lay, (x + lay.width / 2, y + lay.height / 2), angle)


def footer(base, offset=0):
    d = ImageDraw.Draw(base, "RGBA")
    y0 = H - 150
    d.rectangle([0, y0, W, H], fill=WINE_LO)
    checker(d, H - 30, h=30, cell=45, offset=offset)
    tracked(d, (M, y0 + 30), "PEÇA PELO LINK DA BIO", font(F_UI, 27), CREAM, tk=1.3)
    tracked(d, (M, y0 + 68), "CAMPO LIMPO PAULISTA · VÁRZEA PAULISTA · JUNDIAÍ",
            font(F_UIM, 20), (246, 240, 225, 205), tk=0.8)
    fm = font(F_MARK, 46)
    d.text((W - M - d.textlength("GREGO'S", font=fm), y0 + 26), "GREGO'S", font=fm, fill=CREAM)


# --------------------------------------------------------------- layouts
def L_cartaz(c):
    img = wine_bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(c["n"])

    fh, hl, hs, ha, hh = fit(d, c["head"], F_HEAD, W - 2 * M - 40, 290, 116, 60)
    ytop = 138
    put_lines(d, 0, ytop, hl, fh, CREAM, ha, center=W / 2)
    yb = ytop + hh

    # traco de marcador sob a headline
    lw = min(300, W * 0.34)
    rough_line(d, W / 2 - lw / 2, yb + 26, W / 2 + lw / 2, rng=rng)

    hand_note(img, W / 2 - 260, yb + 44, c["hand"], size=54, angle=c.get("hand_rot", -2.6))

    ptop = int(yb + 150)
    pbot = H - 150 - 52
    ph = cover(FOTOS + c["foto"], W - 2 * M - 26, pbot - ptop - 14,
               *c.get("focus", (0.5, 0.5)), zoom=c.get("zoom", 1.0))
    photo_card(img, ph, (W / 2, (ptop + pbot) / 2), angle=c.get("tilt", -1.5))
    half_w = (W - 2 * M - 26) / 2 + 16
    ctr_y = (ptop + pbot) / 2
    half_h = (pbot - ptop - 14) / 2 + 16
    tape(img, W / 2 - half_w + 26, ctr_y - half_h + 12, angle=-38)
    tape(img, W / 2 + half_w - 26, ctr_y - half_h + 20, angle=34)

    sticker_star(img, W - M - 44, ptop + 22, 104, c["badge"], angle=c.get("badge_rot", -11))
    footer(img)
    return img.convert("RGB")


def L_split(c):
    img = wine_bg().convert("RGBA")
    rng = random.Random(c["n"])
    ph_h = 700
    img.paste(cover(FOTOS + c["foto"], W, ph_h, *c.get("focus", (0.5, 0.5)),
                    zoom=c.get("zoom", 1.0)).convert("RGBA"), (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    checker(d, ph_h - 30, h=30, cell=45, offset=1)
    if c.get("mark", True):
        wordmark_blob(img, M, M - 12, 46)

    fs = font(F_SUB, 35)
    sl = wrap(d, c["sub"], fs, W - 2 * M - 40)
    top, bot = ph_h + 52, H - 150 - 38
    room = (bot - top) - len(sl) * 43 - 96
    fh, hl, hs, ha, hh = fit(d, c["head"], F_HEAD, W - 2 * M, room, 114, 56)
    total = hh + 30 + 54 + len(sl) * 43
    y = top + max(0, ((bot - top) - total) / 2)
    y = put_lines(d, M, y, hl, fh, CREAM, ha)
    rough_line(d, M, y + 28, M + 232, rng=rng)
    y += 56
    for l in sl:
        d.text((M, y), l, font=fs, fill=(246, 240, 225, 228))
        y += 43
    hand_note(img, M - 10, ph_h - 122, c["hand"], size=52,
              angle=c.get("hand_rot", -4))
    sticker_star(img, W - M - 40, ph_h - 108, 100, c["badge"], angle=c.get("badge_rot", 9))
    footer(img, offset=1)
    return img.convert("RGB")


def L_full(c):
    img = cover(FOTOS + c["foto"], W, H, *c.get("focus", (0.5, 0.42)),
                zoom=c.get("zoom", 1.0)).convert("RGBA")
    rng = random.Random(c["n"])
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = Image.new("L", (1, H)); gp = g.load()
    for y in range(H):
        t = y / (H - 1)
        gp[0, y] = int(min(252, 236 * (max(0.0, t - 0.24) / 0.76) ** 1.3
                           + 120 * max(0.0, 1 - t / 0.30)))
    veil.putalpha(g.resize((W, H)))
    veil.paste(Image.new("RGB", (W, H), WINE_LO), (0, 0), veil.split()[3])
    img.alpha_composite(veil)
    d = ImageDraw.Draw(img, "RGBA")
    if c.get("mark", True):
        wordmark_blob(img, M, M - 12, 46)

    base = H - 150 - 56
    fs = font(F_SUB, 35)
    sl = wrap(d, c["sub"], fs, W - 2 * M - 30)
    fh, hl, hs, ha, hh = fit(d, c["head"], F_HEAD, W - 2 * M, 350, 114, 58)
    y = base - len(sl) * 43 - 56 - hh
    hand_note(img, M - 6, y - 92, c["hand"], size=52, angle=c.get("hand_rot", -4))
    y = put_lines(d, M, y, hl, fh, CREAM, ha)
    rough_line(d, M, y + 28, M + 232, rng=rng)
    y += 56
    for l in sl:
        d.text((M, y), l, font=fs, fill=(246, 240, 225, 234))
        y += 43
    sticker_star(img, W - M - 44, 268, 100, c["badge"], angle=c.get("badge_rot", -8))
    footer(img)
    return img.convert("RGB")


LAY = {"cartaz": L_cartaz, "split": L_split, "full": L_full}

PECAS = [
    dict(n="01_grego_de_sempre", lay="cartaz", foto="037_sirio.jpg",
         focus=(0.40, 0.52), zoom=1.45, tilt=-1.6, badge=["O", "CLÁSSICO"],
         head="O GREGO DE SEMPRE", hand="o que todo mundo pede",
         sub="Carne no espeto, vinagrete e queijo maçaricado no pão crocante."),

    dict(n="02_gregao_queijo", lay="split", foto="foto gregos 16.jpg",
         focus=(0.46, 0.54), zoom=1.15, badge=["O", "GREGÃO"],
         head="QUEIJO ATÉ A BORDA", hand="sem economia",
         sub="O maior da casa, maçaricado de ponta a ponta."),

    dict(n="03_macarico", lay="full", foto="foto gregos 06.jpg",
         focus=(0.50, 0.44), badge=["NA", "HORA"],
         head="A GENTE MAÇARICA NA SUA FRENTE", hand="dá pra ouvir o chiado",
         sub="O queijo derrete na hora do pedido. Sem vitrine, sem atalho."),

    dict(n="04_espeto", lay="split", foto="foto gregos 04.jpg",
         focus=(0.56, 0.48), badge=["BASTI-", "DORES"],
         head="CORTADO NA HORA, DO ESPETO", hand="nada parado esperando",
         sub="Churrasco grego de verdade, fatiado só quando você pede."),

    dict(n="05_combo", lay="cartaz", foto="039_sirio.jpg",
         focus=(0.50, 0.50), zoom=1.28, tilt=1.4, badge=["COMBO"],
         head="RESOLVE A NOITE INTEIRA", hand="grego + batata + gelada",
         sub="Um pedido só e ninguém passa fome."),

    dict(n="06_mesa_farta", lay="cartaz", foto="059_mesa-completa-frontal.jpg",
         focus=(0.50, 0.44), zoom=1.12, tilt=-1.2, badge=["PRA", "DIVIDIR"],
         head="PEDIU, CHEGOU", hand="chama a galera",
         sub="Mesa farta pra dividir com todo mundo. Ou não dividir nada."),

    dict(n="07_primeira_mordida", lay="full", foto="foto gregos 29.jpg",
         focus=(0.46, 0.16), zoom=1.02, badge=["EXPERI-", "MENTA"],
         head="A PRIMEIRA MORDIDA EXPLICA", hand="depois a gente conversa",
         sub="Difícil de descrever. Muito fácil de repetir."),

    dict(n="08_toda_noite_enche", lay="split", foto="foto gregos 18.jpg",
         focus=(0.47, 0.62), mark=False, badge=["CAMPO", "LIMPO"],
         head="TODA NOITE ENCHE", hand="e não é por acaso",
         sub="Passa aqui num sábado e me diz se tem mesa vazia."),

    dict(n="09_cabe_todo_mundo", lay="split", foto="foto gregos 13.jpg",
         focus=(0.50, 0.46), zoom=1.10, badge=["NOSSA", "CASA"],
         head="AQUI CABE TODO MUNDO", hand="traz a família inteira",
         sub="Salão novo, climatizado e com espaço pra sentar sem pressa."),

    dict(n="10_montagem", lay="cartaz", foto="foto gregos 05.jpg",
         focus=(0.44, 0.52), zoom=1.20, tilt=1.7, badge=["MON-", "TAGEM"],
         head="O SEGREDO TÁ NA MONTAGEM", hand="camada por camada",
         sub="Pão aberto, carne fatiada na hora e vinagrete por cima."),
]

if __name__ == "__main__":
    for p in PECAS:
        img = LAY[p["lay"]](p)
        path = f"{OUT}GREGOS_{p['n']}.jpg"
        img.save(path, quality=93, subsampling=0, optimize=True)
        print(path, os.path.getsize(path) // 1024, "KB")
