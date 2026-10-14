"""IoU de silueta en 4 vistas entre un candidato y Gamma (llevado al espacio de Beta). Uso: measure.py cand.glb gamma.glb beta.glb out_prefix"""
import sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import render

cand, gamma, beta, out = sys.argv[1:5]
def pts(path):
    t = render.gather(path); return t, np.concatenate([x[0].reshape(-1, 3) for x in t])
bt, B = pts(beta); bH = B[:, 1].max() - B[:, 1].min(); by0 = B[:, 1].min(); bc = ((B[:, 0].max() + B[:, 0].min()) / 2, (B[:, 2].max() + B[:, 2].min()) / 2)
gt, G = pts(gamma); gy0 = G[:, 1].min(); gH = G[:, 1].max() - gy0; s = bH / gH
gc = ((G[:, 0].max() + G[:, 0].min()) / 2, (G[:, 2].max() + G[:, 2].min()) / 2)
gt = [((t[0] - [gc[0], gy0, gc[1]]) * s + [bc[0], by0, bc[1]],) + t[1:] for t in gt]
ct, C = pts(cand)
allv = np.concatenate([C] + [t[0].reshape(-1, 3) for t in gt]); bounds = (allv.min(0), allv.max(0))
BG = np.array([0.93, 0.92, 0.90]) * 255
res = {}; sheet = Image.new('RGB', (420 * 4, 640 * 2), 'white')
for i, yaw in enumerate((0, 45, 90, 180)):
    a = np.asarray(render.render(ct, yaw, bounds=bounds)); b = np.asarray(render.render(gt, yaw, bounds=bounds))
    ma = np.abs(a - BG).sum(-1) > 12; mb = np.abs(b - BG).sum(-1) > 12
    iou = (ma & mb).sum() / (ma | mb).sum(); res[f'vista_{yaw}'] = round(float(iou), 4)
    diff = np.zeros(a.shape, np.uint8) + 235; diff[ma & mb] = (120, 120, 120); diff[ma & ~mb] = (220, 60, 60); diff[~ma & mb] = (60, 90, 220)
    sheet.paste(Image.fromarray(a), (420 * i, 0)); sheet.paste(Image.fromarray(diff), (420 * i, 640))
res['promedio'] = round(float(np.mean([v for k, v in res.items() if k.startswith('vista')])), 4)
sheet.save(out + '_iou.png'); json.dump(res, open(out + '_iou.json', 'w'))
print(json.dumps(res))
