# Junta os quadros de frames_v6/ em animações com transparência (loop infinito, 100 ms por quadro).
import glob
from PIL import Image
fr = [Image.open(f).convert('RGBA') for f in sorted(glob.glob('frames_v6/f*.png'))]
fr[0].save('popup_aviator_v6.webp', save_all=True, append_images=fr[1:], duration=100, loop=0, quality=88, method=6)
print(len(fr), 'quadros')
