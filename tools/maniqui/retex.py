"""Reescala las texturas embebidas de un GLB y lo reempaca. Uso: retex.py in.glb out.glb SIZE"""
import json, struct, sys, io
from PIL import Image

src, dst, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
b = open(src, 'rb').read()
L = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20 + L])
binc = b[28 + L:]
img_views = {im['bufferView'] for im in j.get('images', [])}
mats = j['materials'][0]
color_tex = mats['pbrMetallicRoughness']['baseColorTexture']['index']
color_view = j['images'][j['textures'][color_tex]['source']]['bufferView']

out = bytearray(); new_views = []
for i, bv in enumerate(j['bufferViews']):
    o = bv.get('byteOffset', 0); data = binc[o:o + bv['byteLength']]
    if i in img_views:
        im = Image.open(io.BytesIO(data)).convert('RGB').resize((size, size), Image.LANCZOS)
        buf = io.BytesIO()
        if i == color_view:
            im.save(buf, 'JPEG', quality=90); mime = 'image/jpeg'
        else:
            im.save(buf, 'PNG', optimize=True); mime = 'image/png'
        data = buf.getvalue()
        for img in j['images']:
            if img['bufferView'] == i: img['mimeType'] = mime
    while len(out) % 4: out.append(0)
    nb = dict(bv); nb['byteOffset'] = len(out); nb['byteLength'] = len(data); nb['buffer'] = 0
    out += data; new_views.append(nb)
while len(out) % 4: out.append(0)
j['bufferViews'] = new_views; j['buffers'] = [{'byteLength': len(out)}]
js = json.dumps(j, separators=(',', ':')).encode()
js += b' ' * ((4 - len(js) % 4) % 4)
total = 12 + 8 + len(js) + 8 + len(out)
with open(dst, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, total))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
    f.write(struct.pack('<II', len(out), 0x004E4942)); f.write(out)
print(dst, round(total / 1e6, 2), 'MB')
