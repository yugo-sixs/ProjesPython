# Sistema de control de asistencia

Proyecto inicial para una app movil de asistencia con:

- Django + Django REST Framework
- MySQL
- JWT
- Panel web administrativo de Django
- Flutter como cliente movil

## Estructura

```text
backend/   API REST, reglas de negocio y panel RH
mobile/    Cliente Flutter inicial
docs/      SQL y documentacion tecnica
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

3. Levantar MySQL con Docker:

```bash
docker compose up -d mysql
```

4. Crear migraciones y tablas:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5. Ejecutar servidor:

```bash
python manage.py runserver 0.0.0.0:8000
```

6. Generar faltas de un dia sin registro:

```bash
python manage.py generate_absences --date 2026-07-09
```

## Endpoints principales

Autenticacion:

```text
POST /api/auth/login/
POST /api/auth/refresh/
```

App movil:

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

## Payload movil para entrada/salida

Debe enviarse como `multipart/form-data` para incluir fotografias:

```text
device_datetime=2026-07-09T08:05:00-06:00
latitude=19.432608
longitude=-99.133209
gps_accuracy=8.5
employee_photo=<archivo>
environment_photo=<archivo>
device_id=<identificador del telefono>
```

## Reglas implementadas

- Puntual: entrada a la hora programada o antes.
- Tolerancia: entrada dentro de los minutos de tolerancia configurados.
- Retardo: entrada despues de la tolerancia.
- Descanso: si el dia del horario esta marcado como descanso.
- Horas trabajadas: diferencia entre entrada y salida.
- Horas extra: horas trabajadas menos jornada normal configurada.

## Nota

El entorno actual no tiene Django ni Flutter instalados en el PATH del sistema. Los archivos quedan listos para instalar dependencias y ejecutar en una maquina con Python, MySQL y Flutter configurados.
