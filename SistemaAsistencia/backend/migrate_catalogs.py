"""
Script para migrar departamentos y puestos existentes en tabla empleados
a los nuevos modelos de catálogos.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attendance.models import Employee, Department, Position

# Obtener todos los departamentos únicos
departments = Employee.objects.exclude(department='').values_list('department', flat=True).distinct()

print(f"Migrando {len(departments)} departamentos...")
for dept_name in departments:
    dept, created = Department.objects.get_or_create(
        name=dept_name,
        defaults={'active': True}
    )
    status = "✓ Creado" if created else "- Existente"
    print(f"  {status}: {dept_name}")

# Obtener todos los puestos únicos
positions = Employee.objects.exclude(position='').values_list('position', flat=True).distinct()

print(f"\nMigrando {len(positions)} puestos...")
for pos_name in positions:
    pos, created = Position.objects.get_or_create(
        name=pos_name,
        defaults={'active': True}
    )
    status = "✓ Creado" if created else "- Existente"
    print(f"  {status}: {pos_name}")

print("\n✅ Migración completada.")
print(f"   Departamentos: {Department.objects.count()}")
print(f"   Puestos: {Position.objects.count()}")
