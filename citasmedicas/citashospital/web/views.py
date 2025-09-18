# citasmedicas/citashospital/web/views.py
import json
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse

def home(request):
    return render(request, 'home.html')

def listar_usuarios(request):
    with connection.cursor() as cursor:
        # Hacemos un JOIN para obtener el nombre del rol
        cursor.execute("""
            SELECT usuario.id, usuario.username, rol.nombre
            FROM usuario
            JOIN rol ON usuario.rol_id = rol.id
            WHERE usuario.estatus_id = 1
        """)
        rows = cursor.fetchall()

    usuarios = []
    for row in rows:
        usuarios.append({
            'id': row[0],
            'username': row[1],
            'rol': row[2],  # Ahora 'rol' es el nombre del rol
        })

    return render(request, 'listar_usuarios.html', {'usuarios': usuarios})


# views.py
def crear_usuario(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM rol")
        roles = cursor.fetchall()
    roles = [{'id': r[0], 'nombre': r[1]} for r in roles]

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        # Este será el ID del rol seleccionado
        rol_id = request.POST.get('rol', '').strip()

        # Validación de campos vacíos
        if not username or not password or not rol_id:
            messages.error(request, "⚠ Todos los campos son obligatorios.")
            return render(request, 'crear_usuario.html', {'roles': roles})

        if password != request.POST.get('password1', '').strip():
            messages.error(request, "⚠ Las contraseñas no coinciden.")
            # Si las contraseñas no coinciden, volvemos a renderizar
            # el formulario
            return render(request, 'crear_usuario.html', {'roles': roles, 'username': username})
        
        # Verificación de duplicado
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM usuario WHERE username = %s", [username])
            count = cursor.fetchone()[0]

        if count > 0:
            messages.error(request, f"⚠ El usuario '{username}' ya existe.")
            return render(request, 'crear_usuario.html', {'roles': roles})

        # Inserción del nuevo usuario
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO usuario (username, password, rol_id, estatus_id)
                VALUES (%s, %s, %s, %s)
            """, [username, password, rol_id, 1])  # Asumiendo que 1 = activo
            messages.success(request, "✅ Usuario creado correctamente.")
        return redirect('listar_usuarios')

    return render(request, 'crear_usuario.html', {'roles': roles})


def editar_usuario(request, usuario_id):
    # Obtenemos el usuario y su rol
    # if request.session.get('rol') != 'admin':
    #     messages.error(request, "⚠ No tienes permiso para editar usuarios.")
    #     return redirect('listar_usuarios')

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT usuario.id, usuario.username, usuario.password,
                   rol.id, rol.nombre
            FROM usuario
            JOIN rol ON usuario.rol_id = rol.id
            WHERE usuario.id=%s
            """,
            [usuario_id]
        )
        row = cursor.fetchone()
    if not row:
        messages.error(request, "Usuario no encontrado.")
        return redirect('listar_usuarios')

    usuario = {
        'id': row[0],
        'username': row[1],
        'password': row[2],
        'rol_id': row[3],      # ID del rol
        'rol_nombre': row[4],  # Nombre del rol
    }

    # Obtener lista de roles para el formulario
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM rol")
        roles = cursor.fetchall()
    roles = [{'id': r[0], 'nombre': r[1]} for r in roles]

    if usuario['rol_nombre'] == 'admin':
        messages.warning(
            request, "No está permitido editar un usuario con rol 'admin'.")
        return redirect('listar_usuarios')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        rol_id = request.POST.get('rol', '').strip()

        if not username or not password or not rol_id:
            messages.error(request, "⚠ Todos los campos son obligatorios.")
            return render(request, 'editar_usuario.html', {'usuario': usuario, 'roles': roles})

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE usuario
                SET username=%s, password=%s, rol_id=%s
                WHERE id=%s
            """, [username, password, rol_id, usuario_id])

        messages.success(request, "Usuario actualizado correctamente.")
        return redirect('listar_usuarios')

    return render(request, 'editar_usuario.html', {'usuario': usuario, 'roles': roles})


def desactivar_usuario(request, usuario_id):
    with connection.cursor() as cursor:
        # Cambia el estatus_id a "2" o el ID correspondiente a "desactivado"
        cursor.execute("""
            UPDATE usuario
            SET estatus_id = %s
            WHERE id = %s
        """, [2, usuario_id])
    return redirect('listar_usuarios')


def actualizar_usuario(request, usuario_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        rol = data.get('rol')

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE usuario
                SET username=%s, rol=%s
                WHERE id=%s
            """, [username, rol, usuario_id])

        return JsonResponse({'status': 'ok'})


