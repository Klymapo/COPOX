"""Test localized frontal skin normal repair without moving facial geometry.

This is a shading candidate, not a substitute for closing structural holes.
Used only on the measured G2-C8 face region; eye/brow atlas is untouched.
"""
from pathlib import Path
import copy
import hashlib
import json
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render
from reparar_v03 import add_accessor, write_glb

BASE = Path('build/g2c8/maniqui_G2C8_COLOR_UNIFORME_SIN_APROBAR.glb')
BASE_SHA = 'bf4ec71a56e94c61c3933c7194ec44026b6e8c31648175f4c497ba167c139e50'
OUT = Path('build/g2c9/maniqui_G2C9_NORMALES_ROSTRO_SIN_APROBAR.glb')
REPORT = Path('docs/maniqui/g2c9/NORMALES.json')


def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
    if OUT.exists():
        raise FileExistsError(OUT)
    source, binary = render.load(BASE)
    primitive = source['meshes'][0]['primitives'][0]
    position = render.acc(source, binary, primitive['attributes']['POSITION'])
    normal = render.acc(source, binary, primitive['attributes']['NORMAL'])
    face = render.acc(source, binary, primitive['indices']).astype(int).reshape(-1, 3)
    used = np.zeros(len(position), dtype=bool)
    used[np.unique(face)] = True
    # Measured glabella and lower orbital/upper cheek bounds of this model.
    x, y, z = position.T
    region = used & (z > .165) & (
        ((abs(x) < .04) & (y > .705) & (y < .775)) |
        ((abs(x) > .025) & (abs(x) < .155) & (y > .59) & (y < .668)))
    donor = np.flatnonzero(region & (normal[:, 2] > .65))
    suspect = np.flatnonzero(region & (normal[:, 2] < .5))
    tree = cKDTree(position[donor])
    amended = normal.copy()
    changed = []
    for index in suspect:
        near = tree.query_ball_point(position[index], .018)
        if len(near) < 3:
            continue
        peer = donor[near]
        distance = np.linalg.norm(position[peer] - position[index], axis=1)
        weights = 1 / (distance + .001) ** 2
        vector = np.average(normal[peer], axis=0, weights=weights)
        vector /= np.linalg.norm(vector)
        if vector[2] < .55:
            continue
        amended[index] = vector
        changed.append(int(index))
    assert 20 < len(changed) < 150
    result = copy.deepcopy(source)
    raw = bytearray(binary)
    old_accessor = source['accessors'][primitive['attributes']['NORMAL']]
    result['meshes'][0]['primitives'][0]['attributes']['NORMAL'] = add_accessor(
        result, raw, amended.astype(np.float32), old_accessor['componentType'],
        old_accessor['type'], 34962)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_glb(OUT, result, raw)
    exported, exported_binary = render.load(OUT)
    assert exported_binary[:len(binary)] == binary
    for key in ('nodes', 'skins', 'animations', 'materials', 'images', 'textures', 'scenes'):
        assert exported.get(key) == source.get(key), key
    for index, other in enumerate(source['meshes'][0]['primitives']):
        if index != 0:
            assert exported['meshes'][0]['primitives'][index] == other
    assert len(exported['skins'][0]['joints']) == 56 and len(exported['animations']) == 29
    report = {'source': str(BASE), 'source_sha256': BASE_SHA,
              'glb': str(OUT), 'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
              'changed_normal_vertex_ids': changed, 'changed_normal_count': len(changed),
              'moved_vertices': 0, 'triangles_added_or_deleted': 0,
              'skin_weights_and_face_atlas_unchanged': True,
              'status': 'PENDING_VISUAL', 'production_approved': False,
              'scope_limit': 'Shading only; structural holes and fold geometry remain.'}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(report['sha256'], len(changed))


if __name__ == '__main__':
    main()
