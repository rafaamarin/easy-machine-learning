import matplotlib.pyplot as plt
import numpy as np

columnas = ("distancia_km", "duracion_min", "fc_media")
entrenamientos = np.array(
    [[5, 29, 148], [8, 45, 152], [10, 55, 156], [6, 34, 149], [12, 64, 160]],
    dtype=float,
)
medias = entrenamientos.mean(axis=0)
desviaciones = entrenamientos.std(axis=0)
datos_estandarizados = (entrenamientos - medias) / desviaciones

print(f"Medias originales: {medias.round(2)}")
print(f"Desviaciones originales: {desviaciones.round(2)}")
print(f"Medias tras z-score: {datos_estandarizados.mean(axis=0).round(6)}")
print(f"Desviaciones tras z-score: {datos_estandarizados.std(axis=0).round(6)}")

paleta = ["#1f5a99", "#c2410c", "#6b7a16"]
fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
axes[0].bar(columnas, entrenamientos[0], color=paleta)
axes[0].set(
    title="Unidades distintas (base cero)",
    xlabel="feature",
    ylabel="valor original",
)
axes[0].set_ylim(bottom=0)
axes[1].bar(columnas, datos_estandarizados[0], color=paleta)
axes[1].axhline(0, color="#1f2937", linewidth=1)
axes[1].set(title="z-score", xlabel="feature", ylabel="desviaciones de la media")
for axis in axes:
    axis.tick_params(axis="x", rotation=25)
fig.suptitle("¿Por qué escalar permite comparar features?")
fig.tight_layout()
if "agg" not in plt.get_backend().lower():
    plt.show()
