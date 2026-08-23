import pandas as pd


def inspeccionar(datos: pd.DataFrame) -> pd.DataFrame:
    numericos = datos.select_dtypes(include="number")
    return pd.DataFrame(
        {
            "media": numericos.mean(),
            "desviacion": numericos.std(ddof=0),
            "minimo": numericos.min(),
            "maximo": numericos.max(),
        }
    )


entrenamientos_df = pd.DataFrame(
    {
        "distancia_km": [5, 8, 10, 6, 12],
        "duracion_min": [29, 45, 55, 34, 64],
        "fc_media": [148, 152, 156, 149, 160],
        "tipo": ["suave", "tempo", "tempo", "suave", "largo"],
    }
)
resumen = inspeccionar(entrenamientos_df)

print(entrenamientos_df)
print("\nResumen numérico:")
print(resumen.round(2))
null_count = int(entrenamientos_df.isna().sum().sum())
print(f"\nshape={entrenamientos_df.shape}; nulos={null_count}")
