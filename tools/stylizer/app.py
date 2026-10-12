"""Web workspace: persistent jobs, mobile status, generation and asset review."""

import argparse
import atexit
import getpass
import html
import logging
from logging.handlers import RotatingFileHandler
import sys
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

import gradio as gr

from artifacts import artifact_paths
from config import PROJECT_ROOT, settings
from fidelity import ASPECTS, RATINGS, save_review
from jobs import ACTIVE, JobManager

REQS_POR_MINUTO = 2
REQS_POR_HORA = 15
_peticiones = defaultdict(deque)
_manager = None
_manager_guard = threading.Lock()
STATUS_LABELS = {"queued": "En cola", "running": "En curso", "completed": "Completada",
                 "failed": "Falló", "interrupted": "Interrumpida"}
CSS = """
.gradio-container { max-width: 1180px !important; }
.job-summary { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }
.job-summary strong { font-size:1.5rem; display:block; }
.job-summary > div { flex:1; min-width:110px; padding:14px; border:1px solid var(--border-color-primary); border-radius:12px; }
.job-list { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:12px; }
.job-card { border:1px solid var(--border-color-primary); border-left:4px solid #0891b2; border-radius:10px; padding:14px; overflow-wrap:anywhere; }
.job-card h3 { font-size:1rem; margin:8px 0; }
.job-meta { font-size:.875rem; opacity:.8; }
.job-stage { padding:16px; border:1px solid var(--border-color-primary); border-radius:12px; margin:8px 0; overflow-wrap:anywhere; }
.job-stage h3 { font-size:1.1rem; margin:0 0 8px; }
@media(max-width:600px) {
  .gradio-container { padding:12px !important; }
  .job-list { grid-template-columns:1fr; }
  button { min-height:44px; }
  .tab-container button { padding:0 9px; font-size:14px; }
}
"""


def get_manager():
    global _manager
    with _manager_guard:
        if _manager is None:
            cfg = settings()
            _manager = JobManager(cfg.data_dir, cfg.output_dir)
        return _manager


def shutdown():
    if _manager is not None:
        _manager.close()


atexit.register(shutdown)


def verificar_limite(request):
    ip = request.client.host if request and request.client else "local"
    current = time.monotonic()
    history = _peticiones[ip]
    while history and current - history[0] >= 3600:
        history.popleft()
    if sum(current - stamp < 60 for stamp in history) >= REQS_POR_MINUTO:
        raise gr.Error(f"Espera: límite de {REQS_POR_MINUTO} tareas por minuto.")
    if len(history) >= REQS_POR_HORA:
        raise gr.Error(f"Espera: límite de {REQS_POR_HORA} tareas por hora.")
    history.append(current)


def status_panels(selected=None):
    manager = get_manager()
    jobs = manager.recent()
    choices = [(f"{STATUS_LABELS[job['status']]} · {job['label'][:40]} · {job['id'][:8]}", job["id"]) for job in jobs]
    if selected not in {job["id"] for job in jobs}:
        selected = jobs[0]["id"] if jobs else None
    job = manager.get(selected) if selected else None
    if job:
        error = f"<p>{html.escape(job['error'][:600])}</p>" if job.get("error") else ""
        stage = (f"<section class='job-stage'><h3>{html.escape(STATUS_LABELS[job['status']])}</h3>"
                 f"<p>{html.escape(job['stage'])}</p>{error}"
                 f"<span class='job-meta'>Tarea {job['id'][:8]} · Consulta: {time.strftime('%H:%M:%S')}</span></section>")
    else:
        stage = "<section class='job-stage'><h3>Aún no hay tareas</h3><p>Abre Generar para crear un modelo o Godot para preparar uno existente.</p></section>"
    counts = {state: sum(job["status"] == state for job in jobs) for state in ("queued", "running", "completed")}
    summary = "<div class='job-summary'>" + "".join(f"<div><strong>{counts[state]}</strong>{label}</div>" for state, label in
              [("queued", "En cola"), ("running", "Procesando"), ("completed", "Completadas en el historial")]) + "</div>"
    cards = "".join(f"<article class='job-card'><span class='job-meta'>{html.escape(STATUS_LABELS[item['status']])} · {item['id'][:8]}</span>"
                    f"<h3>{html.escape(item['label'][:90])}</h3><p>{html.escape(item['stage'])}</p></article>" for item in jobs[:8])
    return gr.update(choices=choices, value=selected), stage, summary + "<div class='job-list'>" + cards + "</div>"


