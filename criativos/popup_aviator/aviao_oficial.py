# Extrai o avião oficial do logo Aviator (imagem de referência) e gera uma versão em relevo 3D:
# volume arredondado, luz/sombra, brilho especular e espessura lateral.  Saída: aviao_oficial.png
# uso: python3 aviao_oficial.py <imagem_do_logo.png>
import sys
import numpy as np
from PIL import Image, ImageFilter

src = Image.open(sys.argv[1]).convert('RGB')
a = np.asarray(src).astype(float)
red = np.clip((a[..., 0] - np.maximum(a[..., 1], a[..., 2])) / 150.0, 0, 1)
on = (red > 0.45)
rows = np.where(on.sum(1) > 0)[0]
# primeiro bloco contínuo de linhas com vermelho = avião (o resto é o degradê/lettering de baixo)
brk = np.where(np.diff(rows) > 5)[0]
r1 = rows[brk[0]] if len(brk) else rows[-1]
r0 = rows[0]
cols = np.where(on[r0:r1 + 1].sum(0) > 0)[0]
pad = 8
crop = Image.fromarray((red * 255).astype('uint8')).crop((cols[0] - pad, r0 - pad, cols[-1] + pad + 1, r1 + pad + 1))
S = 6
big = crop.resize((crop.width * S, crop.height * S), Image.BICUBIC).filter(ImageFilter.GaussianBlur(S * 0.5))
m = np.clip((np.asarray(big).astype(float) - 72) / 14 + 0.5, 0, 1)
M = 80
m = np.pad(m, M)
H, W = m.shape
def _box(x, r, ax):
    r = max(1, int(round(r)))
    p = np.pad(x, [(r + 1, r) if i == ax else (0, 0) for i in range(2)], mode='edge')
    c = np.cumsum(p, axis=ax)
    n = x.shape[ax]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax); lo = np.take(c, np.arange(0, n), axis=ax)
    return (hi - lo) / (2 * r + 1)
def blur(x, r):   # gaussiana aproximada (3 passadas de box) em ponto flutuante, sem degraus
    x = x.astype(float)
    for _ in range(3):
        x = _box(_box(x, r * 0.58, 0), r * 0.58, 1)
    return x

# mapa de altura "inflado" -> normais
h = (0.5 * blur(m, 5) + 0.3 * blur(m, 12) + 0.2 * blur(m, 26)) * m
h = blur(h, 2.5)
gy, gx = np.gradient(h * 46.0)
n = np.dstack([-gx, -gy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
def lit(L): L = np.array(L, float); L /= np.linalg.norm(L); return np.clip((n * L).sum(2), 0, 1), L
dif, L = lit([-0.45, -0.75, 0.6])
hv = L + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
spec = np.clip((n * hv).sum(2), 0, 1) ** 38
rim, _ = lit([0.7, 0.55, 0.25])                      # contraluz quente vindo de baixo/direita
yy = np.linspace(0, 1, H)[:, None]
base = np.array([232, 46, 30.]) * (1 - yy[..., None] * 0.28)
col = base * (0.5 + 0.8 * dif[..., None]) + np.array([255, 235, 220.]) * spec[..., None] * 0.95 + np.array([255, 120, 60.]) * (rim[..., None] ** 3) * 0.35
col = np.clip(col, 0, 255)

# espessura lateral (extrusão para baixo/direita)
D = 16
out = np.zeros((H, W, 4))
for k in range(D, 0, -1):
    sh = np.roll(np.roll(m, int(k * 0.55), axis=1), k, axis=0)
    c = np.array([120, 14, 8.]) * (0.55 + 0.45 * (1 - k / D))
    out[..., :3] = out[..., :3] * (1 - sh[..., None]) + c * sh[..., None]
    out[..., 3] = np.maximum(out[..., 3], sh)
out[..., :3] = out[..., :3] * (1 - m[..., None]) + col * m[..., None]
out[..., 3] = np.maximum(out[..., 3], m)
out[..., 3] *= 255
Image.fromarray(out.astype('uint8'), 'RGBA').save('aviao_oficial.png')
print(W, H)
