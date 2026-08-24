# Auditoría de seguridad candidata post-fix

Fecha de ejecución: 2026-08-24.

Candidato original: `a81646b4f554409374c08b79c7f42f4a49d645c3`.
Base de esta ronda acotada: `fd3d9a7853063ff931c94653e3780e4c5dd3a52e`.

Estado: **CANDIDATA POST-FIX; NO ES UN PASS DE PUBLICACIÓN**. La revisión final
whole-branch de `40a99d7…a81646b` encontró 0 Critical, 6 Important y 6 Minor.
La primera ola implementó sus correcciones; la scoped re-review posterior de
`fd3d9a7` encontró 0 Critical y 2 Important adicionales: sintaxis alternativas
de supresión omitidas y Ctrl-C durante readiness HTTP sin cleanup. Esta ronda
implementa ambos fixes. Una nueva revisión de alcance exclusivo sobre esos dos
cambios encontró 0 Critical y 0 Important, pero no constituye aprobación global
ni cubrió este documento modificado en paralelo. No existe evidencia nueva de
CI, navegador interactivo o remoto.

## Alcance e inventario del candidato

El inventario post-fix contiene 82 archivos candidatos (los 80 versionados en
la base más el handler HTTP y su prueba), 0 symlinks, 0 archivos mayores de
25 MiB y exactamente los 3 notebooks aprobados mediante inventario Git global.

El inventario histórico siguiente pertenece al candidato previo `f2dd297…` y
se conserva sólo como trazabilidad de la auditoría anterior:

- Archivos versionados: 80; tamaño total: `2868713` bytes.
- Enlaces simbólicos versionados: 0.
- Archivos versionados mayores de 25 MiB: 0.
- Entornos virtuales, configuración local y payload descargado de Pyodide
  versionados: 0. El único elemento inicial bajo el directorio del runtime fue
  el marcador versionado `.gitkeep`, que no constituye un runtime.
- Notebooks versionados en todo el repositorio: exactamente 3, los tres
  aprobados y enumerados en Procedencia.

Los comandos completos y sus exits se registran también en el informe local
ignorado; los valores históricos anteriores no se reutilizan como evidencia de
la candidata actual.

## Procedencia

- Libro fuente: commit
  `d9d044f3892bf636d83f47001cb3a8fb7f41e9a0`, árbol
  `2363fbea93bb7d6ec3c06bd7fe68b6855194f9e3`.
- `material_fuente/notebooks/01-series-dataframes.ipynb`: SHA-256
  `15f0a0f4137ba81117f8bacf90dbd341828335963191b2fdc3a213650df510ea`.
- `material_fuente/notebooks/07-estadisticas-basicas.ipynb`: SHA-256
  `f4352008a8f973f496dba58c08740b250daac81b20b94ba3b1eac86b2221e30a`.
- `material_fuente/notebooks/05-scale.ipynb`: SHA-256
  `894a588d2eb24d02d032ac61a2f2961eef1920a9c6cfdb17e50948d0612dbeaf`.

## detect-secrets 1.5.0 e Historial Git

- El gate candidato añade un segundo pase `--only-allowlisted` para árbol
  actual, índice staged y cada snapshot del Historial Git. El pase recibe todos
  los candidatos, sin prefiltrado local ni réplica manual de las expresiones
  regulares de `detect-secrets`.
- Una vista temporal conserva rutas y líneas, representa archivos vacíos con
  una línea inocua y sustituye bytes no UTF-8 sólo para que el filtro fijado de
  `detect-secrets` pueda inspeccionar sus pragmas. La adjudicación se comprueba
  siempre contra el blob original y el registro cerrado.
- El índice se materializa con `git write-tree`; los blobs staged se escanean
  aunque el worktree contenga otra copia.
- La base de esta ronda contiene 16 commits mediante `git rev-list --all`; la
  candidata añade un único commit acotado.
- Cada commit se inventarió con `git ls-tree -rz --full-tree` y cada blob se
  materializó con `git cat-file` en un directorio temporal. `export-ignore` no
  puede excluir contenido histórico del escaneo.
- La candidata contiene 26 supresiones actuales verificadas. La adjudicación
  exige ruta, línea, detector, sintaxis exacta, valor aprobado y exactamente una
  ocurrencia por ubicación y commit; cualquier otra supresión falla redactada.
- El gate precommit de esta ronda adjudicó `actual=26`, `indice=26` e
  `historial=322`. El único snapshot nuevo contiene esas mismas 26 ubicaciones,
  por lo que el gate fresco postcommit debe adjudicar `historial=348`; el
  resultado ejecutado se conserva en el informe local ignorado.
- Los informes muestran exclusivamente commit, ruta, línea y detector; nunca
  el valor candidato. Los fallos de Git o de las herramientas producen una
  categoría segura y hacen fallar el gate.

La validación cubre además rutas normalmente excluidas, blobs con
`export-ignore`, nombres con controles, nombres no UTF-8, symlinks, gitlinks,
modos no permitidos, rutas inseguras, duplicados y colisiones portables mediante
normalización Unicode NFD más `casefold()` antes de materializar cualquier blob.

## pip-audit 2.10.1

- El gate local actual completó `pip-audit` bajo macOS/Python 3.11 sin
  vulnerabilidades conocidas; no se extrapola a Python 3.13.
- El workflow candidato usa una matriz explícita Ubuntu/Python 3.11 y
  macOS/Python 3.13, con `UV_PYTHON` ligado a cada entrada, sync locked y el gate
  completo. Así la rama `scipy` para Python >=3.12 se auditará en su entorno.
- La matriz no se ha ejecutado en GitHub Actions.

## Notebooks

