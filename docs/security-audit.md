# Auditoría final de seguridad y publicación

Fecha de ejecución: 2026-08-24.

Candidato auditado y aprobado:
`ba94cd22fd3150dca4e884422174685751380eb7`.

Estado: **FINAL — PASS LOCAL Y DE REVISIÓN WHOLE-BRANCH, 0 CRITICAL Y 0
IMPORTANT**. El candidato `ba94cd2` dejó de estar en estado CANDIDATA tras la
re-review final. Este documento se confirma en un commit documental posterior;
ese commit no sustituye ni cambia el hash del candidato auditado y evita una
referencia circular. No existe evidencia nueva de CI remota, navegador
interactivo o funcionalidades de GitHub.

## Alcance e inventario del candidato

El árbol vivo de `ba94cd2` contiene 82 archivos versionados y `2920196` bytes,
0 symlinks y 0 archivos mayores de 25 MiB. El inventario Git global contiene
exactamente los 3 notebooks aprobados. No hay entornos virtuales, configuración
local ni payload descargado de Pyodide versionados; bajo el directorio del
runtime sólo se versiona `.gitkeep`.

El clon de ensayo partió con `.venv` ausente, 0 archivos de payload Pyodide
excluyendo `.gitkeep` y `configuracion/local.json` ausente. El índice y el
worktree estaban limpios antes de instalar y volvieron a estar limpios después
de completar todos los gates.

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

## Licencias y cita

- El código se publica bajo MIT mediante `LICENSE-CODE`.
- El texto educativo, los notebooks y los recursos visuales se publican bajo
  Creative Commons Attribution 4.0 Internacional mediante `LICENSE-CONTENT`.
- `CITATION.cff` identifica Easy Machine Learning, su autoría y la licencia MIT
  del software. No atribuye una fecha de release no verificada.
- `material_fuente/README.md` registra la autorización de redistribución, los
  hashes aprobados y el mapa auditable hacia el contenido construido.

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
- El Historial Git del candidato contiene 17 commits mediante
  `git rev-list --all`.
- Cada commit se inventarió con `git ls-tree -rz --full-tree` y cada blob se
  materializó con `git cat-file` en un directorio temporal. `export-ignore` no
  puede excluir contenido histórico del escaneo.
- La candidata contiene 26 supresiones actuales verificadas. La adjudicación
  exige ruta, línea, detector, sintaxis exacta, valor aprobado y exactamente una
  ocurrencia por ubicación y commit; cualquier otra supresión falla redactada.
- El gate ejecutado dentro del clon limpio adjudicó `actual=26`, `indice=26` e
  `historial=348`, sin hallazgos no adjudicados ni rutas personales.
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

Evidencia fresca dentro del clon limpio exacto de `ba94cd2`:

- `./instalar.sh --yes`: exit 0; `PYODIDE_LOCAL_OK` una vez y 31 archivos de
  runtime materializados sin ensuciar Git.
- `./verificar.sh`: exit 0; 106 pruebas Python, 21 JavaScript y 26 de
  publicación. El gate compuesto ejecutó las suites Python y JavaScript dos
  veces por su corte interno, y terminó con `VERIFICACION_COMPLETA_OK` una vez.
- Ruff, formato, contenido construido y validación estática: exit 0.
- Notebooks: exactamente 3 ejecutados, 23/40/14 celdas y 0 errores.
- `./verificar_seguridad.sh`: exit 0; `SEGURIDAD_PUBLICACION_OK` una vez y
  adjudicación `26/26/348` para actual, índice e historial.

`verificar.sh` también falla de forma genérica si
`git status --porcelain --untracked-files=all` detecta cambios modified, staged
o untracked; los artefactos ignorados permanecen permitidos. Las pruebas de
publicación usan el Python seleccionado por `uv` localmente y en `validar.yml`.
El commit posterior que contiene únicamente este documento se verifica de
nuevo, pero su commit y el incremento histórico se registran sólo en el informe
local ignorado para no perseguir una autorreferencia.

## Aceptación local y navegador