def submit_generation(mode, idea, uploaded_image, provider, request: gr.Request):
    if mode not in ("text", "image"):
        raise gr.Error("Elige el tipo de entrada.")
    if mode == "image" and not uploaded_image:
        raise gr.Error("Sube una imagen.")
    if mode == "text" and not (idea or "").strip():
        raise gr.Error("Escribe una idea.")
    verificar_limite(request)
    try:
        identifier = get_manager().submit_generation(
            idea=idea if mode == "text" else None, image_path=uploaded_image if mode == "image" else None, provider=provider)
    except (ValueError, OSError) as error:
        raise gr.Error(str(error)) from error
    return (*status_panels(identifier), f"Tarea {identifier[:8]} guardada. Puedes seguirla en Estado desde cualquier dispositivo.")


def retry_job(identifier, provider, request: gr.Request):
    verificar_limite(request)
    try:
        identifier = get_manager().retry(identifier, provider)
    except (ValueError, OSError) as error:
        raise gr.Error(str(error)) from error
    return (*status_panels(identifier), "Reintento guardado en la cola.")


def submit_godot(identifier, uploaded_model, height, yaw, triangle_limit, request: gr.Request):
    job = get_manager().get(identifier) if identifier else None
    result = (job or {}).get("result") or {}
    source = uploaded_model or result.get("model")
    if not source:
        raise gr.Error("Carga un GLB o selecciona una tarea con un modelo terminado en Estado.")
    verificar_limite(request)
    try:
        identifier = get_manager().submit_godot(
            source=source, height=height, yaw=yaw, triangle_limit=triangle_limit,
            source_image=result.get("image") if not uploaded_model else None)
    except (ValueError, OSError) as error:
        raise gr.Error(str(error)) from error
    return (*status_panels(identifier), "Preparación para Godot en cola. Consulta su avance en Estado.")


def open_job(identifier):
    job = get_manager().get(identifier) if identifier else None
    if not job:
        raise gr.Error("Selecciona una tarea.")
    if job["status"] in ACTIVE:
        raise gr.Error("La tarea sigue en curso. El estado se actualiza cada 5 segundos.")
    run = job.get("result")
    if not run:
        raise gr.Error(job.get("error") or "Esta tarea no tiene resultados disponibles.")
    directory = Path(run["directory"])
    archive = directory / f"{run['id']}.zip"
    return (artifact_paths(run), str(archive) if archive.exists() else None,
            run.get("image"), run.get("model"), run.get("prompt", ""),
            f"Mostrando tarea **{identifier[:8]}** · {STATUS_LABELS[job['status']]}", run)


def change_mode(mode):
    return gr.update(visible=mode == "text"), gr.update(visible=mode == "image")


def preview_references(run, front, side, back):
    images = [(run["image"], "Imagen utilizada")] if run and run.get("image") else []
    images.extend((path, label) for path, label in [(front, "Frente"), (side, "Perfil"), (back, "Espalda")] if path)
    return images


def reset_review(run):
    return (preview_references(run, None, None, None), (run or {}).get("model"),
            None, None, None, *("Sin evaluar" for _ in ASPECTS), "", "", "")


def record_review(run, front, side, back, *values):
    ratings = dict(zip(ASPECTS, values[:len(ASPECTS)]))
    notes = values[len(ASPECTS)] or ""
    try:
        _, plan, archive = save_review(run, {"front": front, "side": side, "back": back}, ratings, notes)
        get_manager()._update(run["id"], result=run)
    except ValueError as error:
        raise gr.Error(str(error)) from error
    return plan, "Revisión guardada y ZIP actualizado.", artifact_paths(run), archive


