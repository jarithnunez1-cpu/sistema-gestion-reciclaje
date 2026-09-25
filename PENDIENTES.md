# Pendientes de definición funcional

No se han asignado reglas de negocio a los siguientes puntos. El sistema los señala como pendientes y no inventa valores.

| Tema | Comportamiento actual | Decisión pendiente |
|---|---|---|
| Ganancia del reciclador | Se presenta como pendiente; no se calcula importe. | Fórmula, período y datos de entrada. |
| Ingresos generados | Indicador mostrado como pendiente; `ingresos` es `null` en la API. | Fórmula y fuente de precios/valores. |
| `porcentaje_meta` | Se almacena y valida entre 0 y 100. | Significado, base del porcentaje y aplicación en reportes. |
| Recicladores activos | Se informa el número de recicladores registrados. | Criterio de “activo”. |
| Alcance administrador | Cada cuenta nueva se asocia al administrador que la creó; falta precisar permisos por administrador en todos los datos existentes. | Si el administrador ve solo sus recicladores y recolecciones o todo el sistema; permisos de edición y eliminación. |
| Acceso empresarial | El informe es consultable por administradores; no hay rol de empresa. | Si las empresas tendrán login al sistema y cómo se validará su identidad. |
| Descarga de informes | Informe consultable en la aplicación. | Formato (PDF, Excel u otro), diseño y filtros de descarga. |
| Contraseña | Se crea mediante administrador/CLI y se almacena con hash. | Recuperación, cambio y caducidad de contraseña. |
| Auditoría | No se conserva historial de modificaciones. | Si se requiere, eventos a registrar y retención. |

La indicación del PDF de que “las empresas podrán consultar y descargar” requiere resolver su tensión con los roles actualmente definidos (solo Administrador y Reciclador). Hasta entonces, el sistema no concede cuentas empresariales ni descarga con formato supuesto.
