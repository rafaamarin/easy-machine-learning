# Machine Learning y Deep Learning haciendo

Construye. Ejecuta. Cambia una cosa. Mira qué ocurre.

## Cómo usar esta guía {#como_usar}

1. Lee el reto.
2. Predice el resultado.
3. Ejecuta el código.
4. Modifica un valor.
5. Marca la comprobación cuando puedas explicarlo.

El navegador resuelve experimentos breves. TensorFlow y PyTorch se abrirán en JupyterLab cuando el recorrido necesite Python nativo.

> No memorices la salida. Provócala y explica por qué cambió.

<label>
  <input type="checkbox" data-progress-id="00_inicio:como_usar">
  Puedo explicar el ciclo: predecir → ejecutar → modificar → interpretar.
</label>

<progress class="progress-meter" data-progress-meter aria-label="Progreso del módulo" value="0" max="2"></progress>
<output data-progress-text>0 de 2</output>

## Reto: ¿hay mejora? {#primer_experimento data-pedagogy="reto"}

Cinco tiempos representan cinco sesiones de 5 km. Antes de ejecutar: ¿cuántos minutos separan la primera y la última sesión?

<py-lab data-lab-id="00_primer_experimento" data-src="contenido_fuente/00_inicio/labs/00_primer_experimento.py" data-packages="numpy" data-title="Mide una mejora"></py-lab>

<details markdown="1" data-static-output-for="00_primer_experimento">
<summary>Salida de referencia si Python no carga</summary>

```text
Sesiones: 5
Primer 5 km: 32 min
Último 5 km: 28 min
Mejora observada: 4 min
```
</details>

### Observa {data-pedagogy="observa"}

La resta cuantifica el cambio. Todavía no demuestra que el entrenamiento lo causó. Solo describe estos cinco registros.

### Modifica {data-pedagogy="modifica"}

Cambia el último `28` por `33`. Ejecuta otra vez. Explica por qué `mejora_min` pasa a ser negativo.

<details markdown="1" data-hint>
<summary>Pista</summary>

La operación siempre es `primer tiempo - último tiempo`.
</details>

<details markdown="1" data-solution>
<summary>Solución razonada</summary>

Con `33`, la resta es `32 - 33 = -1`. El signo negativo indica que la última sesión tardó un minuto más; no hubo mejora en este indicador.
</details>

### Comprueba {data-pedagogy="comprueba"}

<label>
  <input type="checkbox" data-progress-id="00_inicio:primer_experimento">
  Puedo cambiar un dato, predecir el signo y explicar el resultado.
</label>

## Ruta completa {#ruta}

El índice lateral muestra el recorrido entero. Los módulos sin enlace aún no están construidos. Empieza por **01. Datos, formas y señales** cuando aparezca disponible.