with gr.Blocks(title="Stylizer · Taller 3D", analytics_enabled=False) as demo:
    session_run = gr.State()
    gr.Markdown("# Stylizer · Taller 3D")
    gr.Markdown("Genera, revisa y prepara tus modelos desde cualquier dispositivo.")
    with gr.Tabs(overflow_behavior="wrap") as tabs:
        with gr.Tab("Estado", id="status"):
            gr.Markdown("## Tus tareas")
            gr.Markdown("Actualización automática cada 5 segundos. Puedes cerrar esta pestaña: las tareas continúan mientras el servicio esté activo.")
            job_choice = gr.Dropdown(label="Seleccionar tarea", choices=[], interactive=True)
            status_output = gr.HTML()
            with gr.Row():
                refresh_btn = gr.Button("Actualizar")
                open_btn = gr.Button("Abrir resultados", variant="primary")
                retry_btn = gr.Button("Reintentar tarea")
            with gr.Accordion("Proveedor para reintento", open=False):
                retry_provider = gr.Dropdown(["auto", "trellis", "threews"], value="auto", label="Proveedor 3D")
            history_output = gr.HTML()
        with gr.Tab("Generar", id="generate"):
            mode = gr.Radio([("Desde una idea", "text"), ("Usar imagen existente", "image")], value="image", label="Punto de partida")
            idea_input = gr.Textbox(label="Tu idea", lines=3, max_length=4000, visible=False)
            image_input = gr.Image(label="Imagen principal", type="filepath", sources=["upload"], image_mode="RGBA", height=280)
            gr.Markdown("Usa una sola vista del personaje completo. Para un turnaround, recorta una vista.")
            provider = gr.Dropdown([("Automático: TRELLIS.2 → three.ws", "auto"), ("Solo TRELLIS.2", "trellis"), ("Solo three.ws draft", "threews")], value="auto", label="Proveedor 3D")
            gr.Markdown("El respaldo de three.ws es experimental y se detiene si el proveedor solicita pago.")
            generate_btn = gr.Button("Enviar a la cola", variant="primary")
        with gr.Tab("Resultados", id="results"):
            loaded_status = gr.Markdown("Selecciona una tarea en Estado y pulsa Abrir resultados.")
            with gr.Tabs(overflow_behavior="wrap"):
                with gr.Tab("Vista"):
                    with gr.Row():
                        image_output = gr.Image(label="Imagen utilizada", height=320)
                        mesh_output = gr.Model3D(label="Modelo 3D", height=320)
                    prompt_output = gr.Textbox(label="Prompt (si se partió de texto)", lines=3)
                with gr.Tab("Revisar fidelidad"):
                    gr.Markdown("Compara y anota qué conservar o corregir. Esta revisión registra indicaciones; la modificación de geometría se realiza en Blender.")
                    with gr.Row():
                        reference_gallery = gr.Gallery(label="Referencias", columns=2, height=320)
                        review_model = gr.Model3D(label="Modelo para comparar", height=320)
                    with gr.Accordion("Frente, perfil y espalda", open=False):
                        with gr.Row():
                            front_ref = gr.Image(label="Frente", type="filepath", sources=["upload"], image_mode="RGBA")
                            side_ref = gr.Image(label="Perfil", type="filepath", sources=["upload"], image_mode="RGBA")
                            back_ref = gr.Image(label="Espalda", type="filepath", sources=["upload"], image_mode="RGBA")
                    review_ratings = [gr.Radio(RATINGS, value="Sin evaluar", label=aspect) for aspect in ASPECTS]
                    review_notes = gr.Textbox(label="Correcciones concretas", lines=3, max_length=4000)
                    save_review_btn = gr.Button("Guardar revisión y actualizar ZIP")
                    review_plan = gr.Textbox(label="Qué conservar y qué corregir", lines=5, interactive=False)
                    review_status = gr.Markdown()
                with gr.Tab("Descargas"):
                    file_output = gr.File(label="Archivos", file_count="multiple")
                    zip_output = gr.DownloadButton("Descargar todo en ZIP")
        with gr.Tab("Godot", id="godot"):
            gr.Markdown("## Preparar un modelo para Godot")
            gr.Markdown("Usa el modelo de la tarea seleccionada en Estado o carga un GLB. La preparación se realiza con Blender en el equipo que aloja el servicio.")
            model_input = gr.File(label="GLB existente (opcional)", file_types=[".glb"], type="filepath")
            with gr.Row():
                target_height = gr.Number(value=1.8, minimum=0.01, maximum=100, label="Altura total en metros")
                target_yaw = gr.Number(value=0, minimum=-360, maximum=360, label="Giro horizontal en grados")
                target_triangles = gr.Number(value=0, minimum=0, precision=0, label="Objetivo de triángulos (0 conserva)")
            gr.Markdown("Se exporta una copia con escala y base ajustadas, materiales, archivo de Blender y reporte. La reducción es aproximada; revisa silueta y texturas antes de usar el modelo.")
            godot_btn = gr.Button("Preparar para Godot", variant="primary")
    notice = gr.Markdown()
    timer = gr.Timer(5)
    panel_outputs = [job_choice, status_output, history_output]
    submission_outputs = [*panel_outputs, notice]
    mode.change(change_mode, inputs=mode, outputs=[idea_input, image_input], queue=False)
    submitted = generate_btn.click(submit_generation, inputs=[mode, idea_input, image_input, provider],
                                   outputs=submission_outputs, api_name="generate", concurrency_id="submission")
    retried = retry_btn.click(retry_job, inputs=[job_choice, retry_provider], outputs=submission_outputs,
                             api_name="retry", concurrency_id="submission")
    prepared = godot_btn.click(submit_godot, inputs=[job_choice, model_input, target_height, target_yaw, target_triangles],
                              outputs=submission_outputs, api_name="godot", concurrency_id="submission")
    for event in (submitted, retried, prepared):
        event.success(lambda: gr.Tabs(selected="status"), outputs=tabs, api_name=False)
    refresh_btn.click(status_panels, inputs=job_choice, outputs=panel_outputs, queue=False,
                      api_name="status", show_progress="hidden")
    for event in (demo.load, timer.tick, job_choice.input):
        event(status_panels, inputs=job_choice, outputs=panel_outputs, queue=False,
              api_name=False, show_progress="hidden")
    opened = open_btn.click(open_job, inputs=job_choice,
                           outputs=[file_output, zip_output, image_output, mesh_output, prompt_output, loaded_status, session_run],
                           api_name="open")
    review_outputs = [reference_gallery, review_model, front_ref, side_ref, back_ref, *review_ratings, review_notes, review_plan, review_status]
    opened.success(reset_review, inputs=session_run, outputs=review_outputs)
    opened.success(lambda: gr.Tabs(selected="results"), outputs=tabs)
    for reference in (front_ref, side_ref, back_ref):
        reference.change(preview_references, inputs=[session_run, front_ref, side_ref, back_ref], outputs=reference_gallery, queue=False)
    save_review_btn.click(record_review, inputs=[session_run, front_ref, side_ref, back_ref, *review_ratings, review_notes],
                          outputs=[review_plan, review_status, file_output, zip_output],
                          api_name="review", concurrency_id="review")


