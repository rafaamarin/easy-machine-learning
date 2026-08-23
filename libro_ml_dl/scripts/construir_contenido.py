from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
from pathlib import Path
from string import Template
from typing import Any

import markdown

if __package__:
    from scripts.modelo_contenido import (
        load_manifest,
        resolve_book_path,
        validate_manifest,
    )
else:
    from modelo_contenido import load_manifest, resolve_book_path, validate_manifest

LAB_PATTERN = re.compile(
    r'<py-lab data-lab-id="(?P<lab_id>[a-z0-9_]+)" '
    r'data-src="(?P<src>[^"]+)" data-packages="(?P<packages>[^"]*)" '
    r'data-title="(?P<title>[^"]+)"></py-lab>'
)


def source_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expand_lab_tags(markdown_text: str, root: Path) -> str:
    resolved_root = root.resolve()

    def replace(match: re.Match[str]) -> str:
        source_path = (root / match.group("src")).resolve()
        if not source_path.is_relative_to(resolved_root):
            raise ValueError(f"lab fuera del libro: {source_path}")
        code = source_path.read_text(encoding="utf-8")
        title = html.escape(match.group("title"), quote=True)
        packages = html.escape(match.group("packages"), quote=True)
        lab_id = html.escape(match.group("lab_id"), quote=True)
        return (
            f'<section class="python-lab" data-python-lab="{lab_id}" '
            f'data-packages="{packages}">'
            f'<header><h3>{title}</h3><span data-lab-status aria-live="polite">'
            "Sin ejecutar</span></header>"
            f'<textarea data-lab-code spellcheck="false" '
            f'aria-label="Código Python de {title}">{html.escape(code)}</textarea>'
            '<div class="lab-actions"><button type="button" data-run>Ejecutar</button>'
            '<button type="button" data-cancel disabled>Cancelar</button>'
            '<button type="button" data-reset>Reiniciar</button></div>'
            '<pre data-lab-output aria-live="polite"></pre>'
            "<div data-lab-figures></div></section>"
        )

    return LAB_PATTERN.sub(replace, markdown_text)


def render_navigation(
    modules: list[dict[str, Any]],
    root: Path,
    output_parent: Path,
) -> str:
    items: list[str] = []
    for module in modules:
        label = html.escape(f"{module['number']}. {module['title']}")
        output = module["output"]
        if module["status"] == "disponible" and isinstance(output, str):
            href = os.path.relpath(root / output, start=output_parent)
            items.append(f'<li><a href="{html.escape(href)}">{label}</a></li>')
        else:
            items.append(
                f'<li><span aria-disabled="true">{label} · próximamente</span></li>'
            )
    return "<ol>" + "".join(items) + "</ol>"


def render_module_index(
    modules: list[dict[str, Any]],
    root: Path,
    output_parent: Path,
) -> str:
    modules_by_id = {str(module["id"]): module for module in modules}
    cards: list[str] = []
    for module in modules:
        title = html.escape(f"{module['number']}. {module['title']}")
        output = module["output"]
        if module["status"] == "disponible" and isinstance(output, str):
            href = os.path.relpath(root / output, start=output_parent)
            heading = f'<a href="{html.escape(href)}">{title}</a>'
            status = "Disponible"
        elif module["status"] == "en_construccion":
            heading = title
            status = "En construcción"
        else:
            heading = title
            status = "Planificado"
        prerequisites = module["prerequisites"]
        prerequisite_titles = [
            str(modules_by_id[item]["title"]) for item in prerequisites
        ]
        prerequisite_text = ", ".join(prerequisite_titles) or "Ninguno"
        cards.append(
            '<article class="module-card">'
            f'<p class="module-status">{status}</p><h3>{heading}</h3>'
            "<dl>"
            f"<div><dt>Duración</dt><dd>{module['duration_minutes']} min</dd></div>"
            "<div><dt>Prerequisitos</dt>"
            f"<dd>{html.escape(prerequisite_text)}</dd></div>"
            "<div><dt>Ejecución</dt>"
            f"<dd>{html.escape(str(module['execution_mode']))}</dd></div>"
            "</dl></article>"
        )
    return (
        '<section aria-labelledby="indice_completo"><h2 id="indice_completo">'
        'Índice completo</h2><div class="module-grid">'
        + "".join(cards)
        + "</div></section>"
    )


def render_module(
    root: Path,
    module: dict[str, Any],
    manifest: dict[str, Any],
) -> str:
    source_path = resolve_book_path(root, str(module["source"]))
    source = source_path.read_text(encoding="utf-8")
    expanded = expand_lab_tags(source, root)
    content_html = markdown.markdown(
        expanded,
        extensions=["fenced_code", "tables", "attr_list", "md_in_html"],
    )
    output_path = resolve_book_path(root, str(module["output"]))
    asset_prefix = os.path.relpath(root, output_path.parent)
    modules = manifest["modules"]
    if module["id"] == "00_inicio":
        content_html += render_module_index(modules, root, output_path.parent)
    template = Template(
        (root / "assets" / "plantillas" / "pagina.html").read_text(encoding="utf-8")
    )
    return template.substitute(
        page_title=html.escape(str(module["title"])),
        page_description=html.escape(
            f"Módulo {module['number']}: {module['title']}", quote=True
        ),
        asset_prefix=asset_prefix,
        module_id=html.escape(str(module["id"]), quote=True),
        content_version=html.escape(str(manifest["content_version"])),
        home_href=os.path.relpath(root / "index.html", output_path.parent),
        module_navigation=render_navigation(modules, root, output_path.parent),
        content_html=content_html,
        source_sha256=source_sha256(source),
    )


def build_site(root: Path, check: bool = False) -> list[Path]:
    manifest = load_manifest(root)
    errors = validate_manifest(manifest, root)
    if errors:
        raise ValueError("\n".join(errors))
    changed: list[Path] = []
    for module in manifest["modules"]:
        if module["status"] != "disponible":
            continue
        declared_output_path = root / str(module["output"])
        rendered = render_module(root, module, manifest)
        output_path = resolve_book_path(root, str(module["output"]))
        if check:
            output_is_stale = (
                not output_path.is_file()
                or output_path.read_text(encoding="utf-8") != rendered
            )
            if output_is_stale:
                changed.append(declared_output_path)
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        changed.append(declared_output_path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Construye el HTML estático del libro."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="No escribe; falla si el HTML está obsoleto.",
    )
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    changed = build_site(root, check=arguments.check)
    if arguments.check and changed:
        for path in changed:
            print(f"HTML_OBSOLETO: {path.relative_to(root)}")
        return 1
    for path in changed:
        print(f"GENERADO: {path.relative_to(root)}")
    if arguments.check:
        print("HTML_GENERADO_AL_DIA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
