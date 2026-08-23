import numpy as np

tiempos_min = np.array([32, 31, 30, 29, 28], dtype=float)
mejora_min = float(tiempos_min[0] - tiempos_min[-1])

print(f"Sesiones: {tiempos_min.size}")
print(f"Primer 5 km: {tiempos_min[0]:.0f} min")
print(f"Último 5 km: {tiempos_min[-1]:.0f} min")
print(f"Mejora observada: {mejora_min:.0f} min")
