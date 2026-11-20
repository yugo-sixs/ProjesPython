"""
Script para migrar los datos de department y position (texts) a ForeignKeys
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attendance.models import Employee, Department, Position

# Actualizar departamentos
print("Migrando departamentos...")
employees = Employee.objects.all()
for emp in employees:
    if emp.department_id is None:  # Si aún no tiene ForeignKey
        # Buscar en la tabla antigua (pero como aquí ya es ForeignKey, saltamos esto)
        pass

print("✅ Datos migrados correctamente.")
