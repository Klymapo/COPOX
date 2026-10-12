FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRADIO_ANALYTICS_ENABLED=False \
    STYLIZER_DATA_DIR=/app/storage/jobs \
    STYLIZER_OUTPUT_DIR=/app/storage/outputs \
    HF_HOME=/app/storage/jobs/huggingface \
    STYLIZER_PROMPT_MODE=template

RUN apt-get update && apt-get install -y --no-install-recommends \
      libegl1 libgl1 libx11-6 libxfixes3 libxi6 libxrender1 libxxf86vm1 libsm6 libice6 libxkbcommon0 libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 stylizer \
    && mkdir -p /app/storage/jobs /app/storage/outputs \
    && chown -R stylizer:stylizer /app

WORKDIR /app
COPY requirements.txt requirements-server.txt ./
RUN python -m pip install --no-cache-dir -r requirements-server.txt
RUN python -c "import bpy, gradio; print('Blender', bpy.app.version_string)"
COPY --chown=stylizer:stylizer app.py server.py config.py jobs.py pipeline_core.py \
    artifacts.py fidelity.py mesh_service.py mesh_generator.py mesh_generator_threews.py \
    prompt_stylizer.py image_generator_agnes.py prepare_godot.py blender_prepare.py doctor.py ./
COPY --chown=stylizer:stylizer docs/GODOT_IMPORT.md ./docs/GODOT_IMPORT.md

USER stylizer
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD python -c "import os,urllib.request; port=os.getenv('STYLIZER_PORT') or os.getenv('PORT') or '7860'; urllib.request.urlopen('http://127.0.0.1:'+port+'/healthz',timeout=3)"
CMD ["python", "server.py"]
