# Junta os quadros de frames_<versão>/ em WebP animado com transparência (loop infinito, 100 ms por quadro).
# uso: python3 montar_animacao.py v7
import glob, sys
from PIL import Image
v = sys.argv[1] if len(sys.argv) > 1 else 'v6'
fr = [Image.open(f).convert('RGBA') for f in sorted(glob.glob(f'frames_{v}/f*.png'))]
fr[0].save(f'popup_aviator_{v}.webp', save_all=True, append_images=fr[1:], duration=100, loop=0, quality=88, method=6)
print(len(fr), 'quadros')
