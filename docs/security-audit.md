# Auditoría de seguridad candidata — Fase A

Fecha de ejecución: 2026-08-24.

Estado: **AUDITORÍA CANDIDATA**. La base auditada es
`91c6cb1a248cf45397ebe459f7d968fedb5f7890`. El commit resultante de Fase A se
registra después de crearlo en el informe de trabajo ignorado. La candidatura
no es final hasta completar la revisión independiente y el ensayo desde clon
limpio de Fase B.

## Alcance e inventario

- Candidato de Fase A: 80 archivos, `2847187` bytes totales.
- Enlaces simbólicos versionados: 0.
- Archivos versionados mayores de 25 MiB: 0.
- Entornos locales, cachés, configuración local y descargas de runtime
  versionados: 0. El runtime Pyodide instalado permanece ignorado.
- Política del escáner: los symlinks y los nombres de archivo no UTF-8 fallan
  cerrados; los controles de nombres se escapan antes de imprimir metadatos.

El inventario se calculó sobre el árbol candidato de Fase A, incluida esta
auditoría y la prueba de higiene, antes de crear el commit.

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

- Árbol de trabajo candidato: 0 secretos potenciales y 0 rutas personales.
- Historial Git examinado en vivo: 12 commits mediante `git rev-list --all`;
  cada árbol se exportó con `git archive` a un directorio temporal.
- Hallazgos no adjudicados: 0.
- Se adjudicaron 10 ocurrencias históricas en exactamente dos ubicaciones de
  checksum conocidas. La adjudicación exige detector y contexto, no sólo ruta:
  `libro_ml_dl/scripts/preparar_entorno.py:17` y
  `libro_ml_dl/pruebas/python/test_preparar_entorno.py:81`.
- Los informes contienen exclusivamente commit, ruta, línea y detector; no
  contienen el valor candidato. Una prueba con repositorio temporal y una
  credencial sintética confirmó la redacción y el fallo cerrado.

## pip-audit 2.10.1

- Dependencias auditadas desde el lockfile: 124.
- Vulnerabilidades conocidas encontradas: 0.
- El gate `./verificar_seguridad.sh` terminó con
  `SEGURIDAD_PUBLICACION_OK`.

## Notebooks

Los tres notebooks aprobados se ejecutaron en memoria con el intérprete del
proyecto, sin reescribir los archivos fuente:

- `01-series-dataframes.ipynb`: 23 celdas de código, 0 errores.
- `07-estadisticas-basicas.ipynb`: 40 celdas de código, 0 errores.
- `05-scale.ipynb`: 14 celdas de código, 0 errores.

Los SHA-256 anteriores permanecieron idénticos antes y después de la ejecución.

## Aceptación local

Se ejecutó `./instalar.sh --yes` y el runtime local terminó con
`PYODIDE_LOCAL_OK`. El launcher real se inició con
`./lanzar.sh --sin-jupyter --sin-navegador`, ligado a loopback. La portada y el
recurso principal de Pyodide respondieron HTTP 200. El proceso se detuvo
limpiamente con SIGINT y se comprobó que dejó de escuchar.

La aceptación interactiva no se ejecutó: la sesión no ofrecía ningún navegador
controlable. Por tanto, quedan pendientes la ejecución visual de un ejercicio,
el cambio de salida mediante un hiperparámetro, la apertura y cierre de una
solución y la inspección de consola/red.

## Clon limpio

**Pendiente Fase B.** No se ha creado ni ensayado un clon limpio en esta fase.

## Revisión independiente

**Pendiente Fase B.** No se afirma todavía que existan cero hallazgos Critical
o Important.

## Limitaciones

- La aceptación interactiva con navegador queda pendiente por indisponibilidad
  de la herramienta en esta sesión.
- El clon limpio y la revisión independiente quedan pendientes de Fase B.
- No se ha creado ningún remoto ni se han verificado GitHub Actions, protección
  de ramas, secret scanning, push protection o límites del plan de la cuenta.
- Este documento no contiene tokens, valores candidatos ni rutas locales de la
  máquina de auditoría.
