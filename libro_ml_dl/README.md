# Easy Machine Learning: libro interactivo

Ejecuta la instalación y el lanzamiento con los wrappers de la raíz del
repositorio:

```bash
./instalar.sh
./lanzar.sh
```

La instalación pide confirmación, descarga Pyodide 314.0.5, verifica SHA-256 y
prepara el entorno local opcional de JupyterLab. No registra kernels globales.

## Modo ligero

```bash
./lanzar.sh --sin-jupyter
```

Abre la URL `Libro:` que muestra el launcher. Lectura, progreso y Pyodide
funcionan; Jupyter no se inicia. El servidor sólo publica los HTML construidos
y assets requeridos: no sirve configuración, scripts, fuentes, entornos,
locks, dotfiles ni listados de directorio.

## Verificación

```bash
./verificar.sh
./verificar_seguridad.sh
```

Ambos comandos se ejecutan desde la raíz. Validan estructura, pruebas,
contenido, notebooks, procedencia, estilo, secretos y dependencias. Ninguna
validación estática sustituye el smoke test visual indicado abajo.

## Smoke test visual

1. Ejecuta los cinco laboratorios.
2. Comprueba las dos figuras del módulo 01.
3. Modifica un valor y observa otra salida.
4. Cancela `while True: pass` y reinicia el laboratorio.
5. Marca checkpoints, recarga y verifica persistencia.
6. Prueba teclado, tema oscuro y ancho de 768 px.

## Problemas frecuentes

- `AVISO: Pyodide no está preparado.`: ejecuta `./instalar.sh` desde la raíz.
- `AVISO: Jupyter no encontrado; continúa el modo web.`: el libro sigue
  disponible y JupyterLab queda desactivado.
- `AVISO: JupyterLab no pudo iniciarse; continúa el modo web.`: repite la
  instalación y revisa únicamente la configuración local; el libro web sigue
  activo.
- Puerto ocupado: el lanzador selecciona otro y muestra la URL real.
- La página abierta con `file://` no funciona: usa uno de los servidores
  locales.
