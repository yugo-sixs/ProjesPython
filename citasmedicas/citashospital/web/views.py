# citasmedicas/citashospital/web/views.py
from django.shortcuts import render, redirect
from django.db import connection
import requests
from django.db import connection


def home(request):
    return redirect('listar_usuarios')


def listar_usuarios(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username, rol FROM usuario")
        rows = cursor.fetchall()
        usuarios = [
            {
                'id': r[0],
                'username': r[1],
                'rol': r[2]

            }
            for r in rows
        ]
    return render(request, 'listar_usuarios.html', {'usuarios': usuarios})


def crear_usuario(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        password1 = request.POST['password1']
        rol = request.POST['rol']

        if password != password1:
            return render(request, 'crear_usuario.html', {
                'error': 'Las contraseñas no coinciden.'
            })
        else:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO usuario (username, password, rol)
                    VALUES (%s, %s, %s)
                """, [username, password, rol])

            return redirect('/')
    return render(request, 'crear_usuario.html')


def editar_usuario(request, usuario_id):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        rol = request.POST['rol']

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE usuario
                SET username=%s, password=%s, rol=%s WHERE id=%s
            """, [username, password, rol, usuario_id])

        return redirect('listar_usuarios')

    # GET para cargar datos actuales
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, password, rol, FROM usuario WHERE id=%s", [usuario_id])
        row = cursor.fetchone()
        usuario = None
        if row:
            usuario = {
                'id': row[0],
                'username': row[1],
                'password': row[2],
                'rol': row[3],
            }

    return render(request, 'editar_usuario.html', {'usuario': usuario})
