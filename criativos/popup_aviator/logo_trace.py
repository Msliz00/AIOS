# Extrai o lettering "Aviator" da imagem de referência do logo e gera máscaras em alta resolução
# (logo_aviator_fill.png = letras, logo_aviator_outline.png = contorno engrossado).
# uso: python3 logo_trace.py <imagem_do_logo.png>
import sys
import numpy as np
from PIL import Image, ImageFilter

src = Image.open(sys.argv[1]).convert('RGB')
a = np.asarray(src).astype(float)
red = np.clip((a[..., 0] - np.maximum(a[..., 1], a[..., 2])) / 150.0, 0, 1)
ys, xs = np.where(red > 0.4)
# o lettering é o bloco de baixo: separa pelo maior intervalo vertical sem vermelho
rows = np.where((red > 0.4).sum(1) > 0)[0]
gaps = np.diff(rows); cut = rows[np.argmax(gaps) + 1] if gaps.max() > 3 else rows[0]
sel = ys >= cut
x0, x1, y0, y1 = xs[sel].min(), xs[sel].max(), ys[sel].min(), ys[sel].max()
pad = 6
crop = Image.fromarray((red * 255).astype('uint8')).crop((x0 - pad, y0 - pad, x1 + pad + 1, y1 + pad + 1))
S = 6  # ampliação
big = crop.resize((crop.width * S, crop.height * S), Image.BICUBIC).filter(ImageFilter.GaussianBlur(S * 0.55))
def thr(img, t, soft=10):
    v = np.asarray(img).astype(float)
    return Image.fromarray((np.clip((v - t) / soft + 0.5, 0, 1) * 255).astype('uint8'))
fill = thr(big, 128)
M = 60  # margem para o contorno
canvas = Image.new('L', (fill.width + 2 * M, fill.height + 2 * M), 0); canvas.paste(fill, (M, M))
out = thr(canvas.filter(ImageFilter.GaussianBlur(20)), 20, 8)
for name, m in (('fill', canvas), ('outline', out)):
    im = Image.new('RGBA', canvas.size, (255, 255, 255, 0)); im.putalpha(m); im.save(f'logo_aviator_{name}.png')
print(canvas.size)