def loogin(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        print(f"Intento de login con usuario: {username}")
    
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, rol_id FROM usuario
                WHERE username=%s AND password=%s AND estatus_id=1
            """, [username, password])
            user = cursor.fetchone()

        if user:
            request.session['user_id'] = user[0]
            request.session['username'] = user[1]
            request.session['rol_id'] = user[2]
            print(f"Usuario encontrado: {user}")

            with connection.cursor() as cursor:
                cursor.execute("SELECT nombre FROM rol WHERE id=%s", [user[2]])
                rol_nombre = cursor.fetchone()[0]
            print(f"Rol del usuario: {rol_nombre}")

            messages.success(request, f"Bienvenido, {username}!")

            if rol_nombre in ['admin', 'administrador']:
                return redirect('listar_usuarios')
            elif rol_nombre == 'doctor':
                return redirect('vista_doctor')  
            elif rol_nombre == 'secretaria':
                return redirect('vista_secretaria')
            else:
                return redirect('home')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, 'home.html')

    return render(request, 'home.html')



def logout(request):
    request.session.flush()
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('home')



def crear_cita(request):
    if request.method == 'POST':
        # Aquí iría la lógica para crear una cita
        messages.success(request, "Cita creada correctamente.")
        return redirect('listar_citas')

    return render(request, 'crear_cita.html') 
def listar_citas(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cita.id, cita.fecha, cita.hora, usuario.username, doctor.nombre
            FROM cita
            JOIN usuario ON cita.usuario_id = usuario.id
            JOIN doctor ON cita.doctor_id = doctor.id
            WHERE cita.estatus_id = 1
        """)
        rows = cursor.fetchall()

    citas = []
    for row in rows:
        citas.append({
            'id': row[0],
            'fecha': row[1],
            'hora': row[2],
            'usuario': row[3],
            'doctor': row[4],
        })

    return render(request, 'listar_citas.html', {'citas': citas})   

def editar_cita(request, cita_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cita.id, cita.fecha, cita.hora, usuario.id, doctor.id
            FROM cita
            JOIN usuario ON cita.usuario_id = usuario.id
            JOIN doctor ON cita.doctor_id = doctor.id
            WHERE cita.id=%s
        """, [cita_id])
        row = cursor.fetchone()
    if not row:
        messages.error(request, "Cita no encontrada.")
        return redirect('listar_citas')

    cita = {
        'id': row[0],
        'fecha': row[1],
        'hora': row[2],
        'usuario_id': row[3],
        'doctor_id': row[4],
    }

    # Obtener lista de usuarios y doctores para el formulario
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username FROM usuario WHERE estatus_id=1")
        usuarios = cursor.fetchall()
        cursor.execute("SELECT id, nombre FROM doctor WHERE estatus_id=1")
        doctores = cursor.fetchall()
    usuarios = [{'id': u[0], 'username': u[1]} for u in usuarios]
    doctores = [{'id': d[0], 'nombre': d[1]} for d in doctores]

    if request.method == 'POST':
        fecha = request.POST.get('fecha', '').strip()
        hora = request.POST.get('hora', '').strip()
        usuario_id = request.POST.get('usuario', '').strip()
        doctor_id = request.POST.get('doctor', '').strip()

        if not fecha or not hora or not usuario_id or not doctor_id:
            messages.error(request, "⚠ Todos los campos son obligatorios.")
            return render(request, 'editar_cita.html', {'cita': cita, 'usuarios': usuarios, 'doctores': doctores})

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE cita
                SET fecha=%s, hora=%s, usuario_id=%s, doctor_id=%s
                WHERE id=%s
            """, [fecha, hora, usuario_id, doctor_id, cita_id])

        messages.success(request, "Cita actualizada correctamente.")
        return redirect('listar_citas')

    return render(request, 'editar_cita.html', {'cita': cita, 'usuarios': usuarios, 'doctores': doctores})

def eliminar_cita(request, cita_id):
    with connection.cursor() as cursor:
        # Cambia el estatus_id a "2" o el ID correspondiente a "desactivado"
        cursor.execute("""
            UPDATE cita
            SET estatus_id = %s
            WHERE id = %s
        """, [2, cita_id])
    messages.success(request, "Cita eliminada correctamente.")
    return redirect('listar_citas')



#def crear_doctor(request):
#    if request.method == "POST":
#       nombre = request.POST["nombre"]
#      especialidad_id = request.POST["especialidad"]
#        cedula = request.POST["cedula"]
#        telefono = request.POST["telefono"]
#       correo = request.POST["email"]   # ahora coincide con el formulario
#       usuario_id= request.POST["usuario"]

#       with connection.cursor() as cursor:
#           cursor.execute("""
#               INSERT INTO doctor (nombre, especialidad_id, cedula_profesional, telefono, correo,usuario_id)
#               VALUES (%s, %s, %s, %s, %s)
#           """, [nombre, especialidad_id, cedula, telefono, correo,usuario_id])

    # Traer especialidades
