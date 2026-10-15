"""Acercamiento de cabeza: 4 vistas (0, 45, 90, 180) con bounds de y > y_min. Uso: headzoom.py in.glb out.png [y_min]"""
import sys, numpy as np
sys.path.insert(0, '.')
import render
from PIL import Image
src, out = sys.argv[1], sys.argv[2]; ymin = float(sys.argv[3]) if len(sys.argv) > 3 else 0.50
tris = render.gather(src)
tris = [(t[0][t[0][:, :, 1].min(1) > ymin - 0.05],) + t[1:] for t in tris]; tris = [t for t in tris if len(t[0])]
b = (np.array([-0.35, ymin, -0.35]), np.array([0.35, ymin + 0.70, 0.35]))
sheet = Image.new('RGB', (500 * 4, 500), 'white')
for i, y in enumerate((0, 45, 90, 180)): sheet.paste(render.render(tris, y, W=500, H=500, bounds=b), (500 * i, 0))
sheet.save(out); print(out)
