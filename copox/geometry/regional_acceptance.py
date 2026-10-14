"""Regional acceptance: local success must not be vetoed by unrelated regions."""
from dataclasses import dataclass
from typing import Mapping

REGIONS=("nuca","craneo","rostro","ojos","orejas","cabello","cuello",
         "torso","brazo_izquierdo","brazo_derecho","mano_izquierda",
         "mano_derecha","pierna_izquierda","pierna_derecha",
         "pie_izquierdo","pie_derecho","ropa","accesorios")

@dataclass(frozen=True)
class RegionVerdict:
    region: str
    local_tests_pass: bool
    protected_neighbors_unchanged: bool
    rig_attributes_preserved: bool
    evidence_complete: bool
    notes: str = ""

    @property
    def status(self):
        if not self.local_tests_pass:
            return "REJECTED_LOCAL"
        if not self.protected_neighbors_unchanged or not self.rig_attributes_preserved:
            return "BLOCKED_INTEGRATION"
        if not self.evidence_complete:
            return "NEEDS_EVIDENCE"
        return "ACCEPTED_LOCAL"


def evaluate_regions(verdicts: Mapping[str, RegionVerdict]):
    unknown=set(verdicts)-set(REGIONS)
    if unknown:
        raise ValueError(f"Unknown regions: {sorted(unknown)}")
    results={}
    for name,verdict in verdicts.items():
        if name!=verdict.region:
            raise ValueError(f"Region mismatch: {name}")
        results[name]={"status":verdict.status,"notes":verdict.notes}
    return {
        "regions":results,
        "locally_accepted":sorted(k for k,v in results.items() if v["status"]=="ACCEPTED_LOCAL"),
        "pending":sorted(set(REGIONS)-set(verdicts)),
        "global_approval":False,
        "promotion_allowed":False,
        "rule":"Unrelated regional failures never invalidate locally accepted work; integration requires separate approval",
    }
