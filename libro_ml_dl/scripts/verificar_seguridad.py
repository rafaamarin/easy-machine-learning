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
        return sorted(
            repo_root / os.fsdecode(relative_path)
            for relative_path in completed.stdout.split(b"\0")
            if relative_path
        )
    return sorted(repo_root.rglob("*"))


def find_personal_paths(repo_root: Path) -> list[Path]:
    matches: list[Path] = []
    for path in _candidate_files(repo_root):
        relative_path = path.relative_to(repo_root)
        if (
            not path.is_file()
            or any(part in EXCLUDED_DIRECTORIES for part in relative_path.parts)
            or relative_path.parts[:4] == ("libro_ml_dl", "assets", "vendor", "pyodide")
        ):
            continue
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
    completed = subprocess.run(
        [
            executable,
            "scan",
            "--no-verify",
            "--all-files",
            "--exclude-files",
            EXCLUDED_FILES,
            str(repo_root),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    findings = parse_secret_results(json.loads(completed.stdout))
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
        )


def main() -> int:
    findings = run_secret_scan(REPO_ROOT)
    personal_paths = find_personal_paths(REPO_ROOT)
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
    run_dependency_audit(BOOK_ROOT)
    print("SEGURIDAD_PUBLICACION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
