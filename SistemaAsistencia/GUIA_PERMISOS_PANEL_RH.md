# Guía de permisos del panel administrativo

Esta guía explica cómo crear usuarios, grupos y permisos para el sistema de asistencia.

## 1. Entrar al administrador de Django

Inicia el backend:

```powershell
cd C:\wamp64\www\ProjesPython\SistemaAsistencia\backend
python manage.py runserver
```

Abre:

```text
http://127.0.0.1:8000/admin/
```

Debes entrar con un usuario administrador que tenga:

- `is_staff`: permite entrar al panel de administración.
- `is_superuser`: permite administrar todo sin restricciones.

Para crear el primer administrador:

```powershell
python manage.py createsuperuser
```

## 2. Crear un grupo para RH

1. En el admin, entra a **Grupos**.
2. Selecciona **Agregar grupo**.
3. Escribe, por ejemplo, `Recursos Humanos`.
4. En permisos, selecciona los permisos necesarios.
5. Guarda el grupo.

Los permisos de los modelos de asistencia normalmente aparecen como:

- `attendance | employee`
- `attendance | employee schedule`
- `attendance | work schedule`
- `attendance | work schedule day`
- `attendance | attendance`
- `attendance | attendance record`
- `attendance | justification`

Cada modelo puede tener estos permisos:

- `add`: agregar registros.
- `change`: modificar registros.
- `delete`: eliminar registros.
- `view`: consultar registros.

## 3. Crear un usuario de RH

1. Entra a **Usuarios**.
2. Selecciona **Agregar usuario**.
3. Define nombre de usuario y contraseña.
4. Guarda el usuario.
5. Activa **Estado de personal (`is_staff`)**.
6. En **Grupos**, agrega `Recursos Humanos`.
7. Guarda los cambios.

No actives **Superusuario** para un usuario normal de RH. El superusuario tiene acceso completo a todo el sistema.

## 4. Diferencia entre usuario empleado, RH y administrador

### Empleado

- No debe tener `is_staff`.
- Debe estar relacionado con un registro de `Employee`.
- Su empleado debe tener estado `ACTIVO`.
- Su tipo debe ser `WORKER`.
- Puede utilizar la aplicación móvil de asistencia.

### Usuario de RH

- Debe tener `is_staff` activado.
- Normalmente debe tener un registro `Employee` con tipo `RH`.
- Puede entrar al panel de RH.
- Puede administrar empleados, horarios y consultar reportes según la lógica actual del proyecto.

### Administrador

- Tiene `is_staff` e `is_superuser` activados.
- Puede entrar a `/admin/`.
- Puede administrar usuarios, grupos, permisos y todos los modelos.
- También puede entrar al panel especial de administrador del sistema.

## 5. Asignar un horario a un empleado

La asignación se realiza desde el panel de RH:

```text
http://127.0.0.1:8000/rh/empleados/
```

1. Crea o edita un empleado.
2. Selecciona un horario.
3. Indica la fecha de inicio.
4. Guarda el empleado.

La relación se guarda en `EmployeeSchedule`. El sistema usa esa asignación para determinar el horario vigente, la hora de entrada, la tolerancia y el descanso de comida.

También es posible revisar las asignaciones directamente desde:

```text
http://127.0.0.1:8000/admin/attendance/employeeschedule/
```

## 6. Configurar la comida y las horas trabajadas

Los horarios se administran desde:

```text
http://127.0.0.1:8000/rh/horarios/
```

Para cada día se puede indicar:

- Hora de entrada.
- Hora de salida.
- Minutos de tolerancia.
- Horas regulares de la jornada.
- Minutos de comida.
- Si es día de descanso.

Ejemplo:

```text
Entrada: 08:00
Salida: 17:00
Jornada: 8 horas
Comida: 60 minutos
```

El sistema calcula:

```text
17:00 - 08:00 = 9 horas transcurridas
9 horas - 1 hora de comida = 8 horas trabajadas
```

La comida no se descuenta diariamente de forma manual. Se aplica automáticamente cuando se cierra la asistencia con la salida.

## 7. Importante sobre los permisos de las vistas actuales

Los permisos de modelos del admin controlan qué puede hacer un usuario dentro de `/admin/`. Sin embargo, las vistas web actuales del panel RH tienen estas reglas:

- El dashboard requiere `is_staff`.
- Empleados requiere `is_staff`.
- Horarios requiere `is_staff`.
- Reportes requiere `is_staff`.
- El panel especial de administrador requiere `is_superuser`.
- La vista de asistencia personal está reservada para usuarios que no sean `staff`.

Por esta razón, actualmente no se puede permitir desde el admin que un usuario de RH vea únicamente Empleados pero no Horarios. Aunque se le quite el permiso `change_workscheduleday`, la vista web seguirá comprobando principalmente `is_staff`.

Los permisos individuales sí son útiles para restringir operaciones dentro del admin de Django. Para permisos separados por cada vista del panel RH habría que modificar el código para comprobar permisos como:

```python
request.user.has_perm("attendance.view_employee")
request.user.has_perm("attendance.change_employee")
request.user.has_perm("attendance.view_workschedule")
```

## 8. Recomendación de configuración

Para una instalación normal:

| Tipo | `is_staff` | `is_superuser` | Grupo |
|---|---:|---:|---|
| Empleado | No | No | Ninguno |
| RH | Sí | No | Recursos Humanos |
| Administrador | Sí | Sí | Opcional |

Usa el superusuario únicamente para configurar el sistema. Para el trabajo cotidiano, utiliza usuarios de RH con `is_staff` y un grupo específico.

## 9. Comprobar el acceso

Después de crear un usuario, prueba:

```text
Panel RH: http://127.0.0.1:8000/rh/dashboard/
Empleados: http://127.0.0.1:8000/rh/empleados/
Horarios: http://127.0.0.1:8000/rh/horarios/
Reportes: http://127.0.0.1:8000/rh/reportes/asistencias/
Admin Django: http://127.0.0.1:8000/admin/
```

Si aparece `403 Forbidden`, revisa que el usuario tenga `is_staff` cuando intenta acceder al panel RH, o `is_superuser` cuando intenta acceder al panel especial de administrador.
