# Puesta en marcha

La base queda configurada para MySQL con `utf8mb4`. Define `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT` como variables de entorno antes de iniciar Django. Para producción define también `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` y `DJANGO_ALLOWED_HOSTS`.

1. Instala `requirements.txt` en el entorno virtual.
2. Crea en MySQL una base de datos con cotejamiento `utf8mb4_unicode_ci`.
3. Ejecuta `python manage.py migrate` y `python manage.py createsuperuser`.
4. En el administrador crea materiales, socios, empleados y asigna roles. Los permisos adicionales se asignan en grupos de Django.
5. Inicia el servidor con `python manage.py runserver` para uso local.

La migración inicial introduce un usuario personalizado. En una base existente que ya haya aplicado migraciones con el usuario nativo de Django no se debe aplicar directamente: primero hay que preparar una migración de datos y respaldar la base.

## Respaldos

El script `scripts/backup_mysql.ps1` genera un dump fechado en `backups/`. Requiere `mysqldump` en el `PATH` y las variables `DB_NAME`, `DB_USER`, `DB_PASSWORD` (también acepta `DB_HOST` y `DB_PORT`). Para respaldos diarios, programa este script desde el Programador de tareas de Windows con la cuenta que tenga acceso al servidor y configura una política de retención para la carpeta `backups`.

## Operación

- El usuario comprador registra compras con peso en kg, tara y porcentaje de merma. La compra suma al inventario el neto después de merma.
- Ventas aceptan captura en kg o toneladas; el detalle conserva la unidad capturada y convierte el neto a kg para el inventario.
- Las operaciones quedan protegidas contra borrado desde el administrador. Supervisores y administradores pueden cancelar por la ruta de la operación, indicando motivo; el servicio registra el reverso en el kardex.
- El precio por kg se conserva en cada detalle. Si cambia el precio vigente desde el administrador, se registra en el historial de precios.
- El corte presenta egresos de compra e ingresos de venta del día. La diferencia es un balance diario de caja, no un cálculo contable de costo de ventas.
