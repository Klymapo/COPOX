"""Puente entre Visual Critic y las operaciones geométricas COPOX.

No adivina la intención artística, no inspecciona imágenes con IA y no escribe
GLB. Selecciona una *hipótesis verificable* sólo si el reporte visual cubre TODAS
las referencias y existe diagnóstico geométrico registrado por anomalía.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


OPERATORS = {
    "surface_bulge": ("Scully", "copox.geometry.surface_sculpt.flatten_surface"),
    "surface_fragments": ("Anatomic Cut", "copox.geometry.anatomic_cut.cut_plane"),
    "open_seam": ("Surface Stitch", "copox.geometry.surface_stitch.stitch_parts"),
}
PRIORITY = {"Anatomic Cut": 0, "Surface Stitch": 1, "Scully": 2}


def _number(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return False
    return math.isfinite(value) and (value > 0 if positive else value >= 0)


def _geometry_ready(kind: str, data: dict) -> tuple[bool, list[str], dict]:
    """Fail closed: the plan points to tested callable, not arbitrary code."""
    blockers = []
    args = {}
    if kind == "surface_bulge":
        if not _number(data.get("signed_excess_mm"), positive=True):
            blockers.append("missing_positive_surface_excess_mm")
        if data.get("region_topology_continuous") is not True:
            blockers.append("topology_not_verified_continuous")
        plane=data.get("flatten")
        if not isinstance(plane, dict):
            blockers.append("missing_scully_parameters")
        else:
            mandatory=("direction","target_projection","region_center","region_radii",
                       "strength","falloff","max_displacement")
            if any(k not in plane for k in mandatory):
                blockers.append("incomplete_scully_parameters")
            else:
                a=plane
                vectors=("direction","region_center","region_radii")
                if any(not isinstance(a[k], list) or len(a[k])!=3 or not all(isinstance(t,(int,float)) and not isinstance(t,bool) and math.isfinite(t) for t in a[k]) for k in vectors):
                    blockers.append("invalid_vectors")
                elif not all(t>0 for t in a["region_radii"]) or sum(t*t for t in a["direction"])<1e-15:
                    blockers.append("invalid_direction_or_radii")
                if not (_number(a["max_displacement"],positive=True) and
                        isinstance(a["target_projection"],(int,float)) and not isinstance(a["target_projection"],bool) and math.isfinite(a["target_projection"]) and
                        _number(a["strength"]) and 0<=a["strength"]<=1 and
                        _number(a["falloff"],positive=True) and 0<a["falloff"]<=1):
                    blockers.append("invalid_scully_budget")
                args={"parameters":a,"requires_vertex_protection_mask":True,
                      "recalculate_normals":True}
    elif kind == "surface_fragments":
        components=data.get("disconnected_components")
        tris=data.get("floating_triangles")
        if not ((isinstance(components,int) and not isinstance(components,bool) and components>1) or
                (isinstance(tris,int) and not isinstance(tris,bool) and tris>0)):
            blockers.append("no_measured_fragments")
        if data.get("safe_cut_plane_measured") is not True:
            blockers.append("safe_cut_plane_not_measured")
        if data.get("protected_faces_mask_ready") is not True:
            blockers.append("protected_faces_mask_missing")
        if data.get("skin_attributes_supported") is not True:
            blockers.append("skin_uv_or_morph_unsupported")
        plane=data.get("cut_plane")
        if not isinstance(plane,dict) or set(("normal","offset"))-set(plane):
            blockers.append("cut_plane_not_defined")
        elif (not isinstance(plane["normal"],list) or len(plane["normal"])!=3 or
              not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in plane["normal"]) or
              sum(v*v for v in plane["normal"])<1e-15 or
              not isinstance(plane["offset"],(int,float)) or isinstance(plane["offset"],bool) or not math.isfinite(plane["offset"])):
            blockers.append("cut_plane_invalid")
        else:
            args={"plane":plane,"requires_protected_faces_mask":True,
                  "requires_attribute_transfer":True}
    elif kind == "open_seam":
        boundary=data.get("target_boundary_edges")
        counts=data.get("loop_vertex_counts")
        if not isinstance(boundary,int) or isinstance(boundary,bool) or boundary<=0:
            blockers.append("no_measured_open_seam")
        if not isinstance(counts,list) or len(counts)!=2 or any(type(n)!=int or n<3 for n in counts) or counts[0]!=counts[1]:
            blockers.append("incompatible_loop_cardinality")
        if data.get("loop_winding_valid") is not True:
            blockers.append("loop_winding_not_verified")
        if data.get("attributes_compatible") is not True:
            blockers.append("incompatible_uv_material_or_skin_attributes")
        if data.get("morph_targets_present") is not False:
            blockers.append("morph_target_transfer_not_supported")
        if not _number(data.get("max_gap_m"),positive=True):
            blockers.append("missing_max_gap")
        args={"max_gap_m":data.get("max_gap_m"),"requires_shared_index_space":True,
              "requires_glb_reimport_validation":True,
              "requires_self_intersection_validation":True}
    else:
        blockers.append("unsupported_anomaly_kind")
    return not blockers, blockers, args


def propose(visual_report: dict, geometry_diagnostics: dict) -> dict:
    """Returns a reproducible operator plan; no mutations or promotions."""
    result={"status":"BLOCKED","approved":False,"execute_automatically":False,
            "source":"Visual Critic × COPOX Geometry Kernel",
            "recommendations":[],"issues":[],"priority_order":["Anatomic Cut","Surface Stitch","Scully"]}
    if not isinstance(visual_report,dict) or not isinstance(geometry_diagnostics,dict):
        result["issues"].append("invalid_report_types")
        return result
    if visual_report.get("status")=="INCOMPLETE" or not visual_report.get("all_references_accounted_for"):
        result["issues"].append("reference_coverage_incomplete")
        return result
    comparisons=visual_report.get("comparisons")
    if not isinstance(comparisons,list) or len(comparisons)!=visual_report.get("references_supplied"):
        result["issues"].append("comparison_count_mismatch")
        return result
    reference_ids=[c.get("reference_id") for c in comparisons if isinstance(c,dict)]
    if len(reference_ids)!=len(set(reference_ids)) or any(not x for x in reference_ids):
        result["issues"].append("duplicate_or_invalid_references")
        return result
    expected=set(reference_ids)
    anomalies=visual_report.get("anomaly_cross_view_matrix")
    if not isinstance(anomalies,list) or not anomalies:
        result.update(status="NO_ANOMALIES_REPORTED", issues=["nothing_to_diagnose"])
        return result
    if not isinstance(geometry_diagnostics.get("anomalies"),dict):
        result["issues"].append("missing_geometry_diagnostics")
        return result
    for anomaly in anomalies:
        if not isinstance(anomaly,dict) or not anomaly.get("id"):
            result["issues"].append("invalid_anomaly")
            continue
        aid=anomaly["id"]
        groups=anomaly.get("cross_reference_evidence")
        if not isinstance(groups,dict):
            result["issues"].append(f"{aid}:missing_cross_view_evidence")
            continue
        allowed={"supports","contradicts","not_visible","uncertain"}
        if set(groups)!=allowed or not all(isinstance(groups[k],list) for k in allowed):
            result["issues"].append(f"{aid}:invalid_evidence_groups")
            continue
        covered=sum((groups[k] for k in allowed),[])
        if len(covered)!=len(expected) or set(covered)!=expected:
            result["issues"].append(f"{aid}:not_all_references_checked")
            continue
        matches=groups["supports"]
        contradictory=groups["contradicts"]
        if not matches:
            result["recommendations"].append({"anomaly_id":aid,"state":"INSUFFICIENT_EVIDENCE",
                 "blockers":["no_reference_support"],"reference_coverage":groups})
            continue
        measurements=geometry_diagnostics["anomalies"].get(aid)
        if not isinstance(measurements,dict):
            result["recommendations"].append({"anomaly_id":aid,"state":"DIAGNOSIS_REQUIRED",
                "blockers":["no_measured_mesh_diagnostics"],"reference_coverage":groups})
            continue
        kind=measurements.get("kind")
        op,callable_name=OPERATORS.get(kind,("RESEARCH_REQUIRED",None))
        ready, blockers, arguments=_geometry_ready(kind,measurements)
        if contradictory:
            blockers.append("conflicting_reference_views")
        # Un reporte sin medición reproducible sólo debe producir hipótesis,
        # nunca un plan listo para probar automáticamente.
        provenance=measurements.get("measurement_provenance")
        if not isinstance(provenance,dict) or not isinstance(provenance.get("source_sha256"),str) or len(provenance.get("source_sha256",""))!=64 or any(c not in "0123456789abcdefABCDEF" for c in provenance.get("source_sha256","")) or not provenance.get("measurement_method") or not provenance.get("coordinate_system"):
            blockers.append("missing_measurement_provenance")
        # No manual review means a geometrical hypothesis, not permission to modify.
        unreviewed=[c.get("reference_id") for c in comparisons if c.get("manual_review") is None]
        status="PLAN_READY_FOR_SANDBOX" if ready and not contradictory else "RESEARCH_REQUIRED"
        if blockers:
            status="RESEARCH_REQUIRED"
        result["recommendations"].append({
            "anomaly_id":aid,"region":anomaly.get("region"),
            "kind":kind,"operator":op,"callable":callable_name,
            "state":status,"blockers":blockers,"arguments":arguments,
            "reference_coverage":groups,
            "independent_visual_review_pending":bool(unreviewed),
            "verification":["render_all_references","per_view_difference_map",
                            "protect_all_features","cheap_geometry_preflight",
                            "rig_and_animation_tests","Godot_and_Admin_review"],
            "auto_apply":False})
    result["recommendations"].sort(key=lambda r: (PRIORITY.get(r.get("operator"),99),str(r.get("anomaly_id"))))
    result["status"]="PLANS_FOR_SANDBOX" if (result["recommendations"] and
                          not result["issues"] and
                          all(r.get("state")=="PLAN_READY_FOR_SANDBOX" for r in result["recommendations"])) else "RESEARCH_REQUIRED"
    return result


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--visual-report",required=True)
    p.add_argument("--geometry-diagnostics",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    visual=json.loads(Path(a.visual_report).read_text(encoding="utf-8"))
    geo=json.loads(Path(a.geometry_diagnostics).read_text(encoding="utf-8"))
    report=propose(visual,geo)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"recommendations":len(report["recommendations"]),
                      "issues":report["issues"]},ensure_ascii=False))
    return 0 if report["status"] in {"PLANS_FOR_SANDBOX","NO_ANOMALIES_REPORTED"} else 2


if __name__=="__main__":
    raise SystemExit(main())
