"""Only package known artifacts from the current generation."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def artifact_paths(run):
    directory = Path(run["directory"])
    paths = [directory / name for name in ("manifest.json", "prompt.json", "report.json", "GODOT_IMPORT.md", "blender.log", "model_prepared.blend")]
    if run.get("image"):
        paths.append(directory / "image.png")
    if run.get("model"):
        model = Path(run["model"])
        if model.resolve().parent == directory.resolve():
            paths.append(model)
    paths.extend(sorted(directory.glob("review_*.json")))
    paths.extend(sorted((directory / "references").rglob("*.png")))
    return [str(path) for path in paths if path.is_file()]


def package_run(run):
    directory = Path(run["directory"])
    archive = directory / f"{run['id']}.zip"
    temporary = archive.with_suffix(".zip.tmp")
    with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as bundle:
        for path in artifact_paths(run):
            bundle.write(path, arcname=Path(path).relative_to(directory).as_posix())
    temporary.replace(archive)
    return str(archive)
