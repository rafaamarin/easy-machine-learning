from __future__ import annotations

import argparse
import mimetypes
import os
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import unquote_to_bytes, urlsplit

PUBLIC_FILES = {
    "index.html",
    "contenido/01_datos_y_formas/index.html",
    "assets/css/estilos.css",
    "assets/js/app.mjs",
    "assets/js/jupyter_url.mjs",
    "assets/js/laboratorios.mjs",
    "assets/js/progreso.mjs",
    "assets/js/pyodide_cliente.mjs",
    "assets/js/pyodide_execution.mjs",
    "assets/js/pyodide_worker.mjs",
}
PYODIDE_PREFIX = PurePosixPath("assets/vendor/pyodide")


class PublicBookServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, book_root: Path, port: int) -> None:
        self.book_root = book_root.resolve(strict=True)
        super().__init__(("127.0.0.1", port), PublicBookHandler)


class PublicBookHandler(BaseHTTPRequestHandler):
    server: PublicBookServer

    def do_GET(self) -> None:
        self._serve_file(include_body=True)

    def do_HEAD(self) -> None:
        self._serve_file(include_body=False)

    def log_message(self, _format: str, *args: object) -> None:
        del args

    def _serve_file(self, *, include_body: bool) -> None:
        if not self._has_valid_host():
            self.send_error(400, "Host no permitido")
            return
        candidate = self._resolve_public_file()
        if candidate is None:
            self.send_error(404, "Recurso no disponible")
            return
        try:
            descriptor = os.open(candidate, os.O_RDONLY | os.O_NOFOLLOW)
        except OSError:
            self.send_error(404, "Recurso no disponible")
            return
        with os.fdopen(descriptor, "rb") as source:
            file_size = os.fstat(source.fileno()).st_size
            self.send_response(200)
            self.send_header("Content-Type", _content_type(candidate))
            self.send_header("Content-Length", str(file_size))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            if include_body:
                shutil.copyfileobj(source, self.wfile, length=1024 * 1024)

    def _has_valid_host(self) -> bool:
        values = self.headers.get_all("Host", failobj=[])
        if len(values) != 1:
            return False
        value = values[0]
        if value != value.strip():
            return False
        port = self.server.server_port
        return value.lower() in {
            f"127.0.0.1:{port}",
            f"localhost:{port}",
            f"[::1]:{port}",
        }

    def _resolve_public_file(self) -> Path | None:
        try:
            raw_path = urlsplit(self.path).path
            decoded_path = unquote_to_bytes(raw_path).decode("utf-8", errors="strict")
        except (UnicodeDecodeError, ValueError):
            return None
        if decoded_path == "/":
            relative_path = PurePosixPath("index.html")
        else:
            if (
                not decoded_path.startswith("/")
                or decoded_path.startswith("//")
                or "\\" in decoded_path
                or "\x00" in decoded_path
            ):
                return None
            components = decoded_path[1:].split("/")
            if any(component in {"", ".", ".."} for component in components):
                return None
            relative_path = PurePosixPath(*components)
        relative_value = relative_path.as_posix()
        is_runtime = (
            relative_path != PYODIDE_PREFIX
            and relative_path.is_relative_to(PYODIDE_PREFIX)
            and all(not part.startswith(".") for part in relative_path.parts)
        )
        if relative_value not in PUBLIC_FILES and not is_runtime:
            return None

        candidate = self.server.book_root.joinpath(*relative_path.parts)
        current = self.server.book_root
        try:
            for part in relative_path.parts:
                current /= part
                if current.is_symlink():
                    return None
            resolved_candidate = candidate.resolve(strict=True)
        except OSError:
            return None
        if not resolved_candidate.is_relative_to(self.server.book_root):
            return None
        if not resolved_candidate.is_file():
            return None
        return resolved_candidate


def _content_type(path: Path) -> str:
    if path.suffix == ".mjs":
        return "text/javascript; charset=utf-8"
    content_type, _encoding = mimetypes.guess_type(path.name)
    if content_type is None:
        return "application/octet-stream"
    if content_type.startswith("text/"):
        return f"{content_type}; charset=utf-8"
    return content_type


def create_server(book_root: Path, port: int) -> PublicBookServer:
    return PublicBookServer(book_root, port)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sirve el libro local de forma segura."
    )
    parser.add_argument("--book-root", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    arguments = parser.parse_args()
    server = create_server(arguments.book_root, arguments.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
