"""Restore surviving Alastor facial colours by exact Delta triangle provenance.

The embedded GammaHead texture is retained in the manikin GLB, but the face
primitive lost UVs and was forced to the neutral manikin material. This does
not synthesize geometry, close holes, or import hair/glasses meshes. V1 is a
visual-likeness candidate for comparison, not a final anatomical repair.
"""
from pathlib import Path
import copy, hashlib, json, sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render
from reparar_v03 import add_accessor, write_glb
from g2c5_recover_face import triangle_key, source_selection
from g2c4_inspect import REFERENCE

BASE = Path('build/g2c6/maniqui_G2C6_L1_UNIONES_TOBILLOS_SIN_APROBAR.glb')
BASE_SHA = 'cf759292adace095b0a0c41516e0ecebead3cb48efb44210afcbbef8cc8d71e0'
OUT = Path('build/g2c7/maniqui_G2C7_V1_RASGOS_COLOR_SIN_APROBAR.glb')
REPORT = Path('docs/maniqui/g2c7/V1.json')

def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
    if OUT.exists(): raise FileExistsError(OUT)
    j, binary = render.load(BASE)
    rj, rb = render.load(REFERENCE)
    prim = j['meshes'][0]['primitives'][0]
    refprim = rj['meshes'][0]['primitives'][13]
    faces = render.acc(j, binary, prim['indices']).astype(int).reshape(-1, 3)
    attrs = {a: render.acc(j, binary, k) for a, k in prim['attributes'].items()}
    pos = attrs['POSITION']
    refpos = render.acc(rj, rb, refprim['attributes']['POSITION'])
    reffaces = render.acc(rj, rb, refprim['indices']).astype(int).reshape(-1, 3)
    refuv = render.acc(rj, rb, refprim['attributes']['TEXCOORD_0'])
    lookup = {triangle_key(refpos[tri]): k for k, tri in enumerate(reffaces)}

    # Choose a real skin texel using measured seven-sample colour votes from
    # the exact same source texture. It colours only the out-of-face fallback.
    _, _, _, _, ids, colours, _ = source_selection(j, binary, faces)
    med = np.median(colours.reshape(-1, 3), axis=0)
    reftex = next(g[3] for g in render.gather(REFERENCE) if len(g[0]) == len(reffaces))
    h, w = reftex.shape[:2]
    selected_uv = refuv[reffaces[ids]].reshape(-1, 2)
    pix = reftex[(np.mod(selected_uv[:, 1], 1) * (h-1)).astype(int),
                 (np.mod(selected_uv[:, 0], 1) * (w-1)).astype(int)]
    skin_uv = selected_uv[np.argmin(np.linalg.norm(pix-med, axis=1))]

    flat = faces.reshape(-1)
    expanded = {name: array[flat].copy() for name, array in attrs.items()}
    texcoords = np.tile(skin_uv, (len(flat), 1)).astype(np.float32)
    exact = []
    face_region = []
    for face_no, tri in enumerate(faces):
        points = pos[tri]
        center = points.mean(axis=0)
        facial = bool(center[2] > .10 and .59 < center[1] < .80 and abs(center[0]) < .175)
        src = lookup.get(triangle_key(points))
        if src is None or not facial: continue
        reference_tri = reffaces[src]
        source_points = refpos[reference_tri]
        corner = [int(np.argmin(np.linalg.norm(source_points - p, axis=1))) for p in points]
        if max(np.linalg.norm(source_points[corner] - points, axis=1)) > 1e-6: continue
        texcoords[3*face_no:3*face_no+3] = refuv[reference_tri[corner]]
        exact.append(face_no)
        face_region.append(face_no)

    d = copy.deepcopy(j)
    raw = bytearray(binary)
    dst = d['meshes'][0]['primitives'][0]
    for name, data in expanded.items():
        old = j['accessors'][prim['attributes'][name]]
        dst['attributes'][name] = add_accessor(
            d, raw, data.astype(render.CT[old['componentType']]),
            old['componentType'], old['type'], 34962, name == 'POSITION')
    dst['attributes']['TEXCOORD_0'] = add_accessor(d, raw, texcoords, 5126, 'VEC2', 34962)
    dst['indices'] = add_accessor(d, raw, np.arange(len(flat), dtype=np.uint32), 5125, 'SCALAR', 34963)
    dst['material'] = refprim['material']
    assert dst['material'] == 22 and d['materials'][22] == rj['materials'][22]
    skin_colour = np.median(colours.reshape(-1, 3), axis=0).tolist()
    d['materials'].append({'name':'G2C7_skin_from_Delta_texture_median',
        'pbrMetallicRoughness':{'baseColorFactor':skin_colour+[1.0],
                               'metallicFactor':0.0,'roughnessFactor':0.85},
        'doubleSided':True})
    skin_material = len(d['materials']) - 1
    # Smooth V3 calva and measured neck retain their geometry/weights exactly.
    for pi in (1, 2): d['meshes'][0]['primitives'][pi]['material'] = skin_material
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_glb(OUT, d, raw)
    ej, eb = render.load(OUT)
    ep = ej['meshes'][0]['primitives'][0]
    assert eb[:len(binary)] == binary
    assert len(ej['skins'][0]['joints']) == 56 and len(ej['animations']) == 29
    assert ej['nodes'] == j['nodes'] and ej['skins'] == j['skins'] and ej['animations'] == j['animations']
    for name, data in expanded.items():
        assert np.array_equal(render.acc(ej, eb, ep['attributes'][name]), data)
    assert np.array_equal(render.acc(ej, eb, ep['indices']).reshape(-1), np.arange(len(flat)))
    assert ej['meshes'][0]['primitives'][3:] == j['meshes'][0]['primitives'][3:]
    assert ej['meshes'][1:] == j['meshes'][1:]
    report = {'candidate':'V1','base':str(BASE),'base_sha256':BASE_SHA,
        'reference':str(REFERENCE),'reference_sha256':hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        'glb':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
        'original_face_triangles':len(faces),'source_exact_textured_faces':len(exact),
        'source_exact_textured_face_indices':exact,'fallback_skin_faces':len(faces)-len(exact),
        'new_face_vertex_count':len(flat),'previous_face_vertex_count':len(pos),
        'skin_texture_median_rgb':skin_colour,'fallback_uv':skin_uv.tolist(),
        'source_texture_material':22,'bald_cap_and_neck_material':skin_material,
        'geometry_positions_and_weights_exact_per_corner':True,
        'skin_rig_nodes_animations_exact':True,'triangles_added_or_deleted':0,
        'original_binary_prefix_exact':True,'status':'PENDING_VISUAL','production_approved':False,
        'limitations':['No facial holes or joins are repaired','Textured face uses duplicated vertices to preserve each original UV seam',
                       'Material of scalp/neck changes to measured skin median; body remains neutral grey',
                       'Legacy 15 facial clips still refer to zero-geometry morph targets']}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print({k:report[k] for k in ('sha256','source_exact_textured_faces','fallback_skin_faces','new_face_vertex_count')})

if __name__ == '__main__': main()
