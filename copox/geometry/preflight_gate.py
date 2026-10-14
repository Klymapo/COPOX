#!/usr/bin/env python3
"""GATE A (barato): filtros estructurales/visuales ANTES de poses y renders profundos.

Lee metricas medidas por adaptadores del cassette; NO evalua GLBs directamente.
No certifica que una malla este soldada: la metrica debe venir de una prueba real
de adyacencia y no de un solape geométrico. No promueve modelos.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path


def _require_number(doc: dict, path: str) -> float:
    node = doc
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            raise ValueError(f"Falta metrica {path}; no se permite pasar por defecto")
        node = node[key]
    if isinstance(node, bool) or not isinstance(node, (int, float)) or not math.isfinite(float(node)):
        raise ValueError(f"Metrica invalida {path}")
    return float(node)


def _require_bool(doc: dict, path: str) -> bool:
    node = doc
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            raise ValueError(f"Falta metrica {path}")
        node = node[key]
    if not isinstance(node, bool):
        raise ValueError(f"Metrica booleana invalida {path}")
    return node


def evaluate(metrics: dict, config: dict) -> dict:
    failures = []
    checks = {}
    def check(name: str, okay: bool, detail: str):
        checks[name] = {"passed": okay, "detail": detail}
        if not okay:
            failures.append(name)

    # Las convenciones deben coincidir con la receta; no asumir ejes Z-up ni escala.
    axes = metrics.get("coordinates", {})
    expected = config.get("coordinates", {})
    check("CoordinateContract", axes == expected and bool(expected),
          f"recibido={axes}; requerido={expected}")

    rig = metrics.get("rig", {})
    check("RigBytes", _require_bool(metrics,"rig.original_animation_skin_bytes_equal"),
          "Buffers de animación y skin sin alteraciones")
    check("BodyFrozen", _require_bool(metrics,"rig.frozen_primitives_equal"),
          "Primitivas fuera del foco intactas")
    check("FacialGuard",
          _require_number(metrics,"protected.missing_face_triangles") == 0 and
          _require_number(metrics,"protected.missing_ear_triangles") == 0,
          "Triangulos faciales y auriculares protegidos intactos")

    topology = metrics.get("topology", {})
    check("NoNewNonManifold", _require_number(metrics,"topology.new_nonmanifold_edges") == 0,
          "Sin nuevas aristas no manifold")
    if config.get("requires_connected_seam", False):
        check("SeamConnected", _require_bool(metrics,"topology.seam_connected"),
              "Una superposicion NO cuenta como soldadura")
    if config.get("requires_boundary_reduction", False):
        before = _require_number(metrics,"topology.target_boundary_edges_before")
        after = _require_number(metrics,"topology.target_boundary_edges_after")
        check("TargetBoundaryImproved", after < before, f"{before:g} -> {after:g} bordes")

    vis = metrics.get("visual", {})
    min_diff = float(config.get("min_target_visible_change_pct", 0.0))
    min_gain = float(config.get("min_target_improvement_pp", 0.0))
    max_loss = float(config.get("max_frozen_region_loss_pp", 0.0))
    delta = _require_number(metrics,"visual.target_visible_change_pct")
    gain = _require_number(metrics,"visual.target_improvement_pp")
    loss = _require_number(metrics,"visual.worst_frozen_region_loss_pp")
    check("VisibleDifference",delta >= min_diff,f"{delta:g}% >= {min_diff:g}%")
    check("TargetImprovement",gain >= min_gain,f"{gain:g} pp >= {min_gain:g} pp")
    check("RegressionGuard",loss <= max_loss,f"{loss:g} pp <= {max_loss:g} pp")

    return {"status": "DEEP_ELIGIBLE" if not failures else "REJECTED_EARLY",
            "can_promote": False,
            "must_render_deep": not failures,
            "failures": failures, "checks": checks,
            "notes": [
                "Las metricas visuales deben medirse en regiones concretas y frente a una referencia aprobada",
                "DEEP_ELIGIBLE no significa aprobado; falta auditoria profunda y revision humana"
            ]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metrics",required=True)
    p.add_argument("--config",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        result=evaluate(json.loads(Path(a.metrics).read_text()),json.loads(Path(a.config).read_text()))
        code=0
    except (ValueError,KeyError,TypeError) as exc:
        result={"status":"RESEARCH_REQUIRED","can_promote":False,"must_render_deep":False,
                "failures":["MissingOrInvalidMetrics"],"reason":str(exc)}
        code=2
    out=Path(a.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return code

if __name__=="__main__":
    raise SystemExit(main())
