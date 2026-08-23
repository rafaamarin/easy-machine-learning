# Easy Machine Learning: diseño de publicación independiente

Fecha: 2026-08-23  
Estado: aprobado en conversación; pendiente de implementación

## 1. Objetivo

Crear `rafaamarin/easy-machine-learning` como repositorio privado e independiente
que distribuya el primer corte del libro interactivo de Machine Learning junto
con los tres notebooks que documentan su procedencia. El resultado debe poder
instalarse, validarse y ejecutarse de forma reproducible en hardware de consumo.

El repositorio nace con historial Git limpio. No hereda el historial ni archivos
ajenos del vault UNIR.

## 2. Criterios de éxito

1. El repositorio privado existe en GitHub bajo la cuenta `rafaamarin`.
2. Un clon nuevo funciona en macOS, Linux y Windows mediante WSL con Python 3.11+
   y `uv`.
3. La instalación se completa con `./instalar.sh` y el producto arranca con
   `./lanzar.sh`.
4. El libro funciona en modo web local y ofrece JupyterLab desde el entorno del
   proyecto cuando está instalado.
5. Los tres notebooks citados se incluyen byte por byte y su procedencia queda
   trazada.
6. Pyodide se descarga de forma transaccional y cada artefacto se verifica por
   SHA-256; sus aproximadamente 303 MB locales no se versionan.
7. El gate local, la ejecución aislada de notebooks, el escaneo de secretos y la
   auditoría de dependencias terminan en verde antes del primer push.
8. CI repite las verificaciones relevantes en Ubuntu y macOS.
9. La portada del README incorpora un banner propio y accesible.
10. No se publica ninguna credencial, configuración personal ni ruta absoluta
    de la máquina de desarrollo.

## 3. Alcance

### Incluido

- El directorio versionado `libro_ml_dl/` del corte 01.
- Los notebooks fuente:
  - `01-series-dataframes.ipynb`.
  - `07-estadisticas-basicas.ipynb`.
  - `05-scale.ipynb`.
- Scripts raíz para instalar y lanzar el producto.
- Documentación de descarga, ejecución, reproducción y resolución de problemas.
- Licencias separadas para código y contenido.
- Metadatos de citación, seguridad y contribución.
- CI, auditoría de dependencias y detección de secretos.
- Un banner de marca sin texto generado dentro de la imagen.

### Excluido

- El resto del vault UNIR.
- `.venv`, caches, configuración local y binarios descargados de Pyodide.
- TensorFlow y PyTorch como dependencias del navegador en este corte.
- Soporte nativo de Windows fuera de WSL.
- Despliegue público o GitHub Pages.
- Publicación de secretos activos, incluso si aparecieran en material fuente.

## 4. Restricciones y decisiones vinculantes

- Visibilidad inicial: privada.
- Propietario GitHub: `rafaamarin`.
- Slug: `easy-machine-learning`.
- Título visible: `Easy Machine Learning`.
- El usuario confirmó permiso para redistribuir los tres notebooks.
- Código bajo MIT; texto, notebooks y recursos visuales bajo CC BY 4.0.
- macOS y Linux son nativos; Windows usa WSL.
- El diseño favorece scripts simples y dependencias bloqueadas con `uv`.
- Los notebooks se preservan; cualquier ejecución de validación usa copias
  temporales y no reescribe los originales.

## 5. Estructura del repositorio

```text
easy-machine-learning/
├── README.md
├── LICENSE-CODE
├── LICENSE-CONTENT
├── CITATION.cff
├── CONTRIBUTING.md
├── SECURITY.md
├── REPRODUCIBILITY.md
├── instalar.sh
├── lanzar.sh
├── verificar.sh
├── assets/
│   └── branding/
│       └── easy-machine-learning-banner.png
├── libro_ml_dl/
│   ├── assets/
│   ├── configuracion/
│   ├── contenido/
│   ├── contenido_fuente/
│   ├── datos/
│   ├── pruebas/
│   ├── scripts/
│   ├── pyproject.toml
│   └── uv.lock
├── material_fuente/
│   ├── README.md
│   └── notebooks/
│       ├── 01-series-dataframes.ipynb
│       ├── 07-estadisticas-basicas.ipynb
│       └── 05-scale.ipynb
├── docs/
│   ├── security-audit.md
│   └── superpowers/
└── .github/
    ├── dependabot.yml
    └── workflows/
        ├── validar.yml
        └── seguridad.yml
```

