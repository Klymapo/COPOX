"""Split measured Alastor eye/brow triangles from the neutral face surface.

Derived independently from L1. V1's broad texture transfer exposed black
residual hair/glasses. V2 textures only provenance-matched visible eye and
brow triangles; the rest uses a skin tone sampled from the source atlas.
Geometry and skinning of every original triangle remain exactly unchanged.
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
OUT = Path('build/g2c7/maniqui_G2C7_V2_RASGOS_SELECTIVOS_SIN_APROBAR.glb')
REPORT = Path('docs/maniqui/g2c7/V2.json')

def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
    if OUT.exists(): raise FileExistsError(OUT)
    j, b = render.load(BASE)
    rj, rb = render.load(REFERENCE)
    pr = j['meshes'][0]['primitives'][0]
    rp = rj['meshes'][0]['primitives'][13]
    f = render.acc(j, b, pr['indices']).astype(int).reshape(-1, 3)
    attrs = {name:render.acc(j, b, a) for name, a in pr['attributes'].items()}
    pos = attrs['POSITION']
    rv = render.acc(rj, rb, rp['attributes']['POSITION'])
    rf = render.acc(rj, rb, rp['indices']).astype(int).reshape(-1, 3)
    uv = render.acc(rj, rb, rp['attributes']['TEXCOORD_0'])
    lookup = {triangle_key(rv[tri]):int(i) for i,tri in enumerate(rf)}
    _, _, _, _, _, colours, _ = source_selection(j, b, f)
    skin_rgb = np.median(colours.reshape(-1, 3), axis=0).tolist()
    chosen, corners, source_faces = [], [], []
    for fi, tri in enumerate(f):
        xyz = pos[tri]
        center = xyz.mean(axis=0)
        # Measured envelope of the original visible eyes and brows; central
        # bridge, cheeks and ears are deliberately excluded from texture.
        eyes = (.645 < center[1] < .735 and .035 < abs(center[0]) < .139 and center[2] > .17)
        brows = (.729 < center[1] < .790 and .02 < abs(center[0]) < .155 and center[2] > .145)
        if not (eyes or brows): continue
        src = lookup.get(triangle_key(xyz))
        if src is None: continue
        reftri = rf[src]
        near = [int(np.argmin(np.linalg.norm(rv[reftri]-x, axis=1))) for x in xyz]
        if max(np.linalg.norm(rv[reftri[near]]-xyz, axis=1)) > 1e-6: continue
        chosen.append(fi)
        corners.extend(uv[reftri[near]])
        source_faces.append(src)
    chosen = np.array(chosen, dtype=int)
    assert 300 < len(chosen) < 1100
    keep = np.delete(f, chosen, axis=0)
    d = copy.deepcopy(j)
    raw = bytearray(b)
    d['materials'].append({'name':'G2C7_skin_median_from_Delta',
        'pbrMetallicRoughness':{'baseColorFactor':skin_rgb+[1.0],
                               'metallicFactor':0.0,'roughnessFactor':0.85},
        'doubleSided':True})
    skin_mat = len(d['materials']) - 1
    skin_prim = d['meshes'][0]['primitives'][0]
    skin_prim['indices'] = add_accessor(d, raw, keep.astype(np.uint32).reshape(-1), 5125, 'SCALAR', 34963)
    skin_prim['material'] = skin_mat
    # Append an independently skinned textured surface. Duplicating corners
    # preserves the source atlas seams without moving geometry.
    texfaces = f[chosen]
    flat = texfaces.reshape(-1)
    textured = {'attributes':{}, 'material':rp['material'], 'mode':4}
    for name, array in attrs.items():
        old = j['accessors'][pr['attributes'][name]]
        textured['attributes'][name] = add_accessor(
            d, raw, array[flat].astype(render.CT[old['componentType']]),
            old['componentType'], old['type'], 34962, name=='POSITION')
    textured['attributes']['TEXCOORD_0'] = add_accessor(
        d, raw, np.asarray(corners, dtype=np.float32), 5126, 'VEC2', 34962)
    textured['indices'] = add_accessor(d, raw, np.arange(len(flat), dtype=np.uint32), 5125, 'SCALAR', 34963)
    d['meshes'][0]['primitives'].append(textured)
    for pi in (1,2): d['meshes'][0]['primitives'][pi]['material'] = skin_mat
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_glb(OUT, d, raw)
    ej, eb = render.load(OUT)
    ap = ej['meshes'][0]['primitives'][-1]
    assert eb[:len(b)] == b
    assert len(ej['skins'][0]['joints'])==56 and len(ej['animations'])==29
    assert ej['nodes']==j['nodes'] and ej['skins']==j['skins'] and ej['animations']==j['animations']
    assert np.array_equal(render.acc(ej, eb, ap['attributes']['POSITION']), pos[flat])
    assert np.array_equal(render.acc(ej, eb, ap['attributes']['WEIGHTS_0']), attrs['WEIGHTS_0'][flat])
    assert np.array_equal(render.acc(ej, eb, ap['attributes']['JOINTS_0']), attrs['JOINTS_0'][flat])
    a = np.vstack([keep,texfaces]);keys=lambda t:sorted(triangle_key(x) for x in t)
    assert keys(pos[a])==keys(pos[f])
    report={'candidate':'V2','source':str(BASE),'source_sha256':BASE_SHA,
        'reference':str(REFERENCE),'reference_sha256':hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        'glb':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
        'source_exact_eyes_brows_triangles':len(chosen),'textured_original_triangle_indices':chosen.tolist(),
        'source_triangle_indices':source_faces,'skin_triangles':len(keep),
        'skin_rgb':skin_rgb,'geometric_triangles_added_or_deleted':0,
        'spatial_triangle_multiset_exact':True,'joint_weight_and_normal_corners_exact':True,
        'nodes_skin_animation_definitions_exact':True,'extra_surface_for_atlas_seams':1,
        'original_binary_prefix_exact':True,'status':'PENDING_VISUAL','production_approved':False,
        'limitations':['Colour restoration only; facial holes, nose and jaw remain open',
                       'Original 15 orphan facial morph clips remain nonfunctional',
                       'The strict face envelope may omit some valid skin detail']}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print({k:report[k] for k in ('sha256','source_exact_eyes_brows_triangles','skin_triangles')})

if __name__=='__main__':main()
