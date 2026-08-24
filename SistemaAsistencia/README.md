# Sistema de control de asistencia

Proyecto para una app móvil de asistencia con:

- Django + Django REST Framework
- MySQL
- JWT para la app móvil
- Panel web RH con autenticación de Django
- Flutter como cliente móvil

## Estructura

```text
backend/   API REST, reglas de negocio y panel RH
mobile/    Cliente Flutter inicial
docs/      SQL y documentación técnica
```

## Backend

1. Crear entorno virtual e instalar dependencias:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Configurar variables:

```bash
copy .env.example .env
```

3. Levantar MySQL con Docker o WAMP. Si usas WAMP, revisa que `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD` y `MYSQL_DATABASE` coincidan con tu instalación.

4. Crear tablas y usuario administrador:

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Ejecutar servidor:

```bash
python manage.py runserver 0.0.0.0:8000
```

Para correr pruebas sin permisos de crear bases temporales en MySQL:

```bash
set DJANGO_TEST_SQLITE=1
python manage.py test attendance
```

6. Entrar al panel:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/rh/login/
http://127.0.0.1:8000/admin/
```

7. Generar faltas de un día sin registro:

```bash
python manage.py generate_absences --date 2026-07-09
```

## Credenciales demo

Para crear los usuarios demo en desarrollo local:

```bash
python manage.py create_demo_users
```

| Perfil | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin` | `admin123456` |
| RH | `rh` | `rh123456` |

Estas credenciales son solo para desarrollo local. Cámbialas antes de usar el sistema en producción.

## Endpoints principales

Autenticación:

```text
POST /api/auth/login/
POST /api/auth/refresh/
```

App móvil:

```text
GET  /api/mobile/me/
POST /api/mobile/asistencia/entrada/
POST /api/mobile/asistencia/salida/
GET  /api/mobile/asistencias/
```

Recursos Humanos:

```text
GET/POST      /api/rh/empleados/
GET/PUT/DEL   /api/rh/empleados/{id}/
GET/POST      /api/rh/horarios/
GET/PUT/DEL   /api/rh/horarios/{id}/
GET           /api/rh/asistencias/
POST          /api/rh/asistencias/{id}/justify/
GET           /api/rh/reportes/resumen/
```

## Payload móvil para entrada/salida

Debe enviarse como `multipart/form-data`:

```text
device_datetime=2026-07-09T08:05:00-06:00
latitude=19.432608
longitude=-99.133209
gps_accuracy=8.5
employee_photo=<archivo>
environment_photo=<archivo>
device_id=<identificador del teléfono>
```

## Notas de integridad

- El `.venv`, `.env`, `__pycache__`, `*.pyc`, `media/` y builds de Flutter no deben versionarse.
- El comando `create_demo_users` es solo para desarrollo local porque crea contraseñas conocidas.
- Para completar Flutter si `android/` e `ios/` están vacíos, instala Flutter y ejecuta dentro de `mobile/`: `flutter create .`
