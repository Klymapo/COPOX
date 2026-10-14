#!/usr/bin/env python3
"""COPOX: caso sintético completo de Visual Critic + planificador + Scully.

Todas las referencias son formas matemáticas nuevas creadas en este script.
Un bulto SE INYECTA deliberadamente: no afirma detección semántica general.
El script no lee Beta/Gamma/Hunyuan, no necesita IA ni altera GLB previos.
"""
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from copox.visual.critic import audit,mask_metrics
from copox.visual.mesh_diagnostics import analyze_plane_region
from copox.visual.geometry_planner import propose
from copox.geometry.surface_sculpt import flatten_surface

OUT=Path("docs/visual/geometry_loop_demo")
OUT.mkdir(parents=True,exist_ok=True)
VIEWS=[("front",0.),("three_quarter",math.pi/4),("side",math.pi/2),("back",math.pi)]

def sphere(u=52,v=34):
    pts=[];faces=[]
    for i in range(v+1):
        a=-math.pi/2+math.pi*(i+1e-4)/(v+2e-4)
        for j in range(u):
            b=j*2*math.pi/u
            pts.append([.23*math.cos(a)*math.cos(b),.26*math.sin(a),
                        .245*math.cos(a)*math.sin(b)])
    for i in range(v):
        for j in range(u):
            x=i*u+j;y=i*u+(j+1)%u;z=(i+1)*u+j;w=(i+1)*u+(j+1)%u
            faces.extend(((x,y,z),(y,w,z)))
    return np.asarray(pts,float),np.asarray(faces,int)

def mask_mesh(vertices,faces,yaw,size=(240,260)):
    p=np.asarray(vertices)
    screen_x=p[:,0]*math.cos(yaw)+p[:,2]*math.sin(yaw)
    screen_y=p[:,1]
    uv=np.column_stack((120+screen_x*435,130-screen_y*435))
    img=Image.new("L",size,0);d=ImageDraw.Draw(img)
    for f in faces:d.polygon([tuple(uv[k]) for k in f],fill=255)
    return img

def pretty(mask,path):
    im=Image.new("RGB",mask.size,(246,247,249))
    color=Image.new("RGB",mask.size,(133,163,182))
    im.paste(color,mask=mask)
    im.save(path)

base,faces=sphere()
p=base.copy()
front=(p[:,2]>.115)&(np.abs(p[:,0])<.2)&(p[:,1]>-.07)&(p[:,1]<.225)
peak=.046*np.exp(-((p[:,0]/.11)**2+((p[:,1]-.09)/.11)**2))
p[:,2]+=front*peak
roi=(p[:,2]>.12)&(np.abs(p[:,0])<.185)&(p[:,1]>-.06)&(p[:,1]<.23)
plane=.245
diagnosis=analyze_plane_region(p,faces,roi,[0,0,1],plane)

supplied=[];references=[];views=[]
for name,yaw in VIEWS:
    ref_mask=mask_mesh(base,faces,yaw)
    cand_mask=mask_mesh(p,faces,yaw)
    ref_path=f"ref_{name}.png"
    cand_path=f"candidate_{name}.png"
    rm=f"ref_mask_{name}.png";cm=f"candidate_mask_{name}.png"
    pretty(ref_mask,OUT/ref_path);pretty(cand_mask,OUT/cand_path)
    ref_mask.save(OUT/rm);cand_mask.save(OUT/cm)
    supplied.append(ref_path)
    references.append({"id":f"reference_{name}","view":name,
                       "image":ref_path,"mask":rm,"camera_alignment":"exact"})
    views.append({"view":name,"image":cand_path,"mask":cm})
# The defect class is known from the synthetic construction. Pixel masks
# only confirm which camera directions reveal the intentionally added protrusion.
per={}
for row in references:
    name=row["view"]
    val=mask_metrics(OUT/row["mask"],OUT/f"candidate_mask_{name}.png")
    if val["iou"]<.9995:
        assessment="supports"
        note=f"Diferencia de silueta medible: IoU={val['iou']:.6f}; no prueba causa semántica"
    else:
        assessment="not_visible"
        note=f"Sin cambio perceptible en máscara, IoU={val['iou']:.6f}"
    per[row["id"]]={"assessment":assessment,"note":note}
