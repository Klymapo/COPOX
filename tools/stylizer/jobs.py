"""Persistent single-worker queue shared by every browser using this app."""

import json
import logging
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from filelock import FileLock, Timeout

from config import redact
from mesh_service import PROVIDERS, validate_glb
from pipeline_core import copy_image, run_pipeline
from prepare_godot import prepare_asset, validate_options

LOGGER = logging.getLogger("stylizer.jobs")
ACTIVE = ("queued", "running")


def now():
    return datetime.now(timezone.utc).isoformat()


class JobManager:
    def __init__(self, data_dir, output_dir, *, start=True):
        self.data_dir = Path(data_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.database = self.data_dir / "jobs.sqlite3"
        self.lock = FileLock(str(self.data_dir / "worker.lock"), thread_local=False)
        try:
            self.lock.acquire(timeout=0)
        except Timeout as error:
            raise RuntimeError("Ya hay otra instancia de Stylizer usando esta carpeta de datos.") from error
        self.wake = threading.Event()
        self.stop = threading.Event()
        self.thread = None
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL,
                status TEXT NOT NULL, stage TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, request_json TEXT NOT NULL,
                result_json TEXT, error TEXT)""")
            connection.execute("UPDATE jobs SET status='interrupted', stage='La aplicación se cerró durante la tarea; puedes reintentar.', updated_at=? WHERE status='running'", (now(),))
        self.import_runs()
        if start:
            self.thread = threading.Thread(target=self._loop, name="stylizer-worker", daemon=True)
            self.thread.start()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.database, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def import_runs(self):
        # Import generations from the earlier CLI/UI without taking over active jobs.
        with self.connect() as connection:
            for path in self.output_dir.glob("*/manifest.json"):
                try:
                    run = json.loads(path.read_text(encoding="utf-8"))
                    if Path(run["directory"]).resolve() != path.parent.resolve():
                        continue
                    status = run.get("status", "interrupted")
                    if status not in {"completed", "failed"}:
                        status = "interrupted"
                    connection.execute("INSERT OR IGNORE INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (run["id"], "godot" if run.get("source") == "godot" else "generation",
                         run.get("idea") or "Generación guardada", status, run.get("stage", status),
                         run.get("created_at", now()), run.get("updated_at", now()), "{}", json.dumps(run), run.get("error")))
                except (OSError, ValueError, KeyError, TypeError):
                    LOGGER.warning("Se omitió un registro de generación ilegible.")

    @staticmethod
    def decode(row):
        if row is None:
            return None
        value = dict(row)
        value["request"] = json.loads(value.pop("request_json"))
        value["result"] = json.loads(value.pop("result_json") or "null")
        return value

    def get(self, identifier):
        with self.connect() as connection:
            return self.decode(connection.execute("SELECT * FROM jobs WHERE id=?", (identifier,)).fetchone())

    def recent(self, limit=50):
        with self.connect() as connection:
            return [self.decode(row) for row in connection.execute("SELECT * FROM jobs ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,))]

    def _insert(self, identifier, kind, label, payload):
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0] >= 20:
                raise ValueError("Ya hay 20 tareas pendientes. Espera a que termine alguna.")
            connection.execute("INSERT INTO jobs VALUES (?, ?, ?, 'queued', 'En cola', ?, ?, ?, NULL, NULL)",
                               (identifier, kind, label[:100], now(), now(), json.dumps(payload)))
        self.wake.set()
        return identifier

    def submit_generation(self, *, idea=None, image_path=None, provider="auto"):
        idea = (idea or "").strip()
        if bool(idea) == bool(image_path) or provider not in PROVIDERS:
            raise ValueError("Elige una idea o una imagen y un proveedor válido.")
        if len(idea) > 4000:
            raise ValueError("Limita la idea a 4000 caracteres.")
        identifier = uuid4().hex
        upload_dir = self.data_dir / "inputs" / identifier
        try:
            image = None
            if image_path:
                upload_dir.mkdir(parents=True)
                image = upload_dir / "input.png"
                copy_image(image_path, image)
            return self._insert(identifier, "generation", idea or "Desde imagen", {
                "idea": idea or None, "image_path": str(image) if image else None, "provider": provider})
        except Exception:
            shutil.rmtree(upload_dir, ignore_errors=True)
            raise

    def submit_godot(self, *, source, height=1.8, yaw=0, triangle_limit=0, source_image=None):
        validate_options(height, yaw, triangle_limit)
        validate_glb(source)
        identifier = uuid4().hex
        upload_dir = self.data_dir / "inputs" / identifier
        upload_dir.mkdir(parents=True)
        try:
            shutil.copyfile(source, upload_dir / "input.glb")
            image = None
            if source_image:
                image = upload_dir / "input.png"
                copy_image(source_image, image)
            return self._insert(identifier, "godot", "Preparar para Godot", {
                "source": str(upload_dir / "input.glb"), "height": float(height), "yaw": float(yaw),
                "triangle_limit": int(triangle_limit), "source_image": str(image) if image else None})
        except Exception:
            shutil.rmtree(upload_dir, ignore_errors=True)
            raise

    def retry(self, identifier, provider="auto"):
        previous = self.get(identifier)
        if not previous or previous["status"] in ACTIVE:
            raise ValueError("Selecciona una tarea terminada o interrumpida.")
        if previous["kind"] == "godot":
            payload = previous["request"]
            if not payload:
                raise ValueError("Vuelve a cargar el GLB de origen para esta tarea anterior.")
            return self.submit_godot(**payload)
        run = previous.get("result") or {}
        image = run.get("image") or previous["request"].get("image_path")
        if image and Path(image).is_file():
            return self.submit_generation(image_path=image, provider=provider)
        idea = previous["request"].get("idea")
        if idea:
            return self.submit_generation(idea=idea, provider=provider)
        raise ValueError("No se encontró la entrada original; vuelve a cargarla.")

    def _update(self, identifier, *, stage=None, result=None, status=None, error=None):
        with self.connect() as connection:
            connection.execute("UPDATE jobs SET stage=COALESCE(?,stage), result_json=COALESCE(?,result_json), status=COALESCE(?,status), error=?, updated_at=? WHERE id=?",
                               (redact(stage) if stage else None, json.dumps(result) if result else None, status, redact(error) if error else None, now(), identifier))

    def _next(self):
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created_at, rowid LIMIT 1").fetchone()
            if row:
                connection.execute("UPDATE jobs SET status='running', stage='Iniciando', updated_at=? WHERE id=?", (now(), row["id"]))
            return self.decode(row)

    def _loop(self):
        while not self.stop.is_set():
            job = self._next()
            if not job:
                self.wake.wait(1)
                self.wake.clear()
                continue
            identifier = job["id"]
            try:
                if job["kind"] == "generation":
                    result = run_pipeline(**job["request"], output_root=self.output_dir, run_id=identifier,
                        on_update=lambda run: self._update(identifier, stage=run.get("stage"), result=run))
                else:
                    result = prepare_asset(**job["request"], output_dir=self.output_dir / identifier,
                        progress=lambda stage: self._update(identifier, stage=stage))
                self._update(identifier, status=result["status"], stage="Completado" if result["status"] == "completed" else "Falló la tarea",
                             result=result, error=result.get("error"))
            except Exception as error:
                LOGGER.error("La tarea %s falló: %s", identifier, redact(error))
                self._update(identifier, status="failed", stage="Falló la tarea", error=error)

    def close(self):
        self.stop.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=5)
        if not self.thread or not self.thread.is_alive():
            self.lock.release()
