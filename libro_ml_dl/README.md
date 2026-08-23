# ML/DL haciendo

## Preparación inicial

```bash
uv sync --group validation
uv run python scripts/preparar_entorno.py
```

La segunda orden pide confirmación, descarga Pyodide 314.0.5 y verifica
SHA-256. No instala kernels.

## Modo completo

```bash
./lanzar.sh
```

Abre la web y JupyterLab local si está disponible. TensorFlow usa `unir-tf`.
PyTorch no forma parte de este corte.

## Modo ligero

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Abre `http://127.0.0.1:8000`. Lectura, progreso y Pyodide funcionan; Jupyter
no se inicia.

## Verificación

```bash
uv run --group validation python scripts/verificar_corte_01.py
```

`VALIDACION_ESTATICA_OK` valida estructura.
`CORTE_01_VALIDACION_LOCAL_OK` confirma además pruebas y artefactos locales.
Ninguna sustituye el smoke test visual indicado abajo.

## Smoke test visual

1. Ejecuta los cinco laboratorios.
2. Comprueba las dos figuras del módulo 01.
3. Modifica un valor y observa otra salida.
4. Cancela `while True: pass` y reinicia el laboratorio.
5. Marca checkpoints, recarga y verifica persistencia.
6. Prueba teclado, tema oscuro y ancho de 768 px.

## Problemas frecuentes

- `Pyodide no encontrado`: ejecuta la preparación inicial.
- `unir-tf no aparece`: revisa `jupyter kernelspec list`.
- `Jupyter no se encuentra en un worktree`: usa
  `--jupyter-ejecutable /ruta/al/jupyter`.
- Puerto ocupado: el lanzador selecciona otro y muestra la URL real.
- La página abierta con `file://` no funciona: usa uno de los servidores
  locales.

## Configuración local en un worktree

`configuracion/local.json` está ignorado por Git. Su `vault_root` puede apuntar
al checkout que contiene los notebooks cuando trabajas desde un worktree; el
lanzador usa esa raíz para iniciar JupyterLab.
