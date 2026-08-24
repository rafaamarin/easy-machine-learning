from __future__ import annotations

import hashlib
import json
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import nbformat
from nbclient import NotebookClient

BOOK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BOOK_ROOT.parent
NOTEBOOK_PATHS = (
    REPO_ROOT / "material_fuente/notebooks/01-series-dataframes.ipynb",
    REPO_ROOT / "material_fuente/notebooks/07-estadisticas-basicas.ipynb",
    REPO_ROOT / "material_fuente/notebooks/05-scale.ipynb",
)
KERNEL_NAME = "easy-machine-learning"


@dataclass(frozen=True)
class NotebookExecutionSummary:
    path: Path
    code_cells: int
    error_outputs: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def project_kernel_path() -> Iterator[None]:
    previous_jupyter_path = os.environ.get("JUPYTER_PATH")
    with TemporaryDirectory(prefix="easy_ml_kernel_") as directory:
        kernel_directory = Path(directory) / "kernels" / KERNEL_NAME
        kernel_directory.mkdir(parents=True)
        kernel_directory.joinpath("kernel.json").write_text(
            json.dumps(
                {
                    "argv": [
                        sys.executable,
                        "-m",
                        "ipykernel_launcher",
                        "-f",
                        "{connection_file}",
                    ],
                    "display_name": "Easy Machine Learning",
                    "language": "python",
                }
            ),
            encoding="utf-8",
        )
        os.environ["JUPYTER_PATH"] = directory
        try:
            yield
        finally:
            if previous_jupyter_path is None:
                os.environ.pop("JUPYTER_PATH", None)
            else:
                os.environ["JUPYTER_PATH"] = previous_jupyter_path


def execute_notebook(path: Path) -> NotebookExecutionSummary:
    original_bytes = path.read_bytes()
    try:
        with TemporaryDirectory(prefix="easy_ml_notebook_") as directory:
            execution_root = Path(directory)
            execution_path = execution_root / path.name
            execution_path.write_bytes(original_bytes)
            if execution_path.read_bytes() != original_bytes:
                raise RuntimeError("la copia temporal del notebook no es idéntica")
            notebook = nbformat.read(execution_path, as_version=4)
            with project_kernel_path():
                client = NotebookClient(
                    notebook,
                    timeout=180,
                    kernel_name=KERNEL_NAME,
                    resources={"metadata": {"path": str(execution_root)}},
                )
                client.execute()
            code_cells = sum(cell.cell_type == "code" for cell in notebook.cells)
            error_outputs = sum(
                output.output_type == "error"
                for cell in notebook.cells
                for output in cell.get("outputs", [])
            )
            return NotebookExecutionSummary(path, code_cells, error_outputs)
    finally:
        try:
            source_changed = path.read_bytes() != original_bytes
        except OSError:
            source_changed = True
        if source_changed:
            try:
                path.write_bytes(original_bytes)
                restored = path.read_bytes() == original_bytes
            except OSError as error:
                raise RuntimeError(
                    "el notebook fuente cambió y no pudo restaurarse"
                ) from error
            if not restored:
                raise RuntimeError("el notebook fuente cambió y no pudo restaurarse")
            raise RuntimeError(
                "el notebook fuente cambió durante la ejecución y fue restaurado"
            )


def main() -> int:
    os.environ.setdefault("MPLBACKEND", "Agg")
    for path in NOTEBOOK_PATHS:
        summary = execute_notebook(path)
        print(
            "NOTEBOOK_OK "
            f"path={summary.path.relative_to(REPO_ROOT)} "
            f"code_cells={summary.code_cells} errors={summary.error_outputs}"
        )
    print("NOTEBOOKS_REPRODUCIBLES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
