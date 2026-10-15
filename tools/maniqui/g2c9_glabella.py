"""Repair three tiny glabella gaps and smooth its isolated skin island.

All dimensions and target components are measured from the pinned G2-C8
GLB. The exterior ring, eyes, eyebrows, nose tip and every other primitive
remain unchanged. This is a regional candidate pending artistic inspection.
"""
from pathlib import Path
import collections
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
OUT = Path('build/g2c9/maniqui_G2C9_GLABELA_SUAVE_SIN_APROBAR.glb')
REPORT = Path('docs/maniqui/g2c9/GLABELA.json')


def island_faces(position, faces):
    welded, inverse = np.unique(np.round(position, 6), axis=0, return_inverse=True)
    welded_faces = inverse[faces]
    parent = np.arange(len(welded))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for triangle in welded_faces:
        for point in triangle[1:]:
            parent[root(point)] = root(triangle[0])
    groups = collections.defaultdict(list)
    for i, triangle in enumerate(welded_faces):
        groups[root(triangle[0])].append(i)
    candidates = []
    for group in groups.values():
        if len(group) < 30:
            continue
        center = position[faces[group].reshape(-1)].mean(axis=0)
        if abs(center[0]) < .01 and .70 < center[1] < .75 and center[2] > .17:
            candidates.append(group)
    assert len(candidates) == 1 and len(candidates[0]) == 110
    return np.array(candidates[0], dtype=int)


def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
    if OUT.exists():
        raise FileExistsError(OUT)
    source, binary = render.load(BASE)
    primitive = source['meshes'][0]['primitives'][0]
    attrs = {key: render.acc(source, binary, accessor) for key, accessor
             in primitive['attributes'].items()}
    position = attrs['POSITION']
    old_faces = render.acc(source, binary, primitive['indices']).astype(int).reshape(-1, 3)
    component = island_faces(position, old_faces)
    loops, failures = boundary_cycles(position, old_faces[component])
    assert not failures and sorted(map(len, loops)) == [3, 3, 4, 32]
    outer = max(loops, key=len)
    patches = []
    for loop in loops:
        if len(loop) == 3:
            patches.append(loop[::-1])
        elif len(loop) == 4:
            # The measured second diagonal is the only one that does not
            # add a welded non-manifold edge.
            patches.extend([[loop[0], loop[3], loop[1]],
                            [loop[1], loop[3], loop[2]]])
    patches = np.array(patches, dtype=int)
    faces = np.vstack([old_faces, patches])
    before = topology(position, old_faces)
    filled = topology(position, faces)
    assert filled['welded_nonmanifold_edges'] == before['welded_nonmanifold_edges']
    assert filled['welded_boundary_edges'] == before['welded_boundary_edges'] - 10

    # Weld only for calculating neighborhood positions. The exported vertex
    # indices and UV/skin seams are preserved exactly.
    unique, inverse = np.unique(np.round(position, 6), axis=0, return_inverse=True)
    island_faces_all = np.vstack([old_faces[component], patches])
    adjacency = collections.defaultdict(set)
    for tri in inverse[island_faces_all]:
        for a, b in zip(tri, np.roll(tri, -1)):
            adjacency[int(a)].add(int(b))
            adjacency[int(b)].add(int(a))
    boundary = set(int(x) for x in inverse[outer])
    island_used = set(adjacency)
    movable = sorted(island_used - boundary)
    assert 20 < len(movable) < 90
    current = unique[:, 2].copy()
    initial = current.copy()
    for _ in range(1):
        next_z = current.copy()
        for vertex in movable:
            neighbours = sorted(adjacency[vertex])
            next_z[vertex] = .8 * current[vertex] + .2 * np.mean(current[neighbours])
        current = next_z
    move = current - initial
    print('glabella max depth displacement', float(np.max(abs(move[movable]))))
    assert np.max(abs(move[movable])) < .005
    revised = position.copy()
    affected = np.flatnonzero(np.isin(inverse, movable))
    revised[affected, 2] += move[inverse[affected]]
    assert np.all(revised[:, :2] == position[:, :2])

    # Recompute normals within the island only, without modifying the outer
    # ring. Orient the local weighted estimate toward the original outward
    # front normal to avoid amplifying inverted stray triangles.
    normal = attrs['NORMAL'].copy()
    local = island_faces_all
    triangle = revised[local]
    tri_normals = np.cross(triangle[:, 1] - triangle[:, 0],
                           triangle[:, 2] - triangle[:, 0])
    accum = np.zeros_like(revised)
    for corner in range(3):
        np.add.at(accum, local[:, corner], tri_normals)
    for index in affected:
        norm = np.linalg.norm(accum[index])
        if norm > 1e-9 and accum[index, 2] > 0:
            normal[index] = accum[index] / norm

    updated = topology(revised, faces)
    assert not updated['degenerate_faces']
    assert updated['welded_nonmanifold_edges'] <= before['welded_nonmanifold_edges']
    original_scene = np.concatenate([g[0] for g in render.gather(BASE) if len(g[0])])
    other_count = len(original_scene) - len(old_faces)
    # gather() starts with the face primitive; replace its triangles only.
    scene = np.concatenate([revised[faces], original_scene[len(old_faces):]])
    changed = list(component) + list(range(len(old_faces), len(faces)))
    after_cross, after_coplanar = intersections(scene, changed)
    before_cross, before_coplanar = intersections(original_scene, component)
    # Compare spatial crossing pairs of the island against the unchanged
    # scene; reject any genuinely new crossing.
    assert not (after_cross - before_cross)

    result = copy.deepcopy(source)
    raw = bytearray(binary)
    dest = result['meshes'][0]['primitives'][0]
    for name, value in (('POSITION', revised), ('NORMAL', normal)):
        accessor = source['accessors'][primitive['attributes'][name]]
        dest['attributes'][name] = add_accessor(result, raw, value.astype(np.float32),
            accessor['componentType'], accessor['type'], 34962, name == 'POSITION')
    dest['indices'] = add_accessor(result, raw, faces.astype(np.uint32).reshape(-1),
                                   5125, 'SCALAR', 34963)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_glb(OUT, result, raw)
    exported, exported_binary = render.load(OUT)
    assert exported_binary[:len(binary)] == binary
    for key in ('nodes', 'skins', 'animations', 'materials', 'images', 'textures', 'scenes'):
        assert exported.get(key) == source.get(key), key
    assert exported['meshes'][0]['primitives'][1:] == source['meshes'][0]['primitives'][1:]
    for name in ('JOINTS_0', 'WEIGHTS_0'):
        assert dest['attributes'][name] == primitive['attributes'][name]
    assert len(exported['skins'][0]['joints']) == 56 and len(exported['animations']) == 29
    report = {'source': str(BASE), 'source_sha256': BASE_SHA,
              'glb': str(OUT), 'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
              'component_original_triangles': len(component), 'component_face_ids': component.tolist(),
              'closed_inner_rings': [3, 3, 4], 'added_triangles': patches.tolist(),
              'added_triangle_count': len(patches),
              'moved_vertex_count': len(affected),
              'max_depth_change': float(np.max(abs(move[movable]))),
              'protected_outer_ring_exact': True,
              'new_proper_crossings': len(after_cross - before_cross),
              'before': before, 'after': updated,
              'status': 'PENDING_VISUAL', 'production_approved': False}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(report['sha256'], report['moved_vertex_count'], report['max_depth_change'])


if __name__ == '__main__':
    main()
