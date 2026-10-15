"""Close only measured, collision-free cheek gaps of the G2-C8 GLB.

The large eye, nose and jaw contours remain untouched. Candidate face loops
are identified and validated against the pinned baseline before editing.
"""
from pathlib import Path
import copy
import hashlib
import json
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render
from g2c5_fill_holes import boundary_cycles
from g2c4_candidates import topology
from g2c4_intersections import intersections
from reparar_v03 import add_accessor, write_glb

BASE = Path('build/g2c8/maniqui_G2C8_COLOR_UNIFORME_SIN_APROBAR.glb')
BASE_SHA = 'bf4ec71a56e94c61c3933c7194ec44026b6e8c31648175f4c497ba167c139e50'
OUT = Path('build/g2c9/maniqui_G2C9_HUECOS_MEJILLAS_SIN_APROBAR.glb')
REPORT = Path('docs/maniqui/g2c9/HUECOS.json')
# Measured boundary cycles from this pinned GLB; loop 20 is excluded because
# its adjacent winding points inward. Eye, nose, mouth and scalp are protected.
SELECTED = {32: (-0.119, 0.616, 0.186),
            33: (-0.115, 0.611, 0.188)}


def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
    if OUT.exists():
        raise FileExistsError(OUT)
    source, binary = render.load(BASE)
    primitive = source['meshes'][0]['primitives'][0]
    positions = render.acc(source, binary, primitive['attributes']['POSITION'])
    old = render.acc(source, binary, primitive['indices']).astype(np.uint32).reshape(-1, 3)
    loops, failures = boundary_cycles(positions, old)
    assert len(loops) == 44 and not failures
    patches = []
    for number, expected in SELECTED.items():
        loop = loops[number]
        center = positions[loop].mean(axis=0)
        assert np.linalg.norm(center - expected) < .0015, (number, center)
        assert len(loop) in (3, 4)
        if len(loop) == 3:
            faces = [loop[::-1]]
        else:
            # Both diagonals are tested; this one has larger minimum 3D area.
            faces = [[loop[1], loop[0], loop[2]], [loop[2], loop[0], loop[3]]]
        patches.extend(faces)
    patches = np.array(patches, dtype=np.uint32)
    all_triangles = np.concatenate([g[0] for g in render.gather(BASE) if len(g[0])])
    changed = range(len(all_triangles), len(all_triangles) + len(patches))
    crossings, coplanar = intersections(np.concatenate([all_triangles, positions[patches]]), changed)
    assert not crossings and not coplanar
    before = topology(positions, old)
    after = topology(positions, np.vstack([old, patches]))
    assert not after['degenerate_faces']
    assert after['welded_nonmanifold_edges'] <= before['welded_nonmanifold_edges']
    assert after['welded_boundary_edges'] < before['welded_boundary_edges']
    result = copy.deepcopy(source)
    raw = bytearray(binary)
    result['meshes'][0]['primitives'][0]['indices'] = add_accessor(
        result, raw, np.vstack([old, patches]).reshape(-1), 5125, 'SCALAR', 34963)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_glb(OUT, result, raw)
    exported, exported_binary = render.load(OUT)
    assert exported_binary[:len(binary)] == binary
    for key in ('nodes', 'skins', 'animations', 'materials', 'images', 'textures', 'scenes'):
        assert exported.get(key) == source.get(key), key
    assert exported['meshes'][0]['primitives'][1:] == source['meshes'][0]['primitives'][1:]
    assert len(exported['skins'][0]['joints']) == 56 and len(exported['animations']) == 29
    report = {'source': str(BASE), 'source_sha256': BASE_SHA,
              'glb': str(OUT), 'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
              'selected_boundary_loops': list(SELECTED),
              'added_triangles': patches.tolist(), 'added_triangle_count': len(patches),
              'modified_vertices': 0, 'modified_weights': 0,
              'before': before, 'after': after, 'new_proper_crossings': 0,
              'coplanar_overlap_candidates': 0,
              'status': 'PENDING_VISUAL', 'production_approved': False,
              'scope_limit': 'Three small cheek gaps only; large eye, nose and jaw gaps remain.'}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(report['sha256'], before['welded_boundary_edges'], after['welded_boundary_edges'])


if __name__ == '__main__':
    main()
