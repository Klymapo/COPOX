"""Production entry point for a single persistent Stylizer server."""

import logging
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import gradio as gr
import uvicorn

from config import PROJECT_ROOT, settings, validate_server_config


def create_app():
    cfg = settings()
    validate_server_config(cfg)
    for directory in (cfg.data_dir, cfg.output_dir):
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=directory) as probe:
            probe.write(b"stylizer")

    import app as web

    @asynccontextmanager
    async def lifespan(application):
        application.state.manager = web.get_manager()
        try:
            yield
        finally:
            web.shutdown()

    application = FastAPI(title="Stylizer", lifespan=lifespan,
                          docs_url=None, redoc_url=None, openapi_url=None)

    @application.get("/healthz", include_in_schema=False)
    def health():
        manager = getattr(application.state, "manager", None)
        ready = bool(manager and manager.thread and manager.thread.is_alive() and not manager.stop.is_set())
        return JSONResponse({"status": "ok" if ready else "unavailable"}, status_code=200 if ready else 503)

    @application.middleware("http")
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    return gr.mount_gradio_app(
        application, web.demo.queue(), path="/", auth=(cfg.username, cfg.password),
        auth_message="Acceso a tu taller 3D", allowed_paths=[str(cfg.output_dir)],
        blocked_paths=[str(PROJECT_ROOT / ".env"), str(cfg.data_dir)], max_file_size="100mb",
        css=web.CSS, theme=gr.themes.Soft(primary_hue="cyan", neutral_hue="slate"), pwa=True,
        ssr_mode=False, run_history=False, footer_links=[],
    )


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        application = create_app()
    except (ValueError, OSError, RuntimeError) as error:
        raise SystemExit(str(error)) from error
    # One process owns the SQLite queue. TLS is terminated by the hosting provider.
    uvicorn.run(application, host="0.0.0.0", port=settings().port, workers=1,
                timeout_graceful_shutdown=20)


if __name__ == "__main__":
    main()
