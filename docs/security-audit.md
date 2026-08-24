# Auditoría final de seguridad previa a publicación

Fecha de ejecución: 2026-08-24.

Candidato auditado: `f2dd2973527dcd26d8cf5c4d958b28ebc2e528c1`.

Estado: **AUDITORÍA FINAL EN EL ALCANCE LOCAL PREVIO A PUBLICACIÓN**. La
revisión independiente y su re-review concluyeron con 0 hallazgos Critical y 0
Important abiertos. El ensayo desde clon limpio y los gates locales terminaron
correctamente. Las limitaciones de navegador, automatización remota y un Minor
de cobertura de inventario permanecen declaradas al final del documento.

## Alcance e inventario del candidato

El inventario se midió en un clon local limpio del candidato exacto, antes del
commit que publica este documento:

- Archivos versionados: 80; tamaño total: `2868713` bytes.
- Enlaces simbólicos versionados: 0.
- Archivos versionados mayores de 25 MiB: 0.
- Entornos virtuales, configuración local y payload descargado de Pyodide
  versionados: 0. El único elemento inicial bajo el directorio del runtime fue
  el marcador versionado `.gitkeep`, que no constituye un runtime.
- Notebooks versionados en todo el repositorio: exactamente 3, los tres
  aprobados y enumerados en Procedencia.

Los artefactos creados por la instalación quedaron ignorados y el estado
trackeado del clon permaneció limpio. Los conteos anteriores pertenecen al
candidato `f2dd297…`; el commit documental posterior cambia el historial y el
tamaño del árbol, pero no el código ni el material fuente.

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

- Árbol candidato: 0 secretos potenciales y 0 rutas personales.
- Historial del candidato: 14 commits mediante `git rev-list --all`.
- Cada commit se inventarió con `git ls-tree -rz --full-tree` y cada blob se
  materializó con `git cat-file` en un directorio temporal. `export-ignore` no
  puede excluir contenido histórico del escaneo.
- Hallazgos históricos no adjudicados: 0.
- Ocurrencias históricas adjudicadas: 10 en exactamente dos ubicaciones de
  checksum conocidas. La adjudicación exige detector, sintaxis exacta, valor
  aprobado y una única ocurrencia por ubicación y commit.
- Los informes muestran exclusivamente commit, ruta, línea y detector; nunca
  el valor candidato. Los fallos de Git o de las herramientas producen una
  categoría segura y hacen fallar el gate.

La validación cubre además rutas normalmente excluidas, blobs con
`export-ignore`, nombres con controles, nombres no UTF-8, symlinks, gitlinks,
modos no permitidos, rutas inseguras y duplicados.

## pip-audit 2.10.1

- Dependencias auditadas desde el lockfile: 124.
- Vulnerabilidades conocidas encontradas: 0.
- El gate del clon terminó con `SEGURIDAD_PUBLICACION_OK`.

## Notebooks

Modo: auditoría y reproducibilidad. Audiencia: estudiante en español. Entradas:
exactamente los tres notebooks aprobados. Cada notebook se copia byte a byte a
un directorio temporal, se ejecuta con cwd temporal y conserva el path original
sólo en el resumen. Una comprobación en `finally` protege y, si fuese necesario,
restaura el fuente incluso cuando `nbclient` falla:

- `01-series-dataframes.ipynb`: 23 celdas de código, 0 errores.
- `07-estadisticas-basicas.ipynb`: 40 celdas de código, 0 errores.
- `05-scale.ipynb`: 14 celdas de código, 0 errores.

La ejecución del clon informó 23/40/14 celdas de código, 0 errores y 3/3 hashes
idénticos. No se reescribió ningún notebook fuente.

## Gate funcional y commit documental

`verificar.sh` conserva `git diff --check` y además falla con un mensaje
genérico cuando `git status --porcelain --untracked-files=all` detecta cambios
modified, staged o untracked. Los artefactos ignorados permanecen permitidos.
Por diseño, al modificar este documento la ejecución precommit completa todos
los checks funcionales y falla únicamente en ese control final de worktree
sucio. Tras crear el commit documental se repiten ambos gates sobre el árbol
trackeado limpio; esa evidencia postcommit se conserva en el informe de trabajo
ignorado para evitar una retroedición circular de esta auditoría.

## Aceptación local y navegador

Se ejecutó `./instalar.sh --yes` y el runtime local terminó con
`PYODIDE_LOCAL_OK`. El launcher real se inició con
`./lanzar.sh --sin-jupyter --sin-navegador`, ligado a loopback. La portada y el
recurso principal de Pyodide respondieron HTTP 200. El proceso se detuvo
limpiamente con SIGINT y se comprobó que dejó de escuchar.

La aceptación interactiva de UI no se ejecutó. Tanto implementer como controller
confirmaron que la lista de navegadores controlables fue `[]`. Por ello no se
afirma haber ejecutado visualmente un ejercicio, cambiado la salida mediante un
hiperparámetro, abierto/cerrado una solución ni inspeccionado consola y red.

## Clon limpio

Se creó un clon local temporal desde el candidato exacto. La comprobación
inicial confirmó:

- `.venv`: ausente.
- Payload local de Pyodide: 0 archivos; sólo estaba el `.gitkeep` versionado.
- `configuracion/local.json`: ausente.

Resultados live dentro del clon:

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

Revisor: `/root/task_8_independent_reviewer`.

- Revisión integral original, rango `40a99d7..d6c838e`: 0 Critical, 5
  Important y 4 Minor.
- Re-review de correcciones, rango `d6c838e..f2dd297`: PASS; los 5 Important
  quedaron cerrados y no aparecieron nuevos Critical ni Important.
- Veredicto final: 0 Critical y 0 Important abiertos.

Tres Minor quedaron corregidos. Se difiere deliberadamente uno: el inventario
live global confirma exactamente tres `.ipynb`, pero el test automatizado de
inventario exacto sólo recorre `material_fuente/**/*.ipynb`; no impediría que
en el futuro se versionara un notebook adicional fuera de ese árbol.

## Limitaciones

- Minor abierto: el guard automatizado de inventario exacto sólo protege
  `material_fuente/**/*.ipynb`, aunque el inventario global live contiene
  exactamente los tres notebooks aprobados.
- La aceptación interactiva de navegador no fue posible; sólo existe evidencia
  HTTP loopback y del recurso principal de Pyodide con respuesta 200.
- GitHub Actions, protección de ramas, secret scanning, push protection y las
  funcionalidades o límites del plan de GitHub no se verificaron.
- No se modificaron remotos, no se hizo push y no se cambió visibilidad.
- Este documento no contiene tokens, valores candidatos ni rutas locales de la
  máquina de auditoría.
