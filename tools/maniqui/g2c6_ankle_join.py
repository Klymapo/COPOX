"""Measured, reversible ankle join on immutable V3 plus vetted B2 cleanup.

Moves only the existing lower rings of the two shin primitives into the
existing shoes. No face, scalp, arm, bone, material, or animation data changes.
The shoe overlap is a garment-style termination, not a welded skin surface.
"""
from pathlib import Path
import copy, hashlib, json, sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render
from reparar_v03 import add_accessor, write_glb
from g2c4_inspect import BASE, SHA

B2 = Path('build/g2c4/models/maniqui_G2C4_B2_SIN_APROBAR.glb')
B2_SHA = 'daf3737d0cb5b6469fa407ffab5dc761b2fc0e0acd9c69652cb283d41b4b05ec'
OUT = Path('build/g2c6/maniqui_G2C6_L1_UNIONES_TOBILLOS_SIN_APROBAR.glb')
REPORT = Path('docs/maniqui/g2c6/L1.json')

def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == SHA
    assert hashlib.sha256(B2.read_bytes()).hexdigest() == B2_SHA
    if OUT.exists():
        raise FileExistsError(OUT)
    j, binary = render.load(B2)
    d = copy.deepcopy(j)
    raw = bytearray(binary)
    changes = []
    for shin, shoe in ((4, 15), (5, 23)):
        sp = j['meshes'][0]['primitives'][shin]
        fp = j['meshes'][0]['primitives'][shoe]
        original = render.acc(j, binary, sp['attributes']['POSITION'])
        foot = render.acc(j, binary, fp['attributes']['POSITION'])
        levels = np.unique(original[:, 1])
        lower, next_level = levels[:2]
        ids = np.flatnonzero(np.isclose(original[:, 1], lower, atol=1e-8))
        assert len(ids) == 33 and next_level - lower > 0.03
        # The actual shoe crown and shin ring, measured per side. Preserve
        # a small buried overlap: the bottom cap ends within the shoe shell.
        target_y = float(foot[:, 1].max() - 0.013)
        assert 0 < target_y < foot[:, 1].max() < lower
        assert 0.025 < lower - target_y < 0.035
        updated = original.copy()
        updated[ids, 1] = target_y
        old_id = sp['attributes']['POSITION']
        old = j['accessors'][old_id]
        d['meshes'][0]['primitives'][shin]['attributes']['POSITION'] = add_accessor(
            d, raw, updated.astype(render.CT[old['componentType']]),
            old['componentType'], old['type'], 34962, True)
        changes.append({'shin_primitive': shin, 'shoe_primitive': shoe,
                        'vertex_indices': ids.tolist(), 'vertices_moved': len(ids),
                        'old_lower_y': float(lower), 'new_lower_y': target_y,
                        'shoe_crown_y': float(foot[:, 1].max()),
                        'old_gap_y': float(lower - foot[:, 1].max()),
                        'buried_depth_y': 0.013,
                        'next_shin_ring_y': float(next_level),
                        'xz_bounds': [original[ids][:, [0, 2]].min(0).tolist(),
                                      original[ids][:, [0, 2]].max(0).tolist()]})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_glb(OUT, d, raw)
    ej, eb = render.load(OUT)
    assert eb[:len(binary)] == binary
    assert len(ej['skins'][0]['joints']) == 56 and len(ej['animations']) == 29
    for key in ('nodes', 'skins', 'animations', 'materials', 'images', 'textures', 'scenes'):
        assert ej.get(key) == j.get(key)
    for mi, mesh in enumerate(j['meshes']):
        for pi, oldp in enumerate(mesh['primitives']):
            newp = ej['meshes'][mi]['primitives'][pi]
            assert newp['indices'] == oldp['indices']
            for attr, accessor in oldp['attributes'].items():
                if mi == 0 and pi in (4, 5) and attr == 'POSITION':
                    continue
                assert newp['attributes'][attr] == accessor
    report = {'candidate': 'L1', 'source_v3_sha256': SHA,
              'source_B2_sha256': B2_SHA, 'glb': str(OUT),
              'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
              'operation': 'Measured lower shin ring extension into each existing shoe',
              'changes': changes, 'triangles_added_or_deleted': 0,
              'vertices_moved': sum(c['vertices_moved'] for c in changes),
              'face_scalp_eyes_brows_nose_lips_ears_arms_torso_unchanged': True,
              'rig_skin_weights_nodes_materials_animation_definitions_exact': True,
              'original_binary_prefix_exact': True,
              'status': 'PENDING_VISUAL_AND_GODOT', 'production_approved': False,
              'limitations': ['Shoe termination intentionally overlaps the shin shell; this is not a welded anatomical ankle.',
                              'Facial holes, scalp-to-face seam, folds, and other limb joints are outside this local operation.',
                              'Animation deformation requires separate pose inspection.']}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: report[k] for k in ('candidate', 'sha256', 'vertices_moved', 'triangles_added_or_deleted', 'status')}))

if __name__ == '__main__':
    main()
