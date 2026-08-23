from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BOOK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BOOK_ROOT.parent
EXCLUDED_FILES = (
    r"(^|/)(\.git|\.superpowers|\.venv|\.ruff_cache|__pycache__|"
    r"assets/vendor/pyodide)/"
)
EXCLUDED_DIRECTORIES = {
    ".git",
    ".superpowers",
    ".venv",
    ".ruff_cache",
    "__pycache__",
}
PERSONAL_USER = "rafa"
PERSONAL_PATH_MARKERS = (
    f"/Users/{PERSONAL_USER}/",
    f"/home/{PERSONAL_USER}/",
    f"C:\\Users\\{PERSONAL_USER}\\",
)
SECRET_SCAN_CHUNK_SIZE = 200


@dataclass(frozen=True, order=True)
class SecretFinding:
    path: str
    line_number: int
    detector_type: str


def parse_secret_results(payload: dict[str, Any]) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for path, entries in payload.get("results", {}).items():
        for entry in entries:
            findings.append(
                SecretFinding(
                    path=str(path),
                    line_number=int(entry["line_number"]),
                    detector_type=str(entry["type"]),
                )
            )
    return sorted(findings)


def render_secret_findings(findings: list[SecretFinding]) -> list[str]:
    return [
        f"{finding.path}:{finding.line_number} [{finding.detector_type}]"
        for finding in findings
    ]


def _normalize_secret_paths(
    findings: list[SecretFinding],
    repo_root: Path,
) -> list[SecretFinding]:
    normalized: list[SecretFinding] = []
    resolved_root = repo_root.resolve()
    for finding in findings:
        path = Path(finding.path)
        try:
            relative_path = (
                path.resolve().relative_to(resolved_root)
                if path.is_absolute()
                else path
            )
        except ValueError as error:
            raise RuntimeError(
                "detect-secrets devolvió una ruta fuera del repositorio"
            ) from error
        if ".." in relative_path.parts:
            raise RuntimeError("detect-secrets devolvió una ruta fuera del repositorio")
        normalized.append(
            SecretFinding(
                path=relative_path.as_posix(),
                line_number=finding.line_number,
                detector_type=finding.detector_type,
            )
        )
    return sorted(normalized)


def _is_excluded_candidate(path: Path, repo_root: Path) -> bool:
    relative_path = path.relative_to(repo_root)
    return (
        not path.is_file()
        or any(part in EXCLUDED_DIRECTORIES for part in relative_path.parts)
        or relative_path.parts[:4] == ("libro_ml_dl", "assets", "vendor", "pyodide")
    )


def _candidate_files(repo_root: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
    except OSError:
        completed = None
    if completed is not None and completed.returncode == 0:
        paths = sorted(
            repo_root / os.fsdecode(relative_path)
            for relative_path in completed.stdout.split(b"\0")
            if relative_path
        )
    else:
        if repo_root.joinpath(".git").exists():
            raise RuntimeError("no se pudo obtener el inventario de Git")
        paths = sorted(repo_root.rglob("*"))
    return [path for path in paths if not _is_excluded_candidate(path, repo_root)]


def find_personal_paths(repo_root: Path) -> list[Path]:
    matches: list[Path] = []
    for path in _candidate_files(repo_root):
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(marker in source for marker in PERSONAL_PATH_MARKERS):
            matches.append(path)
    return matches


def run_secret_scan(repo_root: Path) -> list[SecretFinding]:
    executable = shutil.which("detect-secrets")
    if executable is None:
        raise RuntimeError("detect-secrets no está instalado")
    candidates = _candidate_files(repo_root)
    findings: list[SecretFinding] = []
    for start in range(0, len(candidates), SECRET_SCAN_CHUNK_SIZE):
        chunk = candidates[start : start + SECRET_SCAN_CHUNK_SIZE]
        relative_paths = [path.relative_to(repo_root).as_posix() for path in chunk]
        completed = subprocess.run(
            [
                executable,
                "scan",
                "--no-verify",
                "--exclude-files",
                EXCLUDED_FILES,
                "--",
                *relative_paths,
            ],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        findings.extend(parse_secret_results(json.loads(completed.stdout)))
    return _normalize_secret_paths(findings, repo_root)


def run_dependency_audit(book_root: Path) -> None:
    uv = shutil.which("uv")
    pip_audit = shutil.which("pip-audit")
    if uv is None or pip_audit is None:
        raise RuntimeError("uv y pip-audit deben estar instalados")
    with tempfile.NamedTemporaryFile(suffix=".txt") as requirements:
        subprocess.run(
            [
                uv,
                "export",
                "--frozen",
                "--group",
                "validation",
                "--group",
                "notebooks",
                "--group",
                "security",
                "--no-emit-project",
                "--no-hashes",
                "--format",
                "requirements-txt",
            ],
            cwd=book_root,
            check=True,
            stdout=requirements,
            stderr=subprocess.PIPE,
        )
        requirements.flush()
        subprocess.run(
            [
                pip_audit,
                "-r",
                requirements.name,
                "--progress-spinner",
                "off",
            ],
            check=True,
            capture_output=True,
        )


def main() -> int:
    try:
        findings = run_secret_scan(REPO_ROOT)
    except Exception:
        print("ERROR_SEGURIDAD: ESCANEO_SECRETOS", file=sys.stderr)
        return 2
    try:
        personal_paths = find_personal_paths(REPO_ROOT)
    except Exception:
        print("ERROR_SEGURIDAD: RUTAS_PERSONALES", file=sys.stderr)
        return 2
    if findings:
        for line in render_secret_findings(findings):
            print(f"POTENCIAL_SECRETO: {line}", file=sys.stderr)
    if personal_paths:
        for path in personal_paths:
            print(
                f"RUTA_PERSONAL: {path.relative_to(REPO_ROOT)}",
                file=sys.stderr,
            )
    if findings or personal_paths:
        return 1
    try:
        run_dependency_audit(BOOK_ROOT)
    except Exception:
        print("ERROR_SEGURIDAD: AUDITORIA_DEPENDENCIAS", file=sys.stderr)
        return 2
    print("SEGURIDAD_PUBLICACION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