#   with connection.cursor() as cursor:
#        cursor.execute("SELECT id, nombre FROM especialidad")
#       especialidades = cursor.fetchall()
#   especialidades = [{'id': e[0], 'nombre': e[1]} for e in especialidades]

    # Traer usuarios
#   with connection.cursor() as cursor:
#       cursor.execute("SELECT id, username FROM usuario WHERE estatus_id=1")
#        usuarios = cursor.fetchall()    
#   usuarios = [{'id': u[0], 'nombre': u[1]} for u in usuarios]

    # Traer doctores
#   with connection.cursor() as cursor:
#       cursor.execute("""
#            SELECT d.id, d.nombre, e.nombre, d.cedula_profesional, d.telefono, d.correo
#           FROM doctor d
#            JOIN especialidad e ON d.especialidad_id = e.id
#           WHERE d.estatus_id = 1
#        """)
#        doctores = cursor.fetchall()

#    doctores = [
#       {
#           "id": d[0],
#           "nombre": d[1],
#           "especialidad": d[2],
#           "cedula_profesional": d[3],
#           "telefono": d[4],
#           "correo": d[5]
#       }
#       for d in doctores
#  ]

#   return render(request, "crear_doctor.html", {
#       "especialidades": especialidades,
#       "usuarios": usuarios,
#       "doctores": doctores
#   })


from django.shortcuts import render, redirect
from django.db import connection

from django.db import connection
from django.shortcuts import render, redirect

def crear_o_editar_doctor(request, id=None):
    doctor = None  # Para precargar datos si estamos editando

    if request.method == "POST":
        # 🔹 Recibir datos del formulario
        id = request.POST.get("id")
        nombre = request.POST.get("nombre")
        especialidad_id = request.POST.get("especialidad")
        cedula_profesional = request.POST.get("cedula")
        telefono = request.POST.get("telefono")
        correo = request.POST.get("email")
        usuario_id = request.POST.get("usuario_id")

        with connection.cursor() as cursor:
            if id:  # 🔹 EDITAR
                cursor.execute("""
                    UPDATE doctor 
                    SET nombre=%s, especialidad_id=%s, cedula_profesional=%s, 
                        telefono=%s, correo=%s, usuario_id=%s
                    WHERE id=%s
                """, [nombre, especialidad_id, cedula_profesional, telefono, correo, usuario_id, id])
            else:  # 🔹 CREAR
                cursor.execute("""
                    INSERT INTO doctor (nombre, especialidad_id, cedula_profesional, telefono, correo, usuario_id, estatus_id)
                    VALUES (%s, %s, %s, %s, %s, %s, 1)
                """, [nombre, especialidad_id, cedula_profesional, telefono, correo, usuario_id])

        return redirect("crear_doctor")

    # 🔹 Si es GET, cargar datos para editar
    if id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, nombre, especialidad_id, cedula_profesional, telefono, correo, usuario_id
                FROM doctor WHERE id=%s
            """, [id])
            row = cursor.fetchone()
            if row:
                doctor = {
                    "id": row[0],
                    "nombre": row[1],
                    "especialidad_id": row[2],
                    "cedula_profesional": row[3],
                    "telefono": row[4],
                    "correo": row[5],
                    "usuario_id": row[6],
                }

    # 🔹 Obtener especialidades
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM especialidad ORDER BY nombre")
        especialidades = [{"id": e[0], "nombre": e[1]} for e in cursor.fetchall()]

    # 🔹 Obtener usuarios
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username FROM usuario ORDER BY username")
        usuarios = [{"id": u[0], "username": u[1]} for u in cursor.fetchall()]

    # 🔹 Obtener lista de doctores
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.nombre, e.nombre AS especialidad, d.cedula_profesional,
                   d.telefono, d.correo, u.username AS usuario
            FROM doctor d
            LEFT JOIN especialidad e ON d.especialidad_id = e.id
            LEFT JOIN usuario u ON d.usuario_id = u.id
            ORDER BY d.id
        """)
        doctores = [{
            "id": row[0],
            "nombre": row[1],
            "especialidad": row[2],
            "cedula_profesional": row[3],
            "telefono": row[4],
            "correo": row[5],
            "usuario": row[6],
        } for row in cursor.fetchall()]

    # 🔹 Renderizar template
    return render(request, "crear_doctor.html", {
        "especialidades": especialidades,
        "usuarios": usuarios,
        "doctores": doctores,
        "doctor": doctor,
    })

     
    

 
def eliminar_doctor(request, id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE doctor SET estatus_id = %s WHERE id = %s", [2, id])
    messages.success(request, "Doctor eliminado correctamente.")
    return redirect("crear_doctor")