Mantener `libro_ml_dl/` como subdirectorio reduce cambios de rutas y conserva el
builder ya probado. Los wrappers raíz ofrecen la interfaz simple del repositorio.

## 6. Flujo de usuario

### Clonar

Mientras el repositorio sea privado:

```bash
gh repo clone rafaamarin/easy-machine-learning
cd easy-machine-learning
```

También se documentará `git clone` para usuarios autenticados y la descarga ZIP
desde la interfaz de GitHub.

### Instalar

```bash
./instalar.sh
```

El script:

1. Comprueba Python 3.11+ y `uv` sin instalarlos globalmente.
2. Sincroniza las dependencias exactas desde `uv.lock`.
3. Instala JupyterLab, `ipykernel`, NumPy, pandas y scikit-learn en `.venv`.
4. Descarga Pyodide solo tras confirmación o mediante una opción explícita no
   interactiva usada por CI.
5. Verifica el manifiesto y los hashes antes de publicar el runtime local.

### Ejecutar

```bash
./lanzar.sh
```

El wrapper entra en `libro_ml_dl/` y ejecuta el lanzador Python. La web y
JupyterLab se enlazan exclusivamente a `127.0.0.1`. Si Jupyter no arranca, el
libro sigue disponible y muestra un diagnóstico accionable.

### Verificar

```bash
./verificar.sh
```

El comando ejecuta formato, lint, tests Python, tests JavaScript, validación
editorial, HTML determinista, hashes del runtime y smokes que no requieren UI.

## 7. Material fuente y reproducibilidad

Los tres notebooks se copian byte por byte a `material_fuente/notebooks/`. El
mapa de procedencia se actualiza a rutas relativas dentro del nuevo repositorio.
`material_fuente/README.md` documenta título, ubicación original, relación con el
módulo 01, permiso de redistribución confirmado y licencia aplicable.

Los notebooks no dependen de datasets externos. Sus importaciones se limitan a
NumPy, pandas y scikit-learn. CI los ejecuta de principio a fin en un directorio
temporal y falla ante cualquier output de error. Los originales versionados no
reciben outputs nuevos ni cambios de metadata.

`REPRODUCIBILITY.md` fija:

- sistemas soportados;
- versión mínima de Python;
- instalación de `uv` mediante enlace oficial;
- comandos exactos desde un clon vacío;
- versiones de dependencias y estrategia de lockfile;
- preparación y verificación de Pyodide;
- modo ligero sin Jupyter;
- límites conocidos y solución de errores frecuentes.

## 8. Correcciones obligatorias antes de publicar

1. En el cliente Pyodide, invalidar y terminar el worker fallido antes de
   rechazar promesas o invocar listeners externos. Las excepciones de listeners
   no pueden impedir la limpieza.
2. En el validador editorial, resolver la fuente con el helper confinado y no
   abrir rutas que ya hayan sido rechazadas por el manifiesto.
3. Tratar la presencia de `?jupyter_url=` como entrada aunque esté vacía:
   descartarla, limpiar `sessionStorage` y retirar la query.
4. Añadir regresiones focales para reentrancia, listener que lanza, ruta externa
   y query vacía.

No se crea el repositorio remoto hasta que una revisión independiente confirme
que no quedan hallazgos Critical o Important.

## 9. Seguridad

### Pre-push local

- `detect-secrets` sobre todos los archivos candidatos, sin mostrar valores.
- Reglas focales para claves privadas, tokens GitHub/OpenAI, AWS y asignaciones
  típicas de credenciales.
- `pip-audit` sobre las dependencias exportadas desde el lockfile.
- Inventario de archivos, symlinks y tamaños.
- Búsqueda de rutas absolutas y configuraciones locales.
- Confirmación de que `.venv`, runtime Pyodide, caches y `local.json` están
  ignorados.

Los únicos dos hallazgos de entropía del escaneo inicial son checksums SHA-256
esperados y se documentan como falsos positivos por ubicación, no por valor.

### CI