if not any(v["assessment"]=="supports" for v in per.values()):
    raise RuntimeError("Fixture sintética no crea cambio visible para ninguna vista")
manifest={"asset_id":"synthetic-bulged-head-v1",
          "provided_reference_files":supplied,
          "required_views":[row[0] for row in VIEWS],
          "references":references,
          "candidate":{"id":"known-bulge","views":views},
          "anomalies":[{"id":"synthetic_bulge","region":"front_head",
             "description":"Protuberancia frontal añadida intencionalmente en código",
             "per_reference":per}]}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
vreport=audit(manifest,root=OUT,output=OUT/"compare",make_sheets=True)
geo={"anomalies":{"synthetic_bulge":dict(diagnosis,kind="surface_bulge",
     flatten={"direction":[0,0,1],
              "target_projection":plane,"region_center":[0,.09,.225],
              "region_radii":[.185,.18,.19],
              "strength":1.,"falloff":.42,"max_displacement":.055})}}
(OUT/"measured_geometry.json").write_text(json.dumps(geo,indent=2,ensure_ascii=False)+"\n")
plan=propose(vreport,geo)
(OUT/"geometry_plan.json").write_text(json.dumps(plan,indent=2,ensure_ascii=False)+"\n")
suggestions=plan["recommendations"]
if len(suggestions)!=1 or suggestions[0]["operator"]!="Scully" or suggestions[0]["state"]!="PLAN_READY_FOR_SANDBOX":
    raise RuntimeError("El motor no seleccionó Scully con evidencia completa: "+str(plan))
args=suggestions[0]["arguments"]["parameters"]
corrected=flatten_surface(p,direction=args["direction"],target_projection=args["target_projection"],
    region_center=args["region_center"],region_radii=args["region_radii"],
    strength=args["strength"],falloff=args["falloff"],
    protected=np.zeros(len(p),dtype=bool),
    max_displacement=args["max_displacement"])
before_scores={};after_scores={}
contact=Image.new("RGB",(240*4,300*3),(252,252,252))
draw=ImageDraw.Draw(contact)
for col,(name,yaw) in enumerate(VIEWS):
    reference=mask_mesh(base,faces,yaw)
    original=mask_mesh(p,faces,yaw)
    fixed=mask_mesh(corrected.positions,faces,yaw)
    fixed.save(OUT/f"corrected_mask_{name}.png")
    pretty(fixed,OUT/f"corrected_{name}.png")
    before_scores[name]=mask_metrics(OUT/f"ref_mask_{name}.png",OUT/f"candidate_mask_{name}.png")["iou"]
    after_scores[name]=mask_metrics(OUT/f"ref_mask_{name}.png",OUT/f"corrected_mask_{name}.png")["iou"]
    for row,(label,im) in enumerate((("REFERENCIA",reference),("CON BULTO",original),("SCULLY",fixed))):
        rgb=Image.new("RGB",im.size,(248,249,252))
        rgb.paste(Image.new("RGB",im.size,(139,165,187)),mask=im)
        contact.paste(rgb,(col*240,row*300+25))
        draw.text((col*240+9,row*300+6),f"{name}: {label}",fill=(38,49,64))
contact.save(OUT/"four_views_before_after.png")
# No afirmar que una mejora en silueta prueba semejanza; sí es métrica objetiva.
if not after_scores["side"]>before_scores["side"]:
    raise RuntimeError("Scully no mejoró la vista sintética de perfil")
summary={
    "description":"Fixture programada: protuberancia frontal + planes cuantitativos, sin IA de visión",
    "reference_count":len(supplied),"reference_coverage":vreport["all_references_accounted_for"],
    "critic_status":vreport["status"],"plan_status":plan["status"],
    "operator_proposed":suggestions[0]["operator"],"automatic_approval":False,
    "manual_review_pending":suggestions[0]["independent_visual_review_pending"],
    "scully_changed_vertices":corrected.changed_vertices,
    "scully_max_displacement_mm":round(corrected.maximum_displacement*1000,4),
    "before_mask_iou":before_scores,"after_mask_iou":after_scores,
    "limitations":["No detección semántica autónoma: bulto inyectado deliberadamente",
                   "No GLB de personaje ni Godot; demostración de la selección y operador",
                   "No promoción automática"]
}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(summary,indent=2,ensure_ascii=False))
