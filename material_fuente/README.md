# Procedencia del material fuente

Los tres notebooks de esta carpeta se conservaron byte por byte respecto a
las fuentes aprobadas. Su redistribución bajo CC BY 4.0 fue confirmada por el
propietario del repositorio el 2026-08-23.

| Archivo | SHA-256 aprobado | Ruta original en el vault | Contribución al módulo 01 |
| --- | --- | --- | --- |
| `01-series-dataframes.ipynb` | `15f0a0f4137ba81117f8bacf90dbd341828335963191b2fdc3a213650df510ea` | `01-machine-learning/01-sesiones/03-analisis-datos/01-series-dataframes.ipynb` | Formas, ejes y estructuras Series/DataFrame. |
| `07-estadisticas-basicas.ipynb` | `f4352008a8f973f496dba58c08740b250daac81b20b94ba3b1eac86b2221e30a` | `01-machine-learning/01-sesiones/03-analisis-datos/07-estadisticas-basicas.ipynb` | Estadística descriptiva, centro y dispersión. |
| `05-scale.ipynb` | `894a588d2eb24d02d032ac61a2f2961eef1920a9c6cfdb17e50948d0612dbeaf` | `01-machine-learning/01-sesiones/05-modelado-datos/05-pipelines-y-preprocesados/05-scale.ipynb` | Escalado y preprocesado de variables. |

El módulo 01 reescribe esos conceptos como experimentos breves sobre datos de
running. El mapa auditable entre el contenido y sus fuentes está en
[`libro_ml_dl/contenido_fuente/mapa_fuentes.json`](../libro_ml_dl/contenido_fuente/mapa_fuentes.json).
Los hashes se verifican con `./verificar.sh` y cualquier cambio de un solo byte
en los notebooks hace fallar la validación de procedencia.
