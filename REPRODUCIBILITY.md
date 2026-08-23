# Reproducibilidad

Este repositorio es privado: antes de seguir estos pasos, la cuenta o clave
usada para clonar debe tener acceso concedido.

## Sistemas soportados

- macOS arm64/x86_64.
- Linux arm64/x86_64.
- Windows mediante WSL 2.
- Python 3.11 o posterior.

## Desde un clon vacío

```bash
gh repo clone rafaamarin/easy-machine-learning
cd easy-machine-learning
./instalar.sh
./verificar.sh
./lanzar.sh
```

## Instalación no interactiva para CI

```bash
./instalar.sh --yes
```

## Modo web ligero

```bash
cd libro_ml_dl
python3 -m http.server 8000 --bind 127.0.0.1
```

## Qué no modifica la instalación

No instala kernels globales, no escribe fuera del repositorio salvo caches de
`uv`, no cambia los notebooks fuente y no expone servicios fuera de loopback.

## Solución de problemas

- **Falta `uv`.** El instalador termina con
  `ERROR: instala uv desde https://docs.astral.sh/uv/getting-started/installation/`.
  Instálalo desde esa URL, abre una terminal nueva y repite `./instalar.sh`.
- **Puerto ocupado.** El lanzador prueba el puerto solicitado y los 99
  siguientes. Si todo el intervalo está ocupado, muestra
  `No hay puerto libre entre 8000 y 8099`. Libera un puerto o elige otro con
  `./lanzar.sh --puerto-web 9000 --puerto-jupyter 9888`.
- **Pyodide ausente.** El modo web avisa
  `AVISO: Pyodide no está preparado. Ejecuta 'uv run python scripts/preparar_entorno.py'.`.
  Desde la raíz, ejecuta `./instalar.sh`; si antes cancelaste la descarga verás
  `Descarga cancelada; no se modificó el runtime.`.
- **WSL no abre el navegador.** Ejecuta `./lanzar.sh --sin-navegador` y abre
  manualmente en el navegador del host la URL que sigue a `Libro:`. El
  servicio continúa limitado a `127.0.0.1`.
- **Jupyter no está disponible.** El lanzador muestra
  `AVISO: Jupyter no encontrado; continúa el modo web.` y mantiene el libro en
  modo web. Repite `./instalar.sh` para reconstruir el entorno opcional. Si
  proporcionas una ruta inválida con `--jupyter-ejecutable`, el error empieza
  por `Jupyter no existe:`.
