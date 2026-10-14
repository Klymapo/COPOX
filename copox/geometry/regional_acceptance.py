"""COPOX · Gates por región: no usar errores ajenos para vetar progreso local.

La revisión ARTÍSTICA de una región, la integridad de sus vecinos y la
autorización de promoción son decisiones separadas. Ningún gate local
puede fusionar ni sustituir archivos.
"""
from dataclasses import dataclass
from typing import Mapping

REGIONS = (
    "nuca", "craneo", "rostro", "ojos", "orejas", "cabello", "cuello",
    "torso", "brazo_izquierdo", "brazo_derecho", "mano_izquierda",
    "mano_derecha", "pierna_izquierda", "pierna_derecha",
    "pie_izquierdo", "pie_derecho", "ropa", "accesorios",
)


@dataclass(frozen=True)
class RegionVerdict:
    region: str
    local_tests_pass: bool
    protected_neighbors_unchanged: bool
    rig_attributes_preserved: bool
    evidence_complete: bool
    notes: str = ""
    artistic_review_completed: bool = False
    artistic_review_approved: bool = False
    integration_tests_pass: bool = False

    @property
    def status(self):
        if not self.local_tests_pass:
            return "REJECTED_LOCAL"
        if not self.protected_neighbors_unchanged or not self.rig_attributes_preserved:
            return "BLOCKED_INTEGRATION"
        if not self.evidence_complete:
            return "NEEDS_EVIDENCE"
        if self.artistic_review_completed and not self.artistic_review_approved:
            return "REJECTED_VISUAL_LOCAL"
        if not self.artistic_review_completed:
            return "PASS_LOCAL_TECHNICAL"
        return "ACCEPTED_LOCAL"

    @property
    def eligible_for_integration_review(self):
        return self.status == "ACCEPTED_LOCAL" and self.integration_tests_pass


def evaluate_regions(verdicts: Mapping[str, RegionVerdict]):
    unknown = set(verdicts) - set(REGIONS)
    if unknown:
        raise ValueError(f"Unknown regions: {sorted(unknown)}")
    results = {}
    for name, verdict in verdicts.items():
        if name != verdict.region:
            raise ValueError(f"Region mismatch: {name}")
        if verdict.artistic_review_approved and not verdict.artistic_review_completed:
            raise ValueError("Artistic approval requires a completed review")
        results[name] = {
            "status": verdict.status,
            "local_tests_pass": verdict.local_tests_pass,
            "protected_neighbors_unchanged": verdict.protected_neighbors_unchanged,
            "rig_attributes_preserved": verdict.rig_attributes_preserved,
            "evidence_complete": verdict.evidence_complete,
            "artistic_review_completed": verdict.artistic_review_completed,
            "artistic_review_approved": verdict.artistic_review_approved,
            "integration_tests_pass": verdict.integration_tests_pass,
            "eligible_for_integration_review": verdict.eligible_for_integration_review,
            "notes": verdict.notes,
        }
    return {
        "regions": results,
        "accepted_local": sorted(k for k, v in results.items()
                                 if v["status"] == "ACCEPTED_LOCAL"),
        "locally_accepted": sorted(k for k, v in results.items()
                                   if v["status"] == "ACCEPTED_LOCAL"),
        "technical_pass": sorted(k for k, v in results.items()
                                 if v["status"] in ("PASS_LOCAL_TECHNICAL", "ACCEPTED_LOCAL")),
        "integration_review_ready": sorted(k for k, v in results.items()
                                           if v["eligible_for_integration_review"]),
        "pending": sorted(set(REGIONS) - set(verdicts)),
        "global_approval": False,
        "promotion_allowed": False,
        "rule": (
            "A locally successful part remains viable regardless of failures "
            "elsewhere. Local technical QA, artistic approval, cross-region "
            "integration, and authorization to replace the baseline are "
            "four distinct gates."
        ),
    }
