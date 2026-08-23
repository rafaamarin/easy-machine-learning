# 01. Datos, formas y señales

Vas a construir un miniinspector. Antes, necesitas ver un dataset como una máquina lo ve: números organizados por ejes.

**Entrega:** una función que informa forma, centro, dispersión y rango.

<progress class="progress-meter" data-progress-meter aria-label="Progreso del módulo" value="0" max="8"></progress>
<output data-progress-text>0 de 8</output>

## Reto 1: localiza una fila y una columna {#forma data-pedagogy="reto"}

Tenemos cinco entrenamientos y tres medidas numéricas. Predice `shape`, `ndim` y `size` antes de ejecutar.

<py-lab data-lab-id="01_formas" data-src="contenido_fuente/01_datos_y_formas/labs/01_formas.py" data-packages="numpy" data-title="Haz visible la forma"></py-lab>

<details markdown="1" data-static-output-for="01_formas"><summary>Salida de referencia si Python no carga</summary>

`shape: (5, 3)`, `ndim: 2`, `size: 15`.
</details>

### Observa {data-pedagogy="observa"}

`shape=(5, 3)` significa cinco muestras por tres features. `size=15` cuenta escalares. `[:, 1]` conserva todas las filas y extrae la segunda feature.

### Modifica {data-pedagogy="modifica"}

Añade `[7, 39, 151]`. Predice qué valores cambian. Después elimina `fc_media` y repite.

<details markdown="1" data-solution>
<summary>Solución</summary>

Con una fila nueva: `shape=(6, 3)`, `ndim=2`, `size=18`. Sin la tercera columna: `shape=(6, 2)` y `size=12`; `ndim` sigue siendo 2.
</details>

<label><input type="checkbox" data-progress-id="01_datos_y_formas:forma"> Puedo traducir filas, columnas, `shape`, `ndim` y `size`.</label>

## Reto 2: resume sin esconder diferencias {#centro_dispersion data-pedagogy="matematica"}

La media responde «¿dónde está el centro?». La desviación responde «¿cuánto se separan los valores del centro?».

Con `[29, 45, 55, 34, 64]`:

1. suma y divide entre cinco;
2. resta la media a cada valor;
3. eleva esas diferencias al cuadrado;
4. promedia y calcula la raíz.

<py-lab data-lab-id="02_centro_dispersion" data-src="contenido_fuente/01_datos_y_formas/labs/02_centro_dispersion.py" data-packages="numpy,matplotlib" data-title="Mueve el centro y la dispersión"></py-lab>

<details markdown="1" data-static-output-for="02_centro_dispersion"><summary>Salida de referencia si Python no carga</summary>

Media `45.40 min`; desviación `12.94 min`. Al sustituir `64` por `120`, ambas aumentan.
</details>

### Desde cero {data-pedagogy="desde_cero"}

Las funciones usan `sum`, `len` y potencias. Cambia `120` por `64`. Comprueba que los resultados manuales coinciden con `np.mean(duraciones)` y `np.std(duraciones)`.

### Rompe y depura {#depura data-pedagogy="depura"}

Cambia todas las duraciones por `40`. La desviación debe ser 0. Si luego divides por ella para escalar, aparecerán valores inválidos. Antes de dividir, comprueba `desviacion == 0`.

<details markdown="1" data-hint><summary>Pista</summary>

Una feature constante no contiene diferencias entre muestras.
</details>

<details markdown="1" data-solution><summary>Protección mínima</summary>

```python
if desviacion == 0:
    raise ValueError("No se puede estandarizar una feature constante")
```
</details>

<label><input type="checkbox" data-progress-id="01_datos_y_formas:dispersion"> Puedo calcular y explicar media y desviación con números pequeños.</label>

## Reto 3: evita que una unidad grite más fuerte {#escala data-pedagogy="reto"}

En una fila, `148` parece dominar a `5`. No significa que la frecuencia cardiaca sea más importante: usa otra unidad.

La estandarización aplica `z = (x - media) / desviación`. El resultado indica cuántas desviaciones separan un valor de su media.

<py-lab data-lab-id="03_escala" data-src="contenido_fuente/01_datos_y_formas/labs/03_escala.py" data-packages="numpy,matplotlib" data-title="Pon las features en una escala comparable"></py-lab>

<details markdown="1" data-static-output-for="03_escala"><summary>Salida de referencia si Python no carga</summary>

Las tres medias transformadas son `0`; las tres desviaciones transformadas son `1` salvo redondeo numérico.
</details>

### Con herramienta {data-pedagogy="con_herramienta"}

NumPy opera por columnas con `axis=0`. Comprueba que cada columna transformada tiene media cercana a 0 y desviación cercana a 1.

### Modifica {data-pedagogy="modifica"}

Cambia todos los valores de `fc_media` sumando 20. Predice qué ocurre con sus z-scores. Después multiplícalos por 2 y vuelve a comprobar.

<details markdown="1" data-solution><summary>Interpretación</summary>

Los z-scores no cambian: trasladar o multiplicar toda una feature cambia su media y desviación en la misma proporción. La posición relativa de cada muestra se conserva.
</details>

<label><input type="checkbox" data-progress-id="01_datos_y_formas:escala"> Puedo estandarizar por columnas y verificar media 0, desviación 1.</label>

## Construye: miniinspector {#miniinspector data-pedagogy="con_herramienta"}

Ahora empaqueta la inspección en una función. La columna `tipo` no entra en cálculos numéricos, pero sigue siendo parte del dataset.

<py-lab data-lab-id="04_miniinspector" data-src="contenido_fuente/01_datos_y_formas/labs/04_miniinspector.py" data-packages="pandas" data-title="Construye el miniinspector"></py-lab>

<details markdown="1" data-static-output-for="04_miniinspector"><summary>Salida de referencia si Python no carga</summary>

El DataFrame tiene `shape=(5, 4)`, cero nulos y tres filas numéricas en el resumen.
</details>

### Comprueba {data-pedagogy="comprueba"}

Añade una columna numérica `desnivel_m=[20, 40, 80, 25, 160]`. El resumen debe crear una fila nueva sin cambiar la función.

<details markdown="1" data-solution><summary>Solución</summary>

```python
entrenamientos_df["desnivel_m"] = [20, 40, 80, 25, 160]
resumen = inspeccionar(entrenamientos_df)
print(resumen.round(2))
```

La función selecciona columnas numéricas en cada llamada. Por eso no necesita conocer el nombre nuevo.
</details>

<label><input type="checkbox" data-progress-id="01_datos_y_formas:miniinspector"> Puedo construir un resumen reutilizable sin hardcodear columnas.</label>

## Checklist de salida {#checklist}

Marca solo lo que puedas hacer sin mirar la solución.

- <label><input type="checkbox" data-progress-id="01_datos_y_formas:salida_forma"> Identificar muestra, feature y eje en un array.</label>
- <label><input type="checkbox" data-progress-id="01_datos_y_formas:salida_estadistica"> Explicar qué cambia cuando aparece un dato extremo.</label>
- <label><input type="checkbox" data-progress-id="01_datos_y_formas:salida_escala"> Estandarizar y verificar el resultado.</label>
- <label><input type="checkbox" data-progress-id="01_datos_y_formas:salida_codigo"> Modificar el miniinspector para un DataFrame nuevo.</label>

Cuando las cuatro estén marcadas, continúa hacia **02. Una recta que aprende**.
