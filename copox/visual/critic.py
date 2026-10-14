"""COPOX Visual Critic: auditoría exhaustiva de referencias, sin aprobación artificial.

- Cada imagen de referencia aportada recibe una comparación INDIVIDUAL.
- El candidato debe disponer de todas las vistas requeridas y cada referencia.
- Un resultado IoU no sustituye revisar semejanza, facciones ni composición.
- Sólo calcula IoU/Chamfer si existen máscaras registradas y cámaras exactas;
  nunca infiere máscaras ni alinea cámaras silenciosamente.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import distance_transform_edt

VIEW_DEFAULTS = ("front", "three_quarter", "side", "back")
VALID_ALIGNMENTS = {"exact", "approximate", "unknown"}
VALID_VERDICTS = {"PASS", "ISSUE", "UNDECIDED"}


def _inside_root(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Falta ruta de imagen o máscara")
    root = root.resolve()
    p = (root / name).resolve()
    if p != root and root not in p.parents:
        raise ValueError(f"Ruta fuera del directorio permitido: {name}")
    return p


def _mask(path: Path):
    with Image.open(path) as im:
        a = np.asarray(im.convert("L"), dtype=np.uint8)
    values = set(np.unique(a).tolist())
    if not values.issubset({0, 255}):
        raise ValueError(f"Máscara debe ser binaria 0/255: {path.name}")
    return a > 0


def mask_metrics(ref_mask: Path, cand_mask: Path) -> dict:
    """Cámara y escala deben haberse alineado ANTES del cálculo."""
    a = _mask(ref_mask); b = _mask(cand_mask)
    if a.shape != b.shape:
        raise ValueError("Máscaras con tamaños distintos; prohibido reescalar silenciosamente")
    union = np.logical_or(a, b).sum()
    iou = float(np.logical_and(a, b).sum() / union) if union else 1.0
    if not a.any() or not b.any():
        return {"iou": iou, "symmetric_chamfer_px": None}
    # Distancias de contorno bidireccionales, en píxeles.
    def edge(q):
        from scipy.ndimage import binary_erosion
        return q & ~binary_erosion(q)
    ea=edge(a);eb=edge(b)
    dab=distance_transform_edt(~eb)
    dba=distance_transform_edt(~ea)
    chamfer=(float(dab[ea].mean()) + float(dba[eb].mean())) / 2.0
    return {"iou": iou, "symmetric_chamfer_px": chamfer}


def _sheet(path: Path, ref: Path, candidate: Path, label: str):
    """Par comparativo en el mismo panel; nunca reescribir imágenes de entrada."""
    w,h=430,480
    dst=Image.new("RGB",(w*2,h+54),(248,249,250))
    draw=ImageDraw.Draw(dst)
    for x,src,title in ((0,ref,"REFERENCIA"),(w,candidate,"CANDIDATO")):
        with Image.open(src) as im:
            raw=im.convert("RGB")
            preview=ImageOps.contain(raw,(w-16,h-14),Image.Resampling.LANCZOS)
        dst.paste(preview,(x+(w-preview.width)//2,42+(h-preview.height)//2))
        draw.text((x+12,12),f"{title} · {src.name}",fill=(20,26,34))
    draw.text((12,h+24),label[:100],fill=(29,52,76))
    path.parent.mkdir(parents=True,exist_ok=True)
    dst.save(path)


def audit(manifest: dict, *, root: Path, output: Path, make_sheets: bool=True) -> dict:
    if not isinstance(manifest,dict):raise ValueError("Manifiesto JSON inválido")
    required=manifest.get("required_views",list(VIEW_DEFAULTS))
    refs=manifest.get("references")
    candidate=manifest.get("candidate")
    if not isinstance(required,list) or not required or len(set(required))!=len(required) or not all(isinstance(v,str) and v for v in required):
        raise ValueError("required_views debe ser una lista única de vistas")
    if not isinstance(refs,list) or not refs or not isinstance(candidate,dict) or not isinstance(candidate.get("views"),list):
        raise ValueError("Sin referencias o vistas de candidato; no se puede certificar")
    views=candidate["views"]
    issues=[];comparisons=[];seen_refs=set()
    candidates={}
    for row in views:
        if not isinstance(row,dict):
            issues.append("Candidato con vista inválida");continue
        key=(row.get("view"),row.get("pose","rest"))
        if key in candidates:
            issues.append(f"Vista/pose duplicada del candidato: {key}")
        candidates[key]=row
    for view in required:
        if (view,"rest") not in candidates:
            issues.append(f"Falta vista obligatoria: {view} / rest")
    ref_rows=[]
    for index,reference in enumerate(refs):
        if not isinstance(reference,dict):
            issues.append(f"Referencia {index} inválida");continue
        ref_id=reference.get("id")
        if not isinstance(ref_id,str) or not ref_id.strip() or ref_id in seen_refs:
            issues.append(f"ID de referencia vacío/duplicado: {ref_id}")
            continue
        seen_refs.add(ref_id)
        view,pose=reference.get("view"),reference.get("pose","rest")
        align=reference.get("camera_alignment","unknown")
        if not isinstance(view,str) or not view:
            issues.append(f"{ref_id}: sin vista identificada");continue
        if align not in VALID_ALIGNMENTS:
            issues.append(f"{ref_id}: camera_alignment inválido");continue
        cam=candidates.get((view,pose))
        if cam is None:
            issues.append(f"{ref_id}: falta candidato para vista={view}, pose={pose}");continue
        ref_rows.append((ref_id,reference,cam,view,pose,align))
    if not ref_rows:issues.append("No hay pares comparables")
    output.mkdir(parents=True,exist_ok=True)
    for rid,reference,cand,view,pose,align in ref_rows:
        missing=[]
        for label,row in (("reference",reference),("candidate",cand)):
            try:
                p=_inside_root(root,row.get("image"))
                if not p.is_file():missing.append(f"{label} image: {p}")
            except (ValueError,TypeError) as e:missing.append(f"{label}: {e}")
        if missing:
            issues.extend(f"{rid}: {e}" for e in missing);continue
        rimg=_inside_root(root,reference["image"])
        cimg=_inside_root(root,cand["image"])
        info={"reference_id":rid,"view":view,"pose":pose,"camera_alignment":align,
              "reference_image":str(rimg),"candidate_image":str(cimg),
              "metrics":None,"manual_review":None}
        # Requerimos revisión por referencia, no un solo score agregado.
        reviewed=reference.get("manual_review")
        if isinstance(reviewed,dict):
            verdict=reviewed.get("verdict")
            observations=reviewed.get("observations")
            reviewer=reviewed.get("reviewer")
            if verdict in VALID_VERDICTS and isinstance(observations,list) and observations and isinstance(reviewer,str) and reviewer.strip():
                info["manual_review"]={"verdict":verdict,"observations":observations,"reviewer":reviewer}
        rm=reference.get("mask");cm=cand.get("mask")
        if rm and cm and align=="exact":
            try:
                rp=_inside_root(root,rm);cp=_inside_root(root,cm)
                if not rp.is_file() or not cp.is_file():
                    issues.append(f"{rid}: faltan máscaras de vista exacta")
                else:
                    info["metrics"]=mask_metrics(rp,cp)
            except ValueError as e:
                issues.append(f"{rid}: {e}")
        elif rm and cm and align!="exact":
            info["metric_note"]="Cámara aproximada o desconocida; no se calcula IoU engañoso"
        else:
            info["metric_note"]="Sin pareja de máscaras registradas; comparación visual requerida"
        if make_sheets:
            from hashlib import sha256
            safe=sha256(rid.encode()).hexdigest()[:12]
            png=output/f"comparison_{safe}.png"
            _sheet(png,rimg,cimg,f"{rid} | {view} | {pose} | {align}")
            info["sheet"]=str(png)
        comparisons.append(info)
    evaluated_ids={x["reference_id"] for x in comparisons}
    if evaluated_ids!=seen_refs:
        issues.append(f"Referencias sin comparación: {sorted(seen_refs-evaluated_ids)}")
    unreviewed=[c["reference_id"] for c in comparisons if c["manual_review"] is None]
    conflicts=[c["reference_id"] for c in comparisons if c["manual_review"] and c["manual_review"]["verdict"]=="ISSUE"]
    all_iou=[x["metrics"]["iou"] for x in comparisons if x["metrics"] is not None]
    result={"status":"INCOMPLETE" if issues else ("REVIEW_REQUIRED" if unreviewed else ("ISSUES_FOUND" if conflicts else "READY_FOR_ADMIN")),
        "automatically_approved":False, "all_references_accounted_for":not issues and evaluated_ids==seen_refs,
        "required_views":required,"references_supplied":len(refs),"references_compared":len(comparisons),
        "issues":issues,"unreviewed_references":unreviewed,"problematic_references":conflicts,
        "worst_mask_iou":min(all_iou) if all_iou else None,
        "comparisons":comparisons,
        "warning":"Todas las referencias deben revisarse visualmente; IoU de máscaras NO demuestra semejanza ni estética."}
    (output/"report.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",help="JSON con referencias y vistas del candidato")
    p.add_argument("--root",default=".",help="Raíz autorizada para leer imágenes")
    p.add_argument("--output",required=True)
    p.add_argument("--no-sheets",action="store_true")
    args=p.parse_args()
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    result=audit(manifest,root=Path(args.root),output=Path(args.output),make_sheets=not args.no_sheets)
    print(json.dumps({k:v for k,v in result.items() if k!="comparisons"},indent=2,ensure_ascii=False))
    return 2 if result["status"]=="INCOMPLETE" else 0


if __name__=="__main__":raise SystemExit(main())
