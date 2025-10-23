# citasmedicas/citashospital/web/views.py
import json
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection
from django.http import JsonResponse
from .models import Usuario, Rol, Estatus, Personal, Especialidad
from django.db import IntegrityError



def home(request):
    return render(request, 'home.html')



def crear_usuario(request):
    roles = Rol.objects.all()
    usuarios = Usuario.objects.filter(estatus_id=1).select_related('rol')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password1 = request.POST.get('password1', '').strip()
        rol_id = request.POST.get('rol', '').strip()

        # Validar campos vacíos
        if not username or not password or not rol_id:
            messages.error(request, "⚠ Todos los campos son obligatorios.")
            return render(request, 'crear_usuario.html', {'roles': roles, 'usuarios': usuarios})

        # Validar contraseñas
        if password != password1:
            messages.error(request, "⚠ Las contraseñas no coinciden.")
            return render(request, 'crear_usuario.html', {'roles': roles, 'usuarios': usuarios})
        
        # Validar si el usuario ya existe
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, "⚠ El nombre de usuario ya existe.")
            return render(request, 'crear_usuario.html', {'roles': roles, 'usuarios': usuarios})
        
        try:
            rol = Rol.objects.get(id=rol_id)
            estatus = Estatus.objects.get(id=1)  # Activo por defecto
            Usuario.objects.create(
                username=username,
                password=password,# parte con encriptacion password=make_password(password),
                rol=rol,
                estatus=estatus
            )

            messages.success(request, f"✅ Usuario '{username}' creado correctamente.")
            usuarios = Usuario.objects.filter(estatus_id=1).select_related('rol')
         
        except Rol.DoesNotExist:
            messages.error(request, "⚠ Rol no válido.")
        except IntegrityError:
            messages.error(request, f"⚠ Error al crear el usuario '{username}'.")

    # Render principal (GET o si hubo error)
    return render(request, 'crear_usuario.html', {
        'roles': roles,
        'usuarios': usuarios
    })


def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    roles = Rol.objects.all()
    usuarios = Usuario.objects.filter(estatus_id=1).select_related('rol')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password1 = request.POST.get('password1', '').strip()
        rol_id = request.POST.get('rol', '').strip()

        if not username or not rol_id:
            messages.error(request, "⚠ Todos los campos son obligatorios.")
            return render(request, 'edit_usuario.html', {'usuario': usuario, 'roles': roles})
        elif password and password != password1:
            messages.error(request, "⚠ Las contraseñas no coinciden.")
            return render(request, 'edit_usuario.html', {'usuario': usuario, 'roles': roles})
        else:
            try:
                rol = Rol.objects.get(id=rol_id)
                usuario.username = username
                usuario.rol = rol
                if password:
                    usuario.password = password  # parte con encriptacion usuario.password = make_password(password)
                usuario.save()
                messages.success(request, f"✅ Usuario '{username}' actualizado correctamente.")
                return redirect('crear_usuario')
            except Rol.DoesNotExist:
                messages.error(request, "⚠ Rol no válido.")
            except IntegrityError:
                messages.error(request, f"⚠ Error al actualizar el usuario '{username}'.")
                
    return render(request, 'crear_usuario.html', {
        'roles': roles,
        'usuarios': usuarios,
        'editando': True,
        'usuario_editar': usuario
    })

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



def crear_personal(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        especialidad = request.POST.get('especialidad', '').strip()

        if not nombre or not especialidad:
            messages.error(request, "⚠ Todos los campos son obligatorios.")
            return render(request, 'crear_personal.html')

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO personal_medico (nombre, especialidad)
                VALUES (%s, %s)
            """, [nombre, especialidad])
            messages.success(request, "✅ Doctor creado correctamente.")
        return redirect('home')

    return render(request, 'crear_personal.html')