La candidata sustituye el docroot amplio por una allowlist de portada, assets
requeridos, runtime Pyodide y contenido construido; rechaza listados, dotfiles,
symlinks, escapes, configuración, scripts, fuentes, locks y `Host` que no sea
loopback con el puerto real. GET y HEAD tienen pruebas HTTP reales. El smoke del
clon limpio lanzó el handler seguro sin Jupyter: portada 200, ruta privada 404 y
`Host` atacante 400. Ctrl-C devolvió exit 0 y el puerto quedó libre. Una
regresión determinista cubre además la interrupción dentro del readiness HTTP y
exige cleanup del proceso ya creado.

La disponibilidad de browser control siguió siendo `[]`; la aceptación
interactiva de UI no se ejecutó. No se afirma haber ejecutado visualmente un
ejercicio, cambiado la salida mediante un hiperparámetro, abierto/cerrado una
solución ni inspeccionado consola y red.

## Clon limpio

Se creó un directorio temporal nuevo y se ejecutó `git clone --local .` desde
un worktree limpio en `ba94cd2`. El HEAD del clon coincidió con el hash completo
aprobado. Antes de instalar se verificó la ausencia real de `.venv`, de
`configuracion/local.json` y de payload Pyodide distinto de `.gitkeep`.

Dentro del clon se ejecutaron, en orden, `./instalar.sh --yes`,
`./verificar.sh`, `./verificar_seguridad.sh`, los hashes de los tres notebooks y
el smoke HTTP descrito arriba. Todos devolvieron exit 0 cuando correspondía; los
hashes coincidieron 3/3 y Git terminó con 0 entradas modified, staged o untracked
no ignoradas.

Tras salir del ensayo, se movió íntegramente su directorio raíz a la Papelera
con `/usr/bin/trash`. La ruta temporal original dejó de existir y el rehearsal
quedó recuperable desde la Papelera; no se eliminó permanentemente ningún
archivo.

## Revisión independiente

La revisión whole-branch inicial sobre `a81646b…` encontró 0 Critical,
6 Important y 6 Minor. Los 6 Important fueron fallback Jupyter, superficie
HTTP, supresiones, colisiones APFS, concurrencia de notebooks y matriz de
dependencias.

El commit `fd3d9a7853063ff931c94653e3780e4c5dd3a52e` corrigió esa ronda. Su
re-review dejó 0 Critical y 2 Important: sintaxis alternativas reconocidas por
`detect-secrets` quedaban fuera del segundo pase, y Ctrl-C durante readiness
HTTP podía dejar un hijo escuchando. El commit aprobado
`ba94cd22fd3150dca4e884422174685751380eb7` cerró ambos con regresiones
redactadas y cleanup determinista.

El reviewer original `/root/final_whole_branch_reviewer` volvió a revisar la
rama completa hasta `ba94cd2` y emitió **PASS: 0 Critical, 0 Important**. Este
veredicto cubre el candidato de código exacto; el commit documental posterior
contiene únicamente esta auditoría y no altera aquel candidato.

Los Minors asociados se corrigen con inventario global mediante
`git ls-files -z '*.ipynb'`, escaneo del índice, Python de publicación ligado a
`uv`, documentación de Python gestionado y configuración ejemplo mínima.

## Limitaciones

- Minor diferido: las descargas de Pyodide aún no incorporan timeout ni límite
  de bytes. Se mantiene fuera de esta ola para no alterar descargas grandes sin
  una verificación de tamaños y reintentos suficientemente conservadora.
- No se añade timeout automático a la ejecución Pyodide: la cancelación manual
  existente se conserva y este cambio queda explícitamente fuera del alcance.
- `pip-audit` se ejecutó localmente bajo macOS/Python 3.11; no se extrapola esa
  evidencia a Python 3.13.
- La matriz remota macOS/Python 3.13 no se ejecutó. GitHub Actions, protección
  de ramas, secret scanning, push protection y las funcionalidades o límites
  del plan de GitHub siguen pendientes de verificación.
- Browser control permaneció en `[]` y la UI interactiva no fue probada; sólo
  existe evidencia automatizada y HTTP loopback.
- No se modificaron remotos, no se hizo push y no se cambió visibilidad.
- Este documento no contiene tokens, valores candidatos ni rutas locales de la
  máquina de auditoría.
