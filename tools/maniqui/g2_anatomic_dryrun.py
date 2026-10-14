#!/usr/bin/env python3
"""G2 · TRIAGE de Anatomic Cut sobre Maniquí r3 real.

Genera *máscaras candidatas*, bordes e imágenes reales de cuatro vistas para
tres bandas alternativas, jamás un 'GLB corregido' a partir de hipótesis.
Sólo permite llevar un recorte a GLB si un gate posterior verifica las
referencias correctas, normal/UV/skin y el contorno objetivo homologado.
"""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from copox.geometry.anatomic_roi import RegionBox,classify_anatomic_band
sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render

SRC=Path("assets/maniqui/maniqui_v0_3_r3.glb")
SHA="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
OUT=Path("docs/maniqui/g2")

def boxes():
    """Caja de protección por facción, no orientación global del motor.
    Aproximaciones conservadoras derivadas de rangos xyz del Maniquí r3.
    Se validan con capturas y fuentes del personaje antes de cualquier corte."""
    pairs=[
      ("cejas_ojos",(-.192,.686,.116),(.192,.788,.28)),
      ("nariz",(-.10,.609,.166),(.10,.722,.29)),
      ("boca",(-.146,.538,.132),(.146,.670,.29)),
      ("oreja_izquierda",(-.27,.605,-.165),(-.19,.755,.23)),
      ("oreja_derecha",(.19,.605,-.165),(.27,.755,.23)),
      ("mandibula",(-.20,.532,.10),(.20,.642,.285)),
      ("nuca_baja",(-.19,.530,-.30),(.19,.653,-.065))
    ]
    return [RegionBox(name,p,q) for name,p,q in pairs]

def boundary_edges(f):
    if not len(f):return {"edges":0,"nonmanifold":0}
    edges=np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]),axis=0),axis=1)
    _,cts=np.unique(edges,axis=0,return_counts=True)
    return {"edges":int(np.count_nonzero(cts==1)),"nonmanifold":int(np.count_nonzero(cts>2))}

def make_sheet(tris,fc,cc,labels,output,head=True):
    hbounds=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))
    views=[("FRONTAL",0),("TRES CUARTOS",45),("PERFIL",90),("ESPALDA",180)]
    canvas=Image.new("RGB",(420*4,468+45),"white")
    draw=ImageDraw.Draw(canvas)
    face=(tris[0][0],np.array([.65,.65,.65]),None,None,fc)
    cap=(tris[1][0],np.array(cc),None,None,None)
    for i,(lab,yaw) in enumerate(views):
        im=render.render([face,cap],yaw,W=420,H=468,bounds=hbounds)
        canvas.paste(im,(420*i,45))
        draw.text((i*420+12,13),lab+" - "+labels,fill=(25,37,50))
    canvas.save(output)

