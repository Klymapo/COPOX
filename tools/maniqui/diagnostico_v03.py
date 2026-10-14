#!/usr/bin/env python3
"""Auditoria geometrica sin alterar el GLB base. Ejecutar desde cualquier carpeta."""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render

def audit(source):
    doc, blob = render.load(source)
    pieces = []
    for k,p in enumerate(doc['meshes'][0]['primitives']):
        a = p['attributes']
        V = render.acc(doc,blob,a['POSITION'])
        F = render.acc(doc,blob,p['indices']).astype(int).reshape(-1,3)
        J = render.acc(doc,blob,a['JOINTS_0']).astype(int)
        W = render.acc(doc,blob,a['WEIGHTS_0'])
        name = p.get('extras',{}).get('pieza', f'prim{k}')
        rec = dict(name=name, vertices=len(V), triangles=len(F),
             bounds=[np.round(V.min(0),4).tolist(),np.round(V.max(0),4).tolist()],
             weight_min=float(W.sum(1).min()),weight_max=float(W.sum(1).max()),
             joints_max=int(J.max()), finite=bool(np.isfinite(V).all() and np.isfinite(W).all()))
        if name in ['Cabeza','Craneo']:
            edges = np.sort(np.concatenate((F[:,[0,1]],F[:,[1,2]],F[:,[2,0]])),axis=1)
            edges, count = np.unique(edges,axis=0,return_counts=True)
            be = edges[count==1]
            border = V[np.unique(be)]
            rec['boundary_edges'] = len(be)
            rec['boundary_verts'] = len(border)
            rec['boundary_bounds'] = [np.round(border.min(0),4).tolist(),np.round(border.max(0),4).tolist()]
            rec['boundary_y_percentiles']=np.round(np.percentile(border[:,1],[0,10,25,50,75,90,100]),4).tolist()
            rec['boundary_z_percentiles']=np.round(np.percentile(border[:,2],[0,10,25,50,75,90,100]),4).tolist()
            rec['face_y_percentiles']=np.round(np.percentile(V[:,1],[0,5,25,50,75,95,100]),4).tolist()
        pieces.append(rec)
    return {'source':source,'nodes':len(doc['nodes']), 'bones':len(doc['skins'][0]['joints']),
       'animations': [x.get('name') for x in doc['animations']],
       'pieces':pieces}
if __name__ == '__main__':
    data = audit(sys.argv[1])
    print(json.dumps(data,indent=2,ensure_ascii=False))
    if len(sys.argv)>2:
        Path(sys.argv[2]).parent.mkdir(parents=True,exist_ok=True)
        Path(sys.argv[2]).write_text(json.dumps(data,indent=2,ensure_ascii=False))
