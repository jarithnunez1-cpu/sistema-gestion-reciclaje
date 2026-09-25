# VerdeCiclo · Sistema Digital de Gestión de Reciclaje

Aplicación web local para administrar recicladores, empresas, materiales, recolecciones, indicadores y consultas de informes mensuales. La autenticación usa un único formulario para los dos roles definidos: `ADMINISTRADOR` y `RECICLADOR`.

## Requisitos

- Python 3.10 o posterior.
- No necesita paquetes de terceros ni un servidor de base de datos aparte.

## Puesta en marcha en Windows / PowerShell

Desde la carpeta del proyecto:

```powershell
python .\app.py init-db
python .\app.py create-admin --nombre "Administración" --correo admin@ejemplo.com --contrasena "Reemplaza-Esta-Clave-2026!"
python .\app.py serve
```

Abre `http://127.0.0.1:8000`. Cambia la contraseña de ejemplo por una propia de al menos 12 caracteres. `create-admin` no imprime ni guarda la contraseña en el proyecto. La base de datos se crea en `data/reciclaje.sqlite3`; define `RECICLAJE_DB` antes de iniciar para guardarla en otra ubicación.

## Desarrollo y pruebas

```powershell
python -m unittest discover -s tests -v
```

Los tests ejecutan solicitudes HTTP contra una base de datos temporal y no alteran la base de datos de trabajo.

## Funciones incluidas

- Sesión única mediante cookie `HttpOnly`, `SameSite=Strict`, token aleatorio almacenado como hash y expiración de 12 horas.
- Hash de contraseña PBKDF2-HMAC-SHA256 con sal aleatoria.
- Autorización de cada endpoint en el backend.
- Alta, consulta, edición y eliminación segura de recicladores; se impide eliminar recicladores con recolecciones.
- Gestión de empresas y materiales; restricciones de clave foránea conservan el historial.
- Registro de recolección ligado en servidor al reciclador autenticado, sin aceptar el identificador de reciclador del formulario.
- Resumen mensual del reciclador; indicadores y filtros para administración; informe mensual por empresa calculado desde recolecciones.
- Validación de correo único, porcentajes meta, fechas requeridas, cantidad positiva y relaciones existentes.

## Rutas principales

- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- `/api/recolectores`, `/api/empresas`, `/api/materiales`
- `GET|POST /api/recolecciones`
- `GET /api/indicadores`, `GET /api/resumen`
- `GET /api/reportes/empresas?empresa=ID&year=AAAA&month=MM`

El informe mensual se consulta dentro del panel administrativo. La descarga y el acceso directo de empresas quedan pendientes hasta que se definan formato y autenticación empresarial.

## Límite de despliegue

El servidor estándar de Python está pensado para desarrollo y redes privadas de confianza, no para exposición directa a Internet. Para producción se debe alojar detrás de HTTPS en un servidor de aplicación con endurecimiento operativo, copias de seguridad, restauración y rotación de secretos. La lógica funcional y la persistencia no dependen de un servicio externo.
