# citashospital/core/views.py
from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection


@api_view(['GET'])
def listar_doctores(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT d.id, u.nombre_completo, e.nombre as especialidad
            FROM doctor d
            JOIN usuario u ON d.usuario_id = u.id
            JOIN especialidad e ON d.especialidad_id = e.id
        """)
        rows = cursor.fetchall()
    doctores = [{'id': r[0], 'nombre': r[1], 'especialidad': r[2]} for r in rows]
    return Response(doctores)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def usuarios_crud(request):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, rol, nombre_completo FROM usuario")
            rows = cursor.fetchall()
        return Response([{'id': r[0], 'username': r[1], 'rol': r[2], 'nombre': r[3]} for r in rows])

    if request.method == 'POST':
        data = request.data
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO usuario (username, password, rol, nombre_completo, telefono, direccion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [data['username'], data['password'], data['rol'], data['nombre_completo'], data['telefono'], data['direccion']])
        return Response({'mensaje': 'Usuario creado'})


@api_view(['GET', 'POST'])
def doctores_crud(request):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT d.id, u.nombre_completo, e.nombre
                FROM doctor d
                JOIN usuario u ON d.usuario_id = u.id
                JOIN especialidad e ON d.especialidad_id = e.id
            """)
            rows = cursor.fetchall()
        return Response([{'id': r[0], 'nombre': r[1], 'especialidad': r[2]} for r in rows])

    if request.method == 'POST':
        data = request.data
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO doctor (usuario_id, cedula_profesional, especialidad_id)
                VALUES (%s, %s, %s)
            """, [data['usuario_id'], data['cedula_profesional'], data['especialidad_id']])
        return Response({'mensaje': 'Doctor creado'})


@api_view(['GET', 'POST'])
def pacientes_crud(request):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.id, u.nombre_completo, p.curp, p.fecha_nacimiento
                FROM paciente p JOIN usuario u ON p.usuario_id = u.id
            """)
            rows = cursor.fetchall()
        return Response([{'id': r[0], 'nombre': r[1], 'curp': r[2], 'fecha_nac': str(r[3])} for r in rows])

    if request.method == 'POST':
        data = request.data
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO paciente (usuario_id, fecha_nacimiento, sexo, curp)
                VALUES (%s, %s, %s, %s)
            """, [data['usuario_id'], data['fecha_nacimiento'], data['sexo'], data['curp']])
        return Response({'mensaje': 'Paciente creado'})


@api_view(['GET', 'POST'])
def secretarias_crud(request):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.id, u.nombre_completo
                FROM secretaria s JOIN usuario u ON s.usuario_id = u.id
            """)
            rows = cursor.fetchall()
        return Response([{'id': r[0], 'nombre': r[1]} for r in rows])

    if request.method == 'POST':
        data = request.data
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO secretaria (usuario_id) VALUES (%s)
            """, [data['usuario_id']])
        return Response({'mensaje': 'Secretaria creada'})


@api_view(['GET', 'POST'])
def citas_crud(request):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, u.nombre_completo, d.id, c.fecha_cita, c.estado
                FROM cita c
                JOIN paciente p ON c.paciente_id = p.id
                JOIN usuario u ON p.usuario_id = u.id
                JOIN doctor d ON c.doctor_id = d.id
            """)
            rows = cursor.fetchall()
        return Response([{'id': r[0], 'paciente': r[1], 'doctor_id': r[2], 'fecha': str(r[3]), 'estado': r[4]} for r in rows])

    if request.method == 'POST':
        data = request.data
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO cita (paciente_id, doctor_id, fecha_cita, hora_inicio, hora_fin, motivo, estado, creada_por)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [data['paciente_id'], data['doctor_id'], data['fecha_cita'], data['hora_inicio'], data['hora_fin'], data['motivo'], data['estado'], data['creada_por']])
        return Response({'mensaje': 'Cita creada'})


@api_view(['GET'])
def listar_pacientes(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.id, u.nombre_completo, p.curp, p.fecha_nacimiento
            FROM paciente p JOIN usuario u ON p.usuario_id = u.id
        """)
        rows = cursor.fetchall()
    pacientes = [{'id': r[0], 'nombre': r[1], 'curp': r[2], 'fecha_nac': str(r[3])} for r in rows]
    return Response(pacientes)
