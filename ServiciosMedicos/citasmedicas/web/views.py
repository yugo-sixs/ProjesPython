# citasmedicas/citashospital/web/views.py
import json
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection
from django.http import JsonResponse
from .models import Usuario, Rol, Estatus, Personal, Especialidad
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password

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

    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        print(f"Intento de login con usuario: {username}")
    
        #buscar usuario en la base de datos
        try:
            user=Usuario.objects.get(
                username=username, 
                password=password,
                estatus_id=1
                )
        except Usuario.DoesNotExist:
            user=None
        if user:
            request.session['usuario_id']=user.id
            request.session['username']=user.username
            request.session['rol']=user.rol.nombre
            print(f"Login exitoso para usuario: {user}")

            rol_nombre = user.rol.nombre 
            print(f"Rol del usuario: {rol_nombre}")
            print(f"Rol sin normalizar (repr): {repr(rol_nombre)}")          

            messages.success(request, f"✅ Bienvenido {user.username}.")

            # Normalizar nombre de rol (quita espacios y ':' y pasa a minúsculas)
            rol_norm = rol_nombre.strip().lower().replace(':', '')
            print(f"Rol normalizado: {rol_norm}")  # ← AGREGA ESTA LÍNEA

            # Redirigir según rol
            if rol_norm in ['admin', 'administrador', 'sa']:
                print("Redirigiendo a crear_usuario para admin/SA")
                return redirect('crear_usuario')
            elif rol_norm == 'doctor':
                print("Redirigiendo a vista_doctor para doctor")
                return redirect('vista_doctor')
                   
            elif rol_norm == 'secretaria':
                print("Redirigiendo a vista_secretaria para secretaria")
                return redirect('vista_secretaria')
            else:
                return redirect('home')
        else:
            messages.error(request, "⚠ Usuario o contraseña incorrectos.")
            print("Error de login: Usuario o contraseña incorrectos.")
            return render(request, 'home')
    return render(request, 'crear_usuario')

def logout(request):
    request.session.flush()
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('home')



def crear_personal(request, personal_id=None):

    # Si viene ID → editar, si no → crear
    if personal_id:
        personal = Personal.objects.get(id=personal_id)
    else:
        personal = Personal()  # OBJETO NUEVO

    especialidades = Especialidad.objects.all()
    usuarios = Usuario.objects.filter(estatus_id=1)

    if request.method == 'POST':
        personal.nombre = request.POST.get('nombre', '').strip()
        personal.apellidopaterno = request.POST.get('apellidopaterno', '').strip()
        personal.apellidomaterno = request.POST.get('apellidomaterno', '').strip()
        personal.telefono = request.POST.get('telefono', '').strip()
        personal.numempleado = request.POST.get('noempleado', '').strip()
        personal.cedula_profesional = request.POST.get('cedulaprofecional', '').strip()
        personal.especialidad_id = request.POST.get('especialidad', '').strip()
        personal.usuario_id = request.POST.get('usuario_id', '').strip()

        personal.save()

        messages.success(request, "Personal guardado correctamente.")
        return redirect('listar_personal')

    return render(request, "crear_personal.html", {
        "personal": personal,
        "especialidades": especialidades,
        "usuarios": usuarios
    })