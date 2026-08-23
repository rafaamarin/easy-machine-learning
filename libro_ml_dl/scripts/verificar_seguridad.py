from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
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


@dataclass(frozen=True, order=True)
class HistoricalFinding:
    commit: str
    path: str
    line_number: int
    detector_type: str


class HistoricalScanError(RuntimeError):
    def __init__(self, findings: list[HistoricalFinding]) -> None:
        self.findings = sorted(findings)
        super().__init__("hallazgos históricos no adjudicados")


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
        f"{_escape_metadata(finding.path)}:{finding.line_number} "
        f"[{_escape_metadata(finding.detector_type)}]"
        for finding in findings
    ]


def render_historical_findings(
    findings: list[HistoricalFinding],
) -> list[str]:
    return [
        f"{_escape_metadata(finding.commit)} "
        f"{_escape_metadata(finding.path)}:{finding.line_number} "
        f"[{_escape_metadata(finding.detector_type)}]"
        for finding in findings
    ]


def _escape_metadata(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)[1:-1]


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
    if path.is_symlink():
        raise RuntimeError("el inventario contiene un enlace simbólico")
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
        try:
            relative_paths = [
                relative_path.decode("utf-8")
                for relative_path in completed.stdout.split(b"\0")
                if relative_path
            ]
        except UnicodeDecodeError as error:
            raise RuntimeError(
                "el inventario contiene un nombre que no es UTF-8"
            ) from error
        paths = sorted(repo_root / path for path in relative_paths)
    else:
        if repo_root.joinpath(".git").exists():
            raise RuntimeError("no se pudo obtener el inventario de Git")
        paths = sorted(repo_root.rglob("*"))
    return [path for path in paths if not _is_excluded_candidate(path, repo_root)]


def _find_personal_path_findings(repo_root: Path) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for path in _candidate_files(repo_root):
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relative_path = path.relative_to(repo_root).as_posix()
        for line_number, line in enumerate(source.splitlines(), start=1):
            if any(marker in line for marker in PERSONAL_PATH_MARKERS):
                findings.append(
                    SecretFinding(relative_path, line_number, "Ruta personal")
                )
    return sorted(findings)


def find_personal_paths(repo_root: Path) -> list[Path]:
    return sorted(
        {
            repo_root / finding.path
            for finding in _find_personal_path_findings(repo_root)
        }
    )


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


def _is_adjudicated_checksum(
    snapshot_root: Path,
    finding: SecretFinding,
) -> bool:
    if finding.detector_type != "Hex High Entropy String":
        return False
    known_location = (finding.path, finding.line_number)
    if known_location not in {
        ("libro_ml_dl/scripts/preparar_entorno.py", 17),
        ("libro_ml_dl/pruebas/python/test_preparar_entorno.py", 81),
    }:
        return False
    try:
        source_lines = (
            snapshot_root.joinpath(finding.path)
            .read_text(encoding="utf-8")
            .splitlines()
        )
        target_line = source_lines[finding.line_number - 1]
    except (IndexError, OSError, UnicodeDecodeError):
        return False
    if re.search(r"[0-9a-fA-F]{64}", target_line) is None:
        return False
    if known_location[0].endswith("scripts/preparar_entorno.py"):
        return "CORE_SHA256" in target_line
    context_start = max(0, finding.line_number - 8)
    context = "\n".join(source_lines[context_start : finding.line_number])
    return "test_sha256_file_uses_file_bytes" in context and (
        "sha256_file(path)" in context
    )


def _validated_archive_members(
    archive: tarfile.TarFile,
) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    for member in members:
        member_path = PurePosixPath(member.name)
        try:
            member.name.encode("utf-8", errors="strict")
        except UnicodeEncodeError as error:
            raise RuntimeError(
                "el historial contiene un nombre que no es UTF-8"
            ) from error
        if member_path.is_absolute() or ".." in member_path.parts:
            raise RuntimeError("git archive devolvió una ruta insegura")
        if member.issym() or member.islnk():
            raise RuntimeError("el historial contiene un enlace simbólico")
        if not (member.isfile() or member.isdir()):
            raise RuntimeError("git archive devolvió un tipo no permitido")
    return members


def _git_commits(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "rev-list", "--all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    try:
        commits = completed.stdout.decode("ascii", errors="strict").splitlines()
    except UnicodeDecodeError as error:
        raise RuntimeError("Git devolvió identificadores no válidos") from error
    if not commits or any(
        re.fullmatch(r"[0-9a-f]{40,64}", commit) is None for commit in commits
    ):
        raise RuntimeError("Git devolvió un historial no válido")
    return commits


def scan_git_history(repo_root: Path) -> list[HistoricalFinding]:
    adjudicated: list[HistoricalFinding] = []
    rejected: list[HistoricalFinding] = []
    for commit in _git_commits(repo_root):
        with tempfile.TemporaryDirectory(prefix="easy_ml_history_") as directory:
            temporary_root = Path(directory)
            archive_path = temporary_root / "tree.tar"
            snapshot_root = temporary_root / "snapshot"
            snapshot_root.mkdir()
            with archive_path.open("wb") as output:
                subprocess.run(
                    ["git", "archive", "--format=tar", commit],
                    cwd=repo_root,
                    check=True,
                    stdout=output,
                    stderr=subprocess.PIPE,
                )
            with tarfile.open(archive_path, mode="r:") as archive:
                members = _validated_archive_members(archive)
                archive.extractall(snapshot_root, members=members)

            secret_findings = run_secret_scan(snapshot_root)
            personal_findings = _find_personal_path_findings(snapshot_root)
            for finding in [*secret_findings, *personal_findings]:
                historical_finding = HistoricalFinding(
                    commit=commit,
                    path=finding.path,
                    line_number=finding.line_number,
                    detector_type=finding.detector_type,
                )
                if _is_adjudicated_checksum(snapshot_root, finding):
                    adjudicated.append(historical_finding)
                else:
                    rejected.append(historical_finding)
    if rejected:
        raise HistoricalScanError(rejected)
    return sorted(adjudicated)


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
    try:
        historical_findings = scan_git_history(REPO_ROOT)
    except HistoricalScanError as error:
        for line in render_historical_findings(error.findings):
            print(f"HALLAZGO_HISTORICO: {line}", file=sys.stderr)
        return 1
    except Exception:
        print("ERROR_SEGURIDAD: HISTORIAL_GIT", file=sys.stderr)
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
    for line in render_historical_findings(historical_findings):
        print(f"CHECKSUM_HISTORICO_ADJUDICADO: {line}")
    try:
        run_dependency_audit(BOOK_ROOT)
    except Exception:
        print("ERROR_SEGURIDAD: AUDITORIA_DEPENDENCIAS", file=sys.stderr)
        return 2
    print("SEGURIDAD_PUBLICACION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
