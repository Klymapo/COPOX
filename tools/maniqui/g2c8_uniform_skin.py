"""Apply the measured V2 skin material to the untextured body surfaces.

The original eye and brow atlas surface stays intact. This operation changes
only material references; every vertex, joint weight, morph and clip is exact.
"""
from pathlib import Path
import copy
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render
from reparar_v03 import write_glb

BASE = Path('build/g2c7/maniqui_G2C7_V2_RASGOS_SELECTIVOS_SIN_APROBAR.glb')
BASE_SHA = '0efe44e912a23c2dfae2be850494d7e8a93475606af5e08ba49e69e536daed63'
OUT = Path('build/g2c8/maniqui_G2C8_COLOR_UNIFORME_SIN_APROBAR.glb')
REPORT = Path('docs/maniqui/g2c8/COLOR.json')


def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
    if OUT.exists():
        raise FileExistsError(OUT)
    source, binary = render.load(BASE)
    candidate = copy.deepcopy(source)
    primitives = candidate['meshes'][0]['primitives']
    skin_material = primitives[0]['material']
    assert primitives[1]['material'] == primitives[2]['material'] == skin_material
    assert primitives[24]['material'] != skin_material  # protected eyes and brows
    changed = []
    for index in range(3, 24):
        assert primitives[index]['material'] == 24
        primitives[index]['material'] = skin_material
        changed.append(index)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_glb(OUT, candidate, bytearray(binary))
    exported, exported_binary = render.load(OUT)
    assert exported_binary == binary
    for key in ('nodes', 'skins', 'animations', 'accessors', 'bufferViews',
                'materials', 'images', 'textures', 'scenes'):
        assert exported.get(key) == source.get(key), key
    assert len(exported['skins'][0]['joints']) == 56
    assert len(exported['animations']) == 29
    assert exported['meshes'][0]['primitives'][24] == source['meshes'][0]['primitives'][24]
    report = {
        'source': str(BASE), 'source_sha256': BASE_SHA, 'glb': str(OUT),
        'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
        'skin_material': skin_material,
        'base_color': source['materials'][skin_material]['pbrMetallicRoughness']['baseColorFactor'],
        'changed_primitive_materials': changed,
        'changed_triangles': 0, 'changed_vertices': 0,
        'binary_geometry_animation_data_exact': True,
        'eyes_and_brows_primitive_exact': True,
        'status': 'PENDING_VISUAL', 'production_approved': False,
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
