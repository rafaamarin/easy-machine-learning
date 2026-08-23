# Contribuir

El repositorio es privado. Necesitas acceso autenticado para clonarlo, crear
ramas y proponer cambios.

## Flujo local

Trabaja en una rama enfocada y, desde la raíz del repositorio, ejecuta antes de
abrir una revisión:

```bash
./instalar.sh --yes
./verificar.sh
./verificar_seguridad.sh
git diff --check
```

## Contrato de cambios

- Usa `snake_case` en variables, funciones y archivos Python, sigue PEP 8 y
  añade type hints cuando sean prácticos.
- Añade pruebas enfocadas que fallen por la regresión que pretenden evitar.
- Conserva los notebooks de `material_fuente/notebooks/` byte por byte. No
  limpies salidas, normalices metadatos ni vuelvas a serializar su JSON.
- No confirmes binarios generados de Pyodide. El runtime local bajo
  `libro_ml_dl/assets/vendor/pyodide/` se reconstruye durante la instalación.
- No presentes como disponibles los módulos del roadmap: TensorFlow, PyTorch,
  visión, transformers, ingeniería y proyectos siguen planificados.
- Mantén los cambios pequeños, auditables y sin rutas locales, credenciales ni
  dependencias globales implícitas.

Describe en la propuesta el objetivo, las pruebas ejecutadas, las limitaciones
y cualquier impacto sobre procedencia o reproducibilidad.