def main():
    parser = argparse.ArgumentParser(description="Página web de Stylizer")
    access = parser.add_mutually_exclusive_group()
    access.add_argument("--mobile", action="store_true", help="Enlace HTTPS temporal para el celular")
    access.add_argument("--lan", action="store_true", help="Acceso en la misma red Wi-Fi")
    args = parser.parse_args()
    cfg = settings()
    password = cfg.password
    remote = args.mobile or args.lan
    if remote and not password:
        if not sys.stdin.isatty():
            parser.error("Configura STYLIZER_PASSWORD en .env para usar --mobile o --lan.")
        password = getpass.getpass("Crea una contraseña para el acceso web (mínimo 8 caracteres): ")
    if remote and len(password) < 8:
        parser.error("Usa una contraseña de al menos 8 caracteres.")
    auth = (cfg.username, password) if password else None
    if remote:
        print(f"Usuario del acceso web: {cfg.username}")
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(cfg.data_dir / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    logging.getLogger("stylizer").addHandler(handler)
    get_manager()
    try:
        demo.queue().launch(share=args.mobile, server_name="0.0.0.0" if remote else "127.0.0.1",
                            server_port=cfg.port, auth=auth, auth_message="Acceso a tu taller 3D",
                            allowed_paths=[str(cfg.output_dir)], blocked_paths=[str(PROJECT_ROOT / ".env"), str(cfg.data_dir)],
                            max_file_size="100mb", css=CSS, theme=gr.themes.Soft(primary_hue="cyan", neutral_hue="slate"),
                            pwa=True)
    finally:
        shutdown()


if __name__ == "__main__":
    main()