Modo: auditoría y reproducibilidad. Audiencia: estudiante en español. Entradas:
exactamente los tres notebooks aprobados. Cada notebook se copia byte a byte a
un directorio temporal, se ejecuta con cwd temporal y conserva el path original
sólo en el resumen. Si el fuente cambia concurrentemente, la ejecución falla y
preserva los bytes nuevos; nunca escribe ni restaura el notebook original:

- `01-series-dataframes.ipynb`: 23 celdas de código, 0 errores.
- `07-estadisticas-basicas.ipynb`: 40 celdas de código, 0 errores.
- `05-scale.ipynb`: 14 celdas de código, 0 errores.

La ejecución post-fix confirmó 23/40/14 celdas de código, 0 errores y hashes
pre/post idénticos en los tres fuentes.

## Gate funcional y commit documental

`verificar.sh` conserva `git diff --check` y además falla con un mensaje
genérico cuando `git status --porcelain --untracked-files=all` detecta cambios
modified, staged o untracked. Los artefactos ignorados permanecen permitidos.
Las pruebas de publicación se ejecutan ahora con el Python seleccionado por
`uv` tanto localmente como en `validar.yml`. El gate precommit completó pruebas,
Ruff, contenido y notebooks, y devolvió exit 1 únicamente por el árbol dirty;
la evidencia postcommit se conserva en el informe de trabajo ignorado.

## Aceptación local y navegador

La candidata sustituye el docroot amplio por una allowlist de portada, assets
requeridos, runtime Pyodide y contenido construido; rechaza listados, dotfiles,
symlinks, escapes, configuración, scripts, fuentes, locks y `Host` que no sea
loopback con el puerto real. GET y HEAD tienen pruebas HTTP reales. Un smoke del
launcher confirmó recurso público y HEAD con 200, rutas privadas y Host atacante
sin 200, cierre limpio por Ctrl-C y puerto liberado. Una regresión determinista
adicional interrumpe `wait_for_port` después de crear HTTP y exige exit 0 más
cleanup del proceso creado.

La aceptación interactiva de UI no se ejecutó. Por ello no se
afirma haber ejecutado visualmente un ejercicio, cambiado la salida mediante un
hiperparámetro, abierto/cerrado una solución ni inspeccionado consola y red.

## Clon limpio

El Clon limpio documentado abajo corresponde a `f2dd297…`, no a esta candidata.
La comprobación anterior confirmó:

- `.venv`: ausente.
- Payload local de Pyodide: 0 archivos; sólo estaba el `.gitkeep` versionado.
- `configuracion/local.json`: ausente.

Resultados históricos dentro de aquel clon:

- `./instalar.sh --yes`: exit 0; `PYODIDE_LOCAL_OK` una vez.
- `./verificar.sh`: exit 0; `VERIFICACION_COMPLETA_OK` una vez.
- Suite Python del libro: 85/85; el gate compuesto la ejecutó dos veces.
- Suite JavaScript: 21/21; el gate compuesto la ejecutó dos veces.
- Suite de publicación: 22/22.
- Notebooks ejecutados: 3; 23/40/14 celdas de código y 0 errores.
- `./verificar_seguridad.sh`: exit 0;
  `SEGURIDAD_PUBLICACION_OK` una vez.
- Hashes de notebooks coincidentes: 3/3.
- Entradas trackeadas o no ignoradas tras instalar y verificar: 0.

Al finalizar se salió del clon y se movió íntegramente su directorio raíz a la
Papelera con `/usr/bin/trash`. La ruta de trabajo dejó de existir y el ensayo
quedó recuperable en la Papelera.

## Revisión independiente

La revisión whole-branch final verificó 0 Critical, 6 Important y 6 Minor sobre
la base `a81646b…`. Los 6 Important fueron: fallback Jupyter, superficie HTTP,
supresiones, colisiones APFS, concurrencia de notebooks y matriz de dependencias.
La scoped re-review de la primera corrección encontró 0 Critical y 2 Important:
el prefiltrado del segundo pase omitía sintaxis reconocidas por la dependencia,
y Ctrl-C durante readiness HTTP podía dejar el hijo escuchando. Esta candidata
incluye regresiones y fixes para ambos. La re-review exclusiva de este diff
encontró 0 Critical y 0 Important, con 51/51 focales; excluyó el documento de
auditoría modificado concurrentemente y no declara un veredicto de publicación.

Los Minors asociados se corrigen con inventario global mediante
`git ls-files -z '*.ipynb'`, escaneo del índice, Python de publicación ligado a
`uv`, documentación de Python gestionado y configuración ejemplo mínima.

## Limitaciones

- Minor diferido: las descargas de Pyodide aún no incorporan timeout ni límite
  de bytes. Se mantiene fuera de esta ola para no alterar descargas grandes sin
  una verificación de tamaños y reintentos suficientemente conservadora.
- No se añade timeout automático a la ejecución Pyodide: la cancelación manual
  existente se conserva y este cambio queda explícitamente fuera del alcance.
- La scoped re-review completada fue exclusiva de estos dos fixes y dejó fuera
  el documento de auditoría concurrente; no es una aprobación global. Los gates
  postcommit del informe local tampoco sustituyen ese veredicto de publicación.
- La aceptación interactiva de navegador no fue posible; sólo existe evidencia
  HTTP loopback y del recurso principal de Pyodide con respuesta 200.
- GitHub Actions, protección de ramas, secret scanning, push protection y las
  funcionalidades o límites del plan de GitHub no se verificaron.
- No se modificaron remotos, no se hizo push y no se cambió visibilidad.
- Este documento no contiene tokens, valores candidatos ni rutas locales de la
  máquina de auditoría.
