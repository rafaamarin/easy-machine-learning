import numpy as np

columnas = ("distancia_km", "duracion_min", "fc_media")
entrenamientos = np.array(
    [
        [5, 29, 148],
        [8, 45, 152],
        [10, 55, 156],
        [6, 34, 149],
        [12, 64, 160],
    ],
    dtype=float,
)

print(f"shape: {entrenamientos.shape}")
print(f"ndim: {entrenamientos.ndim}")
print(f"size: {entrenamientos.size}")
print(f"Primera fila: {dict(zip(columnas, entrenamientos[0], strict=True))}")
print(f"Columna duración: {entrenamientos[:, 1]}")
