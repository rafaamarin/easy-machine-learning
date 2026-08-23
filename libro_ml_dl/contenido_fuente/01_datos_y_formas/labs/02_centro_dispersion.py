import matplotlib.pyplot as plt
import numpy as np

duraciones = np.array([29, 45, 55, 34, 64], dtype=float)


def calcular_media(valores: np.ndarray) -> float:
    return float(sum(valores) / len(valores))


def calcular_desviacion(valores: np.ndarray) -> float:
    media = calcular_media(valores)
    varianza = sum((valor - media) ** 2 for valor in valores) / len(valores)
    return float(varianza**0.5)


media_manual = calcular_media(duraciones)
desviacion_manual = calcular_desviacion(duraciones)
duraciones_con_error = duraciones.copy()
duraciones_con_error[-1] = 120
media_con_error = calcular_media(duraciones_con_error)
desviacion_con_error = calcular_desviacion(duraciones_con_error)

print(f"Media: {media_manual:.2f} min")
print(f"Desviación: {desviacion_manual:.2f} min")
print(
    f"Con dato extremo: media={media_con_error:.2f}, "
    f"desviación={desviacion_con_error:.2f}"
)

sesiones = np.arange(1, len(duraciones) + 1)
ancho = 0.36
paleta = {"original": "#1f5a99", "con_error": "#d97706", "contorno": "#5b2c06"}
fig, axis = plt.subplots(figsize=(7, 3.5))
axis.bar(
    sesiones - ancho / 2,
    duraciones,
    ancho,
    color=paleta["original"],
    label="original",
)
axis.bar(
    sesiones + ancho / 2,
    duraciones_con_error,
    ancho,
    color=paleta["con_error"],
    label="con dato extremo",
)
dato_modificado = axis.scatter(
    [sesiones[-1] + ancho / 2],
    [duraciones_con_error[-1]],
    color=paleta["con_error"],
    edgecolors=paleta["contorno"],
    linewidths=1.5,
    marker="D",
    s=64,
    label="dato modificado",
    zorder=3,
)
axis.set(
    xlabel="sesión",
    ylabel="duración (min)",
    title="¿Cómo altera un dato extremo el centro y la dispersión?",
    xticks=sesiones,
)
axis.set_ylim(bottom=0)
axis.legend()
fig.tight_layout()
if "agg" not in plt.get_backend().lower():
    plt.show()
