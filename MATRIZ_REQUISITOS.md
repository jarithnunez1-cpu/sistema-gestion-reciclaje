# Matriz de requisitos

| Requisito | Estado | Ubicación | Observaciones |
|---|---|---|---|
| Login único correo/contraseña | Implementado | `app.py`, `static/index.html`, `static/app.js` | Un endpoint y formulario compartidos. |
| Roles actuales Administrador y Reciclador | Implementado | `schema.sql`, `app.py` | CHECK de rol y autorización de endpoints. |
| Hash seguro de contraseñas | Implementado | `app.py` | PBKDF2-HMAC-SHA256 con sal aleatoria. |
| Sesiones seguras | Implementado | `schema.sql`, `app.py` | Token aleatorio, hash en BD, cookie HttpOnly/SameSite y expiración. |
| Relación Usuario–Administrador/Reciclador | Parcial | `schema.sql`, `app.py` | Claves únicas y alta coherente desde CLI/API; no hay trigger SQL que verifique el rol al insertar perfil directamente desde fuera de la aplicación. |
| Administrador crea/edita/consulta recicladores | Implementado | `app.py`, `static/app.js` | Asociados al administrador que crea la cuenta. |
| Bloquear eliminación de reciclador con historial | Implementado | `app.py`, `schema.sql` | Verificación explícita y FK restrictiva. |
| Gestión de empresas afiliadas | Implementado | `app.py`, `static/app.js` | Crear, listar, editar y eliminar sin historial asociado. |
| Gestión de materiales y validación de meta | Implementado | `app.py`, `schema.sql`, `static/app.js` | El uso de la meta sigue pendiente. |
| Registro de recolección por reciclador | Implementado | `app.py`, `static/app.js` | Identidad ligada a sesión del backend. |
| Fecha requerida, cantidad > 0 y relaciones existentes | Implementado | `app.py`, `schema.sql` | Validado en frontend, backend y restricciones de BD. |
| Consulta administrativa de recolecciones | Implementado | `app.py`, `static/app.js` | El alcance entre varios administradores requiere definición adicional. |
| Resumen mensual del reciclador | Implementado | `app.py`, `static/app.js` | Derivado de recolecciones; ganancia pendiente. |
| Total kg e información mensual | Implementado | `/api/indicadores`, `/api/resumen`, `static/app.js` | Cálculo dinámico; filtros de año, mes, empresa, reciclador y material en administración. |
| Ingresos generados | Pendiente | `PENDIENTES.md` | No hay fórmula en la especificación. |
| Recicladores activos | Parcial | `/api/indicadores`, dashboard | Se muestra el conteo de registrados; criterio de actividad pendiente. |
| Participación de materiales | Implementado | `/api/indicadores`, dashboard | Se calcula desde kilogramos registrados. |
| Informe mensual por empresa | Implementado | `/api/reportes/empresas`, panel Informes | Total calculado exclusivamente desde `RECOLECCION`. |
| Acceso directo empresarial y descarga | Pendiente | `PENDIENTES.md` | Rol empresarial/formato no definidos. |
| Recuperar/cambiar contraseña | Pendiente | `PENDIENTES.md` | Identificado, sin flujo supuesto. |
| Auditoría de modificaciones | Pendiente | `PENDIENTES.md` | Identificado, sin alcance definido. |
| Pruebas de aceptación | Implementado | `tests/test_system.py` | Inicio por roles, permisos, validaciones, asociación automática, historial e informes/indicadores dinámicos. |
| Guía de instalación | Implementado | `README.md` | Python estándar, SQLite local y comandos PowerShell. |
