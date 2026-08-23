![De píxeles a tensores, redes y atención](assets/branding/easy-machine-learning-banner.png)

# Easy Machine Learning

Una ruta práctica y reproducible en español para aprender machine learning
desde los datos y sus formas mediante explicaciones breves y laboratorios
editables que se ejecutan localmente.

[![Validación](https://github.com/rafaamarin/easy-machine-learning/actions/workflows/validar.yml/badge.svg)](https://github.com/rafaamarin/easy-machine-learning/actions/workflows/validar.yml)
[![Seguridad](https://github.com/rafaamarin/easy-machine-learning/actions/workflows/seguridad.yml/badge.svg)](https://github.com/rafaamarin/easy-machine-learning/actions/workflows/seguridad.yml)

## Disponible ahora

- Plataforma web local con navegación, progreso persistente y tema claro u
  oscuro.
- Módulo 00: contrato de estudio y primer microexperimento NumPy.
- Módulo 01: datos, formas, estadística descriptiva y escalado.
- Cinco laboratorios editables y ejecutables.
- Dos figuras didácticas del módulo 01.
- Ejecución local en el navegador mediante Pyodide.
- JupyterLab opcional dentro del entorno del proyecto.

## Descargar

El repositorio es privado. Las tres opciones requieren una cuenta con acceso y
autenticación previa; no existe una descarga pública anónima.

Con GitHub CLI:

```bash
gh auth login
gh repo clone rafaamarin/easy-machine-learning
```

Con Git y una clave SSH autorizada:

```bash
git clone git@github.com:rafaamarin/easy-machine-learning.git
```

Para descargar un ZIP, inicia sesión en GitHub con una cuenta autorizada, abre
el repositorio privado y elige **Code → Download ZIP**. Descomprime el archivo
antes de continuar.

## Instalar y ejecutar

Se requiere Python 3.11 o posterior, `uv` y conexión de red durante la primera
instalación. Desde la raíz del clon:

```bash
./instalar.sh
./lanzar.sh
```

La instalación solicita confirmación antes de descargar el runtime local de
Pyodide. El lanzador publica únicamente en loopback y abre el libro; si el
entorno de Jupyter está disponible, también inicia JupyterLab local.

## Reproducir y verificar

```bash
./verificar.sh
./verificar_seguridad.sh
```

La primera orden valida pruebas Python y JavaScript, estilo, contenido,
notebooks y procedencia. La segunda busca secretos y rutas personales y audita
las dependencias. Consulta la guía de
[reproducibilidad](REPRODUCIBILITY.md) para CI, modo ligero y diagnóstico.

## Estructura del repositorio

```text
.
├── assets/branding/          # identidad visual del proyecto
├── libro_ml_dl/              # plataforma, contenido y pruebas del libro
│   ├── contenido_fuente/     # módulos y laboratorios editables
│   ├── pruebas/              # validaciones Python y JavaScript
│   └── scripts/              # construcción, lanzamiento y verificación
├── material_fuente/          # notebooks aprobados y su procedencia
├── pruebas_publicacion/      # contratos de publicación del repositorio
├── instalar.sh               # instalación reproducible desde la raíz
├── lanzar.sh                 # lanzamiento local desde la raíz
├── verificar.sh              # verificación funcional y de procedencia
└── verificar_seguridad.sh    # verificación de seguridad
```

## Procedencia de los notebooks

Los tres notebooks fuente se preservan byte por byte y sus SHA-256 aprobados,
rutas originales y contribuciones al módulo 01 están documentados en
[`material_fuente/README.md`](material_fuente/README.md).

## Roadmap

Los siguientes bloques están planificados y **todavía no están disponibles**:

- TensorFlow.
- PyTorch.
- Visión por computador.
- Transformers.
- Ingeniería de sistemas de ML/DL.
- Proyectos integradores.

## Licencias y cita

El código se distribuye bajo la [licencia MIT](LICENSE-CODE). El texto
educativo, los notebooks y los activos visuales se distribuyen bajo
[Creative Commons Attribution 4.0 Internacional](LICENSE-CONTENT). Los metadatos
de cita están en [`CITATION.cff`](CITATION.cff), versión `0.1.0`, publicada el
2026-08-23.

## Plataformas y limitaciones

- Soporte: macOS y Linux en arm64/x86_64; Windows únicamente mediante WSL 2.
- Python 3.11 o posterior y `uv` son obligatorios; Node.js se necesita para la
  batería completa de pruebas JavaScript.
- La primera instalación de Pyodide necesita red y espacio local; los binarios
  generados no se incluyen en Git.
- Los servicios se vinculan a `127.0.0.1`; no se ofrece despliegue remoto.
- JupyterLab es opcional. El modo web ligero sigue disponible sin Jupyter.
- No se requiere GPU y los módulos avanzados del roadmap aún no forman parte
  de esta versión.
