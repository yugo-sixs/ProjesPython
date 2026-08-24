from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .models import Especialidad, Personal


def home(request):
    return render(request, 'home.html')


def crear_usuario(request):
    roles = Group.objects.all()
    usuarios = User.objects.filter(is_active=True).prefetch_related('groups')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password1 = request.POST.get('password1', '').strip()
        rol_id = request.POST.get('rol', '').strip()

        if not username or not password or not rol_id:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, 'crear_usuario.html', {'roles': roles, 'usuarios': usuarios})

        if password != password1:
            messages.error(request, "Las contrasenas no coinciden.")
            return render(request, 'crear_usuario.html', {'roles': roles, 'usuarios': usuarios})

        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe.")
            return render(request, 'crear_usuario.html', {'roles': roles, 'usuarios': usuarios})

        try:
            rol = Group.objects.get(id=rol_id)
            usuario = User.objects.create_user(username=username, password=password)
            usuario.groups.add(rol)
            messages.success(request, f"Usuario '{username}' creado correctamente.")
            usuarios = User.objects.filter(is_active=True).prefetch_related('groups')
        except Group.DoesNotExist:
            messages.error(request, "Rol no valido.")
        except IntegrityError:
            messages.error(request, f"Error al crear el usuario '{username}'.")

    return render(request, 'crear_usuario.html', {
        'roles': roles,
        'usuarios': usuarios,
    })


def editar_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    roles = Group.objects.all()
    usuarios = User.objects.filter(is_active=True).prefetch_related('groups')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password1 = request.POST.get('password1', '').strip()
        rol_id = request.POST.get('rol', '').strip()

        if not username or not rol_id:
            messages.error(request, "Todos los campos son obligatorios.")
        elif password and password != password1:
            messages.error(request, "Las contrasenas no coinciden.")
        else:
            try:
                usuario.username = username
                if password:
                    usuario.set_password(password)
                usuario.save()
                usuario.groups.set([Group.objects.get(id=rol_id)])
                messages.success(request, f"Usuario '{username}' actualizado correctamente.")
                return redirect('crear_usuario')
            except Group.DoesNotExist:
                messages.error(request, "Rol no valido.")
            except IntegrityError:
                messages.error(request, f"Error al actualizar el usuario '{username}'.")

    return render(request, 'crear_usuario.html', {
        'roles': roles,
        'usuarios': usuarios,
        'editando': True,
        'usuario_editar': usuario,
        'rol_actual': usuario.groups.first(),
    })


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)
            messages.success(request, f"Bienvenido {user.username}.")

            grupos = set(user.groups.values_list('name', flat=True))
            grupos_norm = {grupo.strip().lower().replace(':', '') for grupo in grupos}

            if grupos_norm.intersection({'admin', 'administrador', 'sa'}):
                return redirect('crear_usuario')
            if 'doctor' in grupos_norm:
                return redirect('vista_doctor')
            if 'secretaria' in grupos_norm:
                return redirect('vista_secretaria')
            return redirect('home')

        messages.error(request, "Usuario o contrasena incorrectos.")

    return render(request, 'home.html')


def loogin(request):
    return login_view(request)


def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesion correctamente.")
    return redirect('home')


def crear_personal(request, personal_id=None):
    personal = get_object_or_404(Personal, id=personal_id) if personal_id else Personal()
    especialidades = Especialidad.objects.all()
    usuarios = User.objects.filter(is_active=True)

    if request.method == 'POST':
        noempleado = request.POST.get('noempleado', '').strip()

        personal.usuario_id = request.POST.get('usuario_id') or None
        personal.tipo_personal = request.POST.get('tipo_personal') or Personal.ADMINISTRATIVO
        personal.nombre = request.POST.get('nombre', '').strip()
        personal.apellidopaterno = request.POST.get('apellidopaterno', '').strip()
        personal.apellidomaterno = request.POST.get('apellidomaterno', '').strip()
        personal.telefono = request.POST.get('telefono', '').strip()
        personal.numempleado = int(noempleado) if noempleado else None
        personal.cedula_profesional = request.POST.get('cedulaprofecional', '').strip()
        personal.especialidad_id = request.POST.get('especialidad') or None
        personal.save()

        messages.success(request, "Personal guardado correctamente.")
        return redirect('listar_personal')

    return render(request, "crear_personal.html", {
        "personal": personal,
        "tipos_personal": Personal.TIPO_PERSONAL_CHOICES,
        "especialidades": especialidades,
        "usuarios": usuarios,
    })


def listar_personal(request):
    return render(request, "crear_personal.html", {
        "personal": Personal(),
        "personal_lista": Personal.objects.select_related('usuario', 'especialidad', 'estatus'),
        "tipos_personal": Personal.TIPO_PERSONAL_CHOICES,
        "especialidades": Especialidad.objects.all(),
        "usuarios": User.objects.filter(is_active=True),
    })


def vista_doctor(request):
    return render(request, 'home.html')


def vista_secretaria(request):
    return render(request, 'home.html')