- El workflow de seguridad se ejecuta en cada push y pull request.
- Las herramientas se fijan a versiones concretas.
- Dependabot revisa GitHub Actions y dependencias Python cuando GitHub lo
  soporte para el repositorio privado.
- Se habilitan alertas de vulnerabilidades y secret scanning cuando la cuenta y
  el plan de GitHub lo permitan.

Una credencial real detiene la publicación. Se informa su archivo y categoría,
pero nunca se imprime ni se sube. Debe eliminarse y rotarse antes de continuar.

## 10. CI y estrategia de pruebas

`validar.yml` usa Ubuntu y macOS con versiones representativas de Python 3.11 y
3.13. Las suites rápidas se ejecutan en la matriz. Un job Ubuntu adicional:

1. prepara Pyodide desde cero;
2. verifica hashes;
3. ejecuta el gate completo;
4. ejecuta los tres notebooks en copias temporales.

Node se usa solo para pruebas del frontend; no es requisito para leer o ejecutar
el libro en el navegador.

El gate de publicación exige:

- Ruff limpio;
- todos los tests Python y JavaScript verdes;
- HTML generado al día;
- notebooks sin outputs de error durante ejecución aislada;
- cero secretos no clasificados;
- cero vulnerabilidades conocidas sin adjudicación;
- cero rutas personales;
- worktree limpio.

## 11. Marca y presentación

El banner sigue la dirección “From pixels to intelligence”:

- formato panorámico;
- fondo oscuro tipo blueprint técnico;
- transición visual de píxeles a tensores, red neuronal y bloques de atención;
- paleta azul eléctrico, cian y un acento cálido moderado;
- sin texto, logos de terceros, marcas de agua ni rostros;
- contraste suficiente y composición legible en GitHub.

El README coloca el título como HTML/Markdown accesible, no dentro de la imagen.
Incluye una descripción honesta del corte disponible, captura de capacidades,
quickstart, estructura, roadmap, licencias y badges de CI/seguridad.

Metadatos iniciales:

- descripción: “Libro interactivo y práctico de Machine Learning en español,
  ejecutable localmente con Pyodide y JupyterLab”.
- topics: `machine-learning`, `python`, `jupyter`, `pyodide`, `education`,
  `spanish`, `local-first`.

No se anuncian TensorFlow, PyTorch, visión o transformers como contenido ya
disponible; permanecen en el roadmap.

## 12. Secuencia de publicación

1. Crear el repositorio local con historial limpio.
2. Importar el libro y los notebooks de forma explícita.
3. Corregir los hallazgos bloqueantes mediante TDD.
4. Añadir portabilidad, documentación, licencias, CI y branding.
5. Ejecutar revisión de código independiente.
6. Ejecutar gate funcional y de seguridad desde estado limpio.
7. Crear `rafaamarin/easy-machine-learning` como repositorio privado.
8. Añadir `origin`, empujar `main` y verificar el commit remoto.
9. Configurar descripción, topics y controles compatibles con la cuenta.
10. Entregar URL, commit, comandos de clonación y resultados de auditoría.

El cambio a visibilidad pública queda fuera de esta entrega y exige una orden
posterior explícita.

## 13. Manejo de fallos

- Si un escáner encuentra un secreto, no se crea ni actualiza el remoto.
- Si un notebook no ejecuta, se conserva el original y se informa la celda y la
  dependencia; no se oculta el error borrando outputs.
- Si CI difiere del entorno local, el repositorio permanece privado y se corrige
  la causa antes de declarar reproducibilidad.
- Si GitHub rechaza configuración opcional, el push no se revierte; se informa
  qué protección depende del plan de cuenta.
- Si el nombre remoto ya existe, no se sobrescribe: se detiene la publicación y
  se solicita otro slug.

## 14. Aceptación final

La entrega termina únicamente cuando:

- el commit local y `origin/main` coinciden;
- la URL privada es accesible para `rafaamarin`;
- los comandos documentados se han probado desde una copia limpia o un entorno
  equivalente;
- el banner está versionado y referenciado correctamente;
- las tres fuentes están incluidas y trazadas;
- las licencias están presentes;
- la auditoría de seguridad está documentada sin exponer valores;
- no quedan hallazgos Critical o Important;
- cualquier límite de navegador o CI no verificable se declara explícitamente.
