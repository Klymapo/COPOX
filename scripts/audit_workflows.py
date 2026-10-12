"""Inventario local de disparadores de GitHub Actions sin servicios externos.

Uso: python scripts/audit_workflows.py
      python scripts/audit_workflows.py --fail-on-schedule

Lee solo YAML fuente; NO ejecuta workflows ni modifica assets.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def read_triggers(source: str) -> list[str]:
    """Extrae nombres de eventos bajo el bloque YAML raíz on:.

    No analiza la expresión entera del YAML; es un inventario conservador.
    """
    events = []
    inside_on = False
    for raw in source.splitlines():
        line = raw.partition("#")[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")):
            inside_on = line in ("on:", "on: {}")
            if line.startswith("on:") and line not in ("on:", "on: {}"):
                events.append(line[3:].strip())
            continue
        if inside_on and line.startswith("  ") and not line.startswith("    "):
            label = line.strip().split(":", 1)[0]
            if label:
                events.append(label)
    return events


def inventory() -> list[dict]:
    result = []
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        events = sorted(set(read_triggers(path.read_text(encoding="utf-8"))))
        result.append({
            "path": path.relative_to(ROOT).as_posix(),
            "events": events,
            "scheduled": "schedule" in events,
            "manual": "workflow_dispatch" in events,
        })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-schedule", action="store_true")
    args = parser.parse_args()
    entries = inventory()
    scheduled = [item["path"] for item in entries if item["scheduled"]]
    print(json.dumps({
        "workflows": len(entries),
        "scheduled": scheduled,
        "manual_only": sum(item["events"] == ["workflow_dispatch"] for item in entries),
        "unknown_triggers": [x["path"] for x in entries if not x["events"]],
    }, ensure_ascii=False, indent=2))
    if args.fail_on_schedule and scheduled:
        print("Revisión humana obligatoria: se detectó al menos una programación.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
