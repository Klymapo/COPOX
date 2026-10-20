"""publicar-version · un paso para publicar un GLB (19 oct 2026).

Antes eran ~8 pasos a mano por versión (≈44 versiones; ULTIMA.txt se corrigió 2 veces). Hace, en orden:
  1. SHA-256 del GLB; NUNCA sobrescribe un archivo distinto en copox-modelos (versión nueva = nombre nuevo).
  2. copia a copox-modelos/<carpeta>/<NOMBRE>.glb, agrega a SHA256SUMS y antepone la línea en ULTIMA.txt
     (estado + fecha + nota + "Anterior: …" con la cadena previa).
  3. copia la evidencia CHXP (png/gif/json) a la rama capturas: capturas/<fecha>/<slug>/.
  4. escribe la ficha docs/fichas/<NOMBRE>.md en COPOX (pedido, resultado, SHA, veredicto CHXP, fallas).
  5. commit + push de los tres repos (con --push).
  6. imprime la línea lista para el «Registro de cambios» de la Memoria maestra de Drive (el script no toca Drive;
     la skill la pega con el conector de Google Docs).

Uso:
  python -m copox.publicar GLB --carpeta theo --nombre THEO_VESTIDO_V5 --nota "qué cambió" \
      [--estado "SIN APROBAR"] [--pedido "lo que pidió Admin"] [--chxp DIR_CHXP] [--push] [--simular]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import os
import shutil
import subprocess

from . import entorno

FIRMA = ("\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
         "Claude-Session: https://claude.ai/code/session_01P7nVUdh4MuWb163YPHK6MA")


def _git(repo, *args, simular=False):
    if simular:
        return f"(simulado) git {' '.join(args)}"
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if r.returncode != 0 and "nothing to commit" not in r.stdout + r.stderr:
        raise RuntimeError(f"git {' '.join(args)} en {repo}: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def _veredicto(chxp):
    if not chxp:
        return None
    a = glob.glob(os.path.join(chxp, "*_AUDITORIA.json"))
    if not a:
        return None
    aud = json.load(open(a[0]))
    return {"veredicto": aud["veredicto"], "pass": aud["pass"], "fail": aud["fail"], "na": aud["na"],
            "fallas": [f"{f['id']} ({f['medida']})" for f in aud["revisiones"] if f["veredicto"] == "FAIL"]}


def publicar(glb, carpeta, nombre, nota, estado="SIN APROBAR", pedido="", chxp=None, push=False, simular=False):
    e = entorno.estado()
    if not e["copox_modelos"]:
        raise entorno.EntornoIncompleto("no encuentro copox-modelos (COPOX_MODELOS)")
    nombre = nombre[:-4] if nombre.lower().endswith(".glb") else nombre
    hoy = _dt.date.today().isoformat()
    sha = entorno.sha256(glb)
    destino_dir = os.path.join(entorno.MODELOS, carpeta)
    destino = os.path.join(destino_dir, nombre + ".glb")
    if os.path.exists(destino) and entorno.sha256(destino) != sha:
        raise FileExistsError(f"{destino} ya existe con otro contenido: una versión nueva lleva NOMBRE nuevo")
    if os.path.abspath(destino) == os.path.abspath(entorno.BASE):
        raise PermissionError("la base congelada no se publica encima")
    log = {"glb": nombre + ".glb", "sha256": sha, "carpeta": carpeta, "estado": estado}
    ver = _veredicto(chxp)
    if not simular:
        os.makedirs(destino_dir, exist_ok=True)
        if not os.path.exists(destino):
            shutil.copy2(glb, destino)
        sums = os.path.join(destino_dir, "SHA256SUMS")
        linea_sum = f"{sha}  {nombre}.glb\n"
        if not (os.path.exists(sums) and linea_sum in open(sums).read()):
            with open(sums, "a") as f:
                f.write(linea_sum)
        ult = os.path.join(destino_dir, "ULTIMA.txt")
        previo = open(ult).read().strip() if os.path.exists(ult) else ""
        chx = f" CHXP V3 {ver['veredicto']} {ver['pass']}/{ver['fail']}" + (f" ({', '.join(ver['fallas'])})" if ver and ver["fallas"] else "") if ver else ""
        linea = f"{nombre}.glb {sha} {estado} ({hoy}): {nota}.{chx}"
        if not previo.startswith(f"{nombre}.glb {sha}"):
            with open(ult, "w") as f:
                f.write(linea + (f" Anterior: {previo}" if previo else "") + "\n")
    _git(entorno.MODELOS, "add", "-A", carpeta, simular=simular)
    _git(entorno.MODELOS, "commit", "-qm", f"{nombre} — {estado}: {nota}{FIRMA}", simular=simular)
    log["commit_modelos"] = _git(entorno.MODELOS, "rev-parse", "--short", "HEAD", simular=simular)

    if chxp and e["capturas"]:
        slug = nombre.lower()
        dcap = os.path.join(entorno.CAPTURAS, "capturas", hoy, slug)
        if not simular:
            os.makedirs(dcap, exist_ok=True)
            for ext in ("png", "gif", "json"):
                for f in glob.glob(os.path.join(chxp, f"*.{ext}")):
                    shutil.copy2(f, dcap)
        _git(entorno.CAPTURAS, "add", "-A", simular=simular)
        _git(entorno.CAPTURAS, "commit", "-qm", f"Capturas CHXP V3 {nombre}{FIRMA}", simular=simular)
        log["commit_capturas"] = _git(entorno.CAPTURAS, "rev-parse", "--short", "HEAD", simular=simular)
        log["capturas"] = f"capturas/{hoy}/{slug}"

    ficha = os.path.join(entorno.RAIZ, "docs", "fichas", nombre + ".md")
    if not simular:
        os.makedirs(os.path.dirname(ficha), exist_ok=True)
        with open(ficha, "w") as f:
            f.write(f"# {nombre}\n\n- Fecha: {hoy}\n- Estado: **{estado}**\n- SHA-256: `{sha}`\n"
                    f"- Archivo: `copox-modelos/{carpeta}/{nombre}.glb`\n")
            if pedido:
                f.write(f"- Pedido de Admin: {pedido}\n")
            f.write(f"- Qué cambió: {nota}\n")
            if ver:
                f.write(f"- CHXP V3: {ver['veredicto']} ({ver['pass']} PASS / {ver['fail']} FAIL / {ver['na']} N-A)\n")
                for x in ver["fallas"]:
                    f.write(f"  - FAIL {x}\n")
            if log.get("capturas"):
                f.write(f"- Evidencia: rama `capturas`, `{log['capturas']}`\n")
    _git(entorno.RAIZ, "add", ficha, simular=simular)
    _git(entorno.RAIZ, "commit", "-qm", f"Ficha {nombre} ({estado}){FIRMA}", simular=simular)
    log["commit_copox"] = _git(entorno.RAIZ, "rev-parse", "--short", "HEAD", simular=simular)

    if push:
        for repo in (entorno.MODELOS, entorno.CAPTURAS if log.get("capturas") else None, entorno.RAIZ):
            if repo:
                _git(repo, "push", "-q", simular=simular)
    log["drive_linea"] = (f"{hoy} — {nombre} ({estado}): {nota}."
                          + (f" CHXP V3 {ver['veredicto']} {ver['pass']}/{ver['fail']}." if ver else "")
                          + f" copox-modelos {log['commit_modelos']} ({carpeta}/{nombre}.glb {sha[:8]}…)"
                          + (f", capturas {log['commit_capturas']} ({log['capturas']})" if log.get("capturas") else "")
                          + f", COPOX {log['commit_copox']} (docs/fichas/{nombre}.md).")
    return log


def main():
    ap = argparse.ArgumentParser(description="Publica un GLB: copox-modelos + capturas + ficha + línea para Drive")
    ap.add_argument("glb")
    ap.add_argument("--carpeta", required=True)
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--nota", required=True)
    ap.add_argument("--estado", default="SIN APROBAR")
    ap.add_argument("--pedido", default="")
    ap.add_argument("--chxp")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()
    print(json.dumps(publicar(a.glb, a.carpeta, a.nombre, a.nota, a.estado, a.pedido, a.chxp, a.push, a.simular),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