def main():
    if hashlib.sha256(SRC.read_bytes()).hexdigest()!=SHA:
        raise RuntimeError("El modelo base fue cambiado; no continuar")
    j,b=render.load(SRC)
    if len(j["skins"][0]["joints"])!=56 or len(j["animations"])!=29:
        raise RuntimeError("Rig y animaciones no coinciden")
    face,cap=j["meshes"][0]["primitives"][:2]
    if face.get("extras",{}).get("pieza")!="Cabeza" or cap.get("extras",{}).get("pieza")!="Craneo":
        raise RuntimeError("Primitivas distintas")
    p=render.acc(j,b,face["attributes"]["POSITION"])
    f=render.acc(j,b,face["indices"]).astype(np.int64).reshape(-1,3)
    cp=render.acc(j,b,cap["attributes"]["POSITION"])
    cf=render.acc(j,b,cap["indices"]).astype(np.int64).reshape(-1,3)
    edges=np.sort(np.vstack((cf[:,[0,1]],cf[:,[1,2]],cf[:,[2,0]])),axis=1)
    unique,count=np.unique(edges,axis=0,return_counts=True)
    ids=np.unique(unique[count==1])
    rim=cp[ids]
    if len(ids)!=128:raise RuntimeError("No se encontró el borde r3 de 128 vertices")
    original_p=p.copy();original_f=f.copy()
    tris=render.gather(SRC)
    OUT.mkdir(parents=True,exist_ok=True)
    profiles=[("conservador",.015,.008),("intermedio",.026,.016),("amplio",.042,.024)]
    report={"source":str(SRC),"sha256":SHA,"up":"Y","front":"+Z","units":"m",
      "rig_bones":56,"clips":29,"face_triangles_original":int(len(f)),
      "protection_boxes":[{"name":x.name,"min":x.minimum,"max":x.maximum} for x in boxes()],
      "protection_policy":"Si algun vértice de un triángulo cae dentro de una región protegida, el triángulo completo queda congelado",
      "profile_results":[],"all_original_files_preserved":True,
      "generated_glb":False,"artistic_references_authoritative":False,
      "note":"Sólo pruebas de máscaras. No se afirma que la banda extraída forme un contorno homólogo"}
    for name,dist,clearance in profiles:
        roi=classify_anatomic_band(p,f,rim,boxes(),seam_distance=dist,clearance=clearance,
                                  angle_center_xz=(-.000038,-.010537))
        label=np.zeros(len(f),dtype=np.int8)
        label[roi.review]=1
        label[roi.candidate]=2
        label[roi.protected]=3
        # Para pintar la región sobre el cráneo, usar SOLO atributos del renderer,
        # no sobreescribir ni exportar el GLB.
        palette=np.array([[.53,.58,.63],[.93,.75,.31],[.12,.70,.53],[.96,.35,.33]])
        colors=np.array([render.srgb(q) for q in palette])
        fc=colors[label]
        make_sheet(tris,fc,[.57,.57,.57],name,OUT/f"g2_mascara_{name}.png")
        kept=f[~roi.candidate]
        before=boundary_edges(f);after=boundary_edges(kept)
        # Visualizar también el resultado hipotético en memoria, sin exportación;
        # NO confundir la eliminación no validada con una reparación.
        ghost=(tris[0][0][~roi.candidate],tris[0][1],None,None,None)
        hbounds=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))
        sheet=Image.new("RGB",(420*4,468+45),"white");d=ImageDraw.Draw(sheet)
        for i,(lab,angle) in enumerate([("Frente",0),("3/4",45),("Perfil",90),("Espalda",180)]):
            im=render.render([ghost,tris[1]],angle,W=420,H=468,bounds=hbounds)
            sheet.paste(im,(420*i,45))
            d.text((420*i+12,13),lab+" - SIN caras candidatas (SIMULACIÓN)",fill=(28,36,48))
        sheet.save(OUT/f"g2_hipotesis_corte_{name}.png")
        row={"profile":name,**roi.report,
             "protection_counts_overlapping":roi.protection_counts,
             "boundary_before_indices":before,
             "boundary_if_candidate_faces_removed":after,
             "triangles_removed_in_hypothesis":int(roi.candidate.sum()),
             "protected_triangles_removed":int((roi.candidate & roi.protected).sum()),
             "remaining_original_face_triangles":int(len(kept)),
             "faces_in_candidate_indices":np.flatnonzero(roi.candidate).astype(int).tolist(),
             "cut_gate_status":"BLOCKED_FOR_REVIEW",
             "why_not_cut":"No hay máscara anatómica respaldada por vistas de la cabeza base ni contorno 128 a 128; la región tiene discontinuidades"}
        report["profile_results"].append(row)
    # No hay criterio válido aún para seleccionar una máscara como 'mejor'
    # a partir de IoU; ese modelo está visualmente fragmentado desde antes.
    report["recommendation"]={
      "status":"RESEARCH_REQUIRED",
      "next_step":"Identificar el borde cuttable de la isla principal, proteger facciones en cada vista y construir una línea cerrada de corte con topología sin bifurcaciones",
      "no_candidate_promoted":True,
      "stitch_not_allowed":True,
      "required_before_glb":["referencias_del_mismo_personaje","mascara_proteccion_verificada",
                             "loop_cerrado_anatomico","atributos_uv_skin_validados",
                             "reimportacion_glb_y_prueba_godot"]
    }
    if not np.array_equal(p,original_p) or not np.array_equal(f,original_f):
        raise RuntimeError("Mutación inesperada de arrays fuente")
    if hashlib.sha256(SRC.read_bytes()).hexdigest()!=SHA:
        raise RuntimeError("Se alteró archivo de origen")
    (OUT/"g2_mask_analysis.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    summary={k:v for k,v in report.items() if k not in ("profile_results","protection_boxes")}
    summary["profiles"]=[{k:v for k,v in row.items() if k!="faces_in_candidate_indices"} for row in report["profile_results"]]
    (OUT/"g2_SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"mask_summaries":[{"profile":x["profile"],"protected":x["protected"],
        "candidate":x["candidate"],"sectors":x["candidate_rim_sectors"],
        "boundary_after":x["boundary_if_candidate_faces_removed"]} for x in report["profile_results"]],
        "glb_generated":False},ensure_ascii=False))
    return report

if __name__=="__main__":
    main()
