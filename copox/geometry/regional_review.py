"""COPOX · evaluator regional para CUALQUIER tipo de asset/cassette.

Una regresión en una zona PENDIENTE NO invalida resultados de otra región
sólo si éstos no alteran bytes/geom fuera de su scope. Separar:
  QA técnico local, criterio artístico local y aprobación del modelo global.
Nunca promover modelos automáticamente.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping

@dataclass(frozen=True)
class RegionVerdict:
    region: str
    technical: str
    artistic: str
    modifications_confined: bool
    invariants_preserved: bool
    blockers: tuple[str, ...] = ()

_VALID_TECH={"PASS","FAIL","UNTESTED"}
_VALID_ART={"IMPROVED","REGRESSION","UNCHANGED","REVIEW_REQUIRED"}


def aggregate_regional_review(regions: Mapping[str,RegionVerdict],
                              *,target_region: str,
                              allow_manual_review:bool=True) -> dict:
    if not regions or target_region not in regions:
        raise ValueError("Región objetivo desconocida")
    names=set(regions)
    if len(names)!=len(regions):
        raise ValueError("Regiones duplicadas")
    for key,r in regions.items():
        if key!=r.region or r.technical not in _VALID_TECH or r.artistic not in _VALID_ART:
            raise ValueError(f"Evaluación regional inválida: {key}")
    target=regions[target_region]
    # A risk to untouched or shared data is a blocker, regardless of other
    # regions' status. No cross-region excuse for a rig failure.
    if not target.modifications_confined or not target.invariants_preserved:
        local="REJECTED_OUT_OF_SCOPE_OR_CORE_INVARIANTS"
    elif target.technical=="FAIL" or target.artistic=="REGRESSION":
        local="REGION_REJECTED"
    elif target.technical=="UNTESTED":
        local="REGION_TECHNICAL_TESTS_REQUIRED"
    elif target.artistic=="REVIEW_REQUIRED" or target.artistic=="UNCHANGED":
        local="REGION_READY_FOR_VISUAL_REVIEW" if allow_manual_review else "REGION_PENDING"
    else:
        local="REGION_IMPROVED_PENDING_HUMAN_APPROVAL"
    return {
        "target_region":target_region,
        "local_result":local,
        "global_model_approved":False,
        "auto_merge":False,
        "auto_replace_model":False,
        "accepted_global_version":None,
        "frozen_untouched_sections":sorted(set(regions)-{target_region}),
        "other_regions_never_veto_local_result_if_unchanged":True,
        "hard_global_guards_remain":[
            "source checksums and untouched geometry",
            "rig/animation/material/UV consistency",
            "no out-of-scope changes",
            "no unapproved GLB replacement"
        ],
        "regions":{k:asdict(v) for k,v in regions.items()},
    }
