#!/usr/bin/env python3
"""Reproducible G2-C profiling on synthetic loops; no benchmark speed promises."""
from __future__ import annotations
import hashlib,json,statistics,time,platform
from pathlib import Path
import numpy as np
import scipy
from copox.geometry.advancing_stitch import stitch_unequal_loops
from copox.geometry.kernel import boundary_loops


def disks(n,m):
    aa=np.arange(n)*2*np.pi/n
    bb=np.arange(m)*2*np.pi/m
    top=np.column_stack((.25*np.cos(aa),.25*np.sin(aa),np.zeros(n)))
    bottom=np.column_stack((.25*np.cos(bb),.25*np.sin(bb),np.full(m,.09)))
    p=np.vstack((top,bottom,[[0,0,0],[0,0,.09]]))
    f=np.asarray([[n+m,i,(i+1)%n] for i in range(n)]+
                [[n+m+1,n+(j+1)%m,n+j] for j in range(m)],dtype=int)
    return p,f


def bench():
    items=[]
    for na,nb in ((12,19),(128,257),(512,769)):
        p,f=disks(na,nb)
        a,b=boundary_loops(f)
        hashes=[];timings=[]
        for rep in range(4):
            start=time.perf_counter()
            r=stitch_unequal_loops(p,f,a,b,max_gap=.19,max_aspect_ratio=100)
            timings.append((time.perf_counter()-start)*1000)
            hashes.append(hashlib.sha256(np.asarray(r.new_faces,dtype="<i8").tobytes()).hexdigest())
        if len(set(hashes))!=1:raise RuntimeError("El mismo input produce resultados diferentes")
        if r.report["production_ready"] or r.report["loops_after"] or len(r.new_faces)!=na+nb:
            raise RuntimeError("Fallo de invariantes en benchmark")
        items.append({"loop_a":na,"loop_b":nb,"bridge_triangles":na+nb,
                      "median_runtime_ms":round(statistics.median(timings[1:]),4),
                      "min_runtime_ms":round(min(timings[1:]),4),
                      "first_runtime_ms":round(timings[0],4),
                      "deterministic_sha256":hashes[0],
                      "run_count":4,
                      "timing_machine_specific":True})
    dest=Path("docs/maniqui/g2c/BENCHMARK_SYNTHETIC.json")
    dest.parent.mkdir(parents=True,exist_ok=True)
    content={"python":platform.python_version(),"numpy":np.__version__,
             "scipy":scipy.__version__,
             "algorithm":"KDTree starter + O(n+m) advancing steps; validated boundary loops",
             "samples":items,
             "warnings":["GitHub Actions timings vary across CPU, do not assert 10x/100x speedup",
                         "Not a benchmark of GLB import, texture baking, self-intersections or visual likeness",
                         "Real r3 must fail anatomy preflight before any stitch"]}
    dest.write_text(json.dumps(content,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(content,ensure_ascii=False))
if __name__=="__main__":
    bench()
