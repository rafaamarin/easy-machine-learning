# Seguridad

## Versiones soportadas

La serie mantenida actualmente es `0.1.x`.

## Comunicar una vulnerabilidad

Nunca abras una incidencia pública que contenga una credencial, token, clave,
secreto o dato sensible.

Usa el informe privado de vulnerabilidades de GitHub cuando esté habilitado.
Si no lo está, contacta con el propietario a través del repositorio privado,
sin publicar los detalles. Incluye una reproducción mínima, el impacto y las
versiones afectadas.

Si una credencial ha quedado expuesta, revócala y rótala antes de intentar la
remediación. Borrar el valor del historial no invalida la credencial.

## Verificación local

Ejecuta desde la raíz:

```bash
./verificar_seguridad.sh
```

El comando busca secretos y rutas personales y audita las dependencias fijadas.
