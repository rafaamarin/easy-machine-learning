from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

if __package__:
    from scripts.modelo_contenido import resolve_vault_root
else:
    from modelo_contenido import resolve_vault_root


def validate_port(port: int) -> int:
    if not 1 <= port <= 65535:
        raise ValueError("El puerto debe estar entre 1 y 65535")
    return port


def port_argument(value: str) -> int:
    try:
        return validate_port(int(value))
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def find_free_port(preferred: int) -> int:
    validate_port(preferred)
    final_port = min(preferred + 99, 65535)
    for candidate in range(preferred, final_port + 1):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", candidate))
            except OSError:
                continue
            return candidate
    raise RuntimeError(f"No hay puerto libre entre {preferred} y {final_port}")


def wait_for_port(
    port: int,
    timeout_seconds: float,
    process: subprocess.Popen[bytes],
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code is not None:
            raise RuntimeError(
                "El servicio terminó antes de abrir el puerto "
                f"{port} (código {return_code})"
            )
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"El servicio no abrió el puerto {port}")


def find_jupyter_executable(repo_root: Path) -> Path | None:
    local = repo_root / ".venv" / "bin" / "jupyter"
    if local.is_file():
        return local
    system = shutil.which("jupyter")
    return Path(system) if system else None


def kernel_names(jupyter: Path) -> set[str]:
    completed = subprocess.run(
        [str(jupyter), "kernelspec", "list", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    return set(payload.get("kernelspecs", {}))


def build_jupyter_command(
    jupyter: Path,
    port: int,
    token: str,
    repo_root: Path,
) -> list[str]:
    return [
        str(jupyter),
        "lab",
        "--no-browser",
        "--ServerApp.ip=127.0.0.1",
        f"--ServerApp.port={port}",
        "--ServerApp.port_retries=0",
        f"--ServerApp.token={token}",
        "--ServerApp.password=",
        "--ServerApp.allow_remote_access=False",
        f"--ServerApp.root_dir={repo_root}",
    ]


def build_web_command(book_root: Path, port: int) -> list[str]:
    return [
        sys.executable,
        str(book_root / "scripts" / "servidor_web.py"),
        "--book-root",
        str(book_root),
        "--port",
        str(port),
    ]


def _signal_process_groups(
    group_ids: list[int],
    signal_number: signal.Signals,
) -> None:
    for group_id in group_ids:
        try:
            os.killpg(group_id, signal_number)
        except ProcessLookupError:
            continue


def _wait_for_processes(
    processes: list[subprocess.Popen[bytes]],
    timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    for process in processes:
        if process.poll() is not None:
            continue
        timeout = max(0, deadline - time.monotonic())
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            continue


def stop_processes(processes: list[subprocess.Popen[bytes]]) -> None:
    group_ids = [process.pid for process in processes]
    _signal_process_groups(group_ids, signal.SIGINT)
    _wait_for_processes(processes, timeout_seconds=5)
    _signal_process_groups(group_ids, signal.SIGTERM)
    _wait_for_processes(processes, timeout_seconds=2)
    _signal_process_groups(group_ids, signal.SIGKILL)
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                continue


def main() -> int:
    parser = argparse.ArgumentParser(description="Lanza el libro local.")
    parser.add_argument("--sin-jupyter", action="store_true")
    parser.add_argument("--sin-navegador", action="store_true")
    parser.add_argument("--puerto-web", type=port_argument, default=8000)
    parser.add_argument("--puerto-jupyter", type=port_argument, default=8888)
    parser.add_argument("--jupyter-ejecutable", type=Path)
    arguments = parser.parse_args()

    book_root = Path(__file__).resolve().parents[1]
    jupyter_override = arguments.jupyter_ejecutable
    http_process: subprocess.Popen[bytes] | None = None
    jupyter_process: subprocess.Popen[bytes] | None = None
    try:
        web_port = find_free_port(arguments.puerto_web)
        web_url = f"http://127.0.0.1:{web_port}/"
        http_process = subprocess.Popen(
            build_web_command(book_root, web_port),
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_for_port(web_port, timeout_seconds=10, process=http_process)
    except Exception:
        if http_process is not None:
            stop_processes([http_process])
        print(
            "ERROR: el servidor web local no pudo iniciarse. "
            "Revisa el entorno y el puerto configurado.",
            file=sys.stderr,
        )
        return 1

    try:
        manifest_path = (
            book_root / "assets" / "vendor" / "pyodide" / "manifest.local.json"
        )
        if not manifest_path.is_file():
            print(
                "AVISO: Pyodide no está preparado. "
                "Ejecuta 'uv run python scripts/preparar_entorno.py'."
            )

        book_url = web_url
        if not arguments.sin_jupyter:
            try:
                if jupyter_override is not None:
                    jupyter_override = jupyter_override.expanduser().resolve()
                    if not jupyter_override.is_file():
                        raise RuntimeError("Jupyter configurado no disponible")
                jupyter = jupyter_override or find_jupyter_executable(book_root)
                if jupyter is None:
                    print("AVISO: Jupyter no encontrado; continúa el modo web.")
                else:
                    vault_root = resolve_vault_root(book_root)
                    names = kernel_names(jupyter)
                    python_status = (
                        "disponible" if "python3" in names else "no registrado"
                    )
                    print(f"Kernel Python del proyecto: {python_status}")
                    jupyter_port = find_free_port(arguments.puerto_jupyter)
                    token = secrets.token_urlsafe(32)
                    command = build_jupyter_command(
                        jupyter,
                        jupyter_port,
                        token,
                        vault_root,
                    )
                    jupyter_process = subprocess.Popen(
                        command,
                        start_new_session=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    wait_for_port(
                        jupyter_port,
                        timeout_seconds=30,
                        process=jupyter_process,
                    )
                    jupyter_url = f"http://127.0.0.1:{jupyter_port}/lab?token={token}"
                    print(f"JupyterLab: {jupyter_url}")
                    book_url = f"{web_url}?{urlencode({'jupyter_url': jupyter_url})}"
            except Exception:
                if jupyter_process is not None:
                    stop_processes([jupyter_process])
                    jupyter_process = None
                print(
                    "AVISO: JupyterLab no pudo iniciarse; continúa el modo web. "
                    "Repite './instalar.sh' y revisa la configuración local."
                )

        print(f"Libro: {book_url}")
        if not arguments.sin_navegador:
            webbrowser.open(book_url)
        while True:
            if http_process.poll() is not None:
                print("ERROR: el servidor web local terminó de forma inesperada.")
                return 1
            if jupyter_process is not None and jupyter_process.poll() is not None:
                stop_processes([jupyter_process])
                jupyter_process = None
                print(
                    "AVISO: JupyterLab se detuvo; "
                    "el libro web sigue disponible. "
                    "Repite './instalar.sh' antes de reintentar."
                )
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 0
    finally:
        remaining_processes = [http_process]
        if jupyter_process is not None:
            remaining_processes.append(jupyter_process)
        stop_processes(remaining_processes)


if __name__ == "__main__":
    raise SystemExit(main())
