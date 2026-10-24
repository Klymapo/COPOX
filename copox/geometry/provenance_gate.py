"""Prevalidación de procedencia declarada (NO certificación jurídica de derechos)."""
from __future__ import annotations
import re

class ProvenanceError(ValueError):
    pass

_ALLOWED={"original","cc0","third_party","unknown","derived"}
_SHA=re.compile(r"^[a-fA-F0-9]{64}$")


def evaluate_manifest(manifest: dict) -> dict:
    """Sin suposiciones: deriva el riesgo de TODOS los ancestros de un activo.

    Que una receta de geometría produzca vértices nuevos no limpia una fuente
    que ya procedía de un tercero. Un PASS declara expediente revisable por
    humano, nunca una certificación automática de propiedad intelectual.
    """
    if not isinstance(manifest,dict) or not isinstance(manifest.get("nodes"),list):
        raise ProvenanceError("Se requiere una lista nodes")
    nodes={}
    for row in manifest["nodes"]:
        if not isinstance(row,dict) or not isinstance(row.get("id"),str) or not row["id"]:
            raise ProvenanceError("Cada nodo requiere id")
        if row["id"] in nodes:raise ProvenanceError("ID de procedencia duplicado")
        if row.get("origin") not in _ALLOWED:raise ProvenanceError("Origen desconocido")
        nodes[row["id"]]=row
    root=manifest.get("target")
    if root not in nodes:raise ProvenanceError("target inexistente")
    visited=set();in_stack=set();blockers=[];trail=[]
    def walk(id):
        if id in in_stack:raise ProvenanceError("Ciclo de procedencia")
        if id in visited:return
        if id not in nodes:raise ProvenanceError("Antecesor inexistente: "+id)
        in_stack.add(id)
        row=nodes[id]
        trail.append(id)
        if row["origin"] in {"third_party","unknown"}:
            blockers.append({"id":id,"reason":row["origin"]})
        if row["origin"] in {"original","cc0"}:
            if not row.get("rights_evidence"):
                blockers.append({"id":id,"reason":"missing_rights_evidence"})
        if row["origin"]=="derived":
            parents=row.get("parents")
            if not isinstance(parents,list) or not parents:
                blockers.append({"id":id,"reason":"derived_without_parents"})
            else:
                for parent in parents:walk(parent)
        if row.get("file"):
            if not isinstance(row.get("sha256"),str) or not _SHA.fullmatch(row["sha256"]):
                blockers.append({"id":id,"reason":"missing_or_invalid_sha256"})
        visited.add(id)
        in_stack.remove(id)
    walk(root)
    return {
        "status":"ORIGIN_REVIEW_READY" if not blockers else "PROVENANCE_BLOCKED",
        "independent_verified":False,
        "release_approved":False,
        "evaluated_nodes":trail,"blockers":blockers,
        "note":"Sólo evalúa declaraciones y trazabilidad; verificar legalidad y licencias manualmente."
    }
