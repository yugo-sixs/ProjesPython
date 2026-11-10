from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from functools import wraps

from .access import has_permission, has_role, landing_view
from .access import default_permissions
from .forms import (
    AccesoUsuarioForm, CitaForm, ConsultaForm, EntradaInventarioForm, EstudioFormSet, EstudioResultadoForm,
    MedicamentoForm, PacienteForm, PersonalForm, RecetaFormSet,
    UsuarioAdminForm, UrgenciasRecepcionForm, UrgenciasValoracionForm,
)
from .models import (
    AccesoUsuario, Cita, Consulta, Estatus, Especialidad, Estudio, Medicamento,
    MovimientoInventario, Paciente, Personal, RecepcionUrgencias,
)


def _solo_administracion(user):
    return has_role(user, 'administrador')


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if not any(has_role(request.user, role) for role in roles):
                return render(request, '403.html', status=403)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def permission_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if not has_permission(request.user, permission):
                return render(request, '403.html', status=403)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def home(request):
    return render(request, 'home.html')


@login_required
@role_required('administrador')
def crear_usuario(request):
    usuarios = User.objects.filter(is_active=True).prefetch_related('groups')
    form = UsuarioAdminForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    usuario = form.save()
                    if not hasattr(usuario, 'accesousuario'):
                        _sync_access_defaults(usuario)
            except IntegrityError:
                form.add_error('username', 'No se pudo crear la cuenta. Comprueba que el usuario no exista.')
                messages.error(request, 'No se creó el usuario; revisa los campos indicados.')
            else:
                messages.success(request, f"Usuario '{usuario.username}' creado correctamente.")
                return redirect('crear_usuario')
        else:
            messages.error(request, 'No se creó el usuario. Corrige los campos marcados.')
    return render(request, 'crear_usuario.html', {
        'form': form,
        'usuarios': usuarios,
    })


@login_required
@role_required('administrador')
def editar_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    usuarios = User.objects.filter(is_active=True).prefetch_related('groups')
    form = UsuarioAdminForm(request.POST or None, instance=usuario)
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    usuario = form.save()
                    if not hasattr(usuario, 'accesousuario'):
                        _sync_access_defaults(usuario)
            except IntegrityError:
                form.add_error('username', 'No se pudo actualizar la cuenta; comprueba el nombre de usuario.')
                messages.error(request, 'No se actualizaron los datos. Corrige los campos indicados.')
            else:
                messages.success(request, f"Usuario '{usuario.username}' actualizado correctamente.")
                return redirect('crear_usuario')
        else:
            messages.error(request, 'No se actualizaron los datos. Corrige los campos marcados.')

    return render(request, 'crear_usuario.html', {
        'form': form,
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

            return redirect(landing_view(user))

        messages.error(request, "Usuario o contrasena incorrectos.")

    return render(request, 'home.html')


def loogin(request):
    return login_view(request)


def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesion correctamente.")
    return redirect('home')


@login_required
@role_required('administrador')
def crear_personal(request, personal_id=None):
    personal = get_object_or_404(Personal, id=personal_id) if personal_id else Personal()
    especialidades = Especialidad.objects.all()
    usuarios = User.objects.filter(is_active=True)

    form = PersonalForm(request.POST or None, instance=personal)
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    saved_personal = form.save(commit=False)
                    saved_personal.estatus = _estatus_activo()
                    saved_personal.save()
                    grupos_por_tipo = {
                        Personal.DOCTOR: 'Doctor',
                        Personal.ENFERMERA: 'Enfermera',
                        Personal.SECRETARIA: 'Secretaria',
                        Personal.ADMINISTRATIVO: 'Administrativo',
                    }
                    nombre_grupo = grupos_por_tipo.get(saved_personal.tipo_personal)
                    if saved_personal.usuario_id and nombre_grupo:
                        grupo = Group.objects.filter(name=nombre_grupo).first()
                        if grupo:
                            saved_personal.usuario.groups.set([grupo])
                            _sync_access_defaults(saved_personal.usuario)
            except IntegrityError:
                form.add_error(None, 'No se guardó el personal porque un dato único ya está registrado. Revisa usuario, número y cédula.')
                messages.error(request, 'No se guardó el personal. Corrige los datos marcados.')
            else:
                messages.success(request, "Personal guardado correctamente.")
                return redirect('listar_personal')
        else:
            messages.error(request, 'No se guardó el personal. Corrige los campos marcados.')

    return render(request, "crear_personal.html", {
        "personal": personal,
        "tipos_personal": Personal.TIPO_PERSONAL_CHOICES,
        "especialidades": especialidades,
        "usuarios": usuarios,
        "form": form,
    })


@login_required
@role_required('administrador')
def listar_personal(request):
    return render(request, "crear_personal.html", {
        "personal": Personal(),
        "form": PersonalForm(),
        "personal_lista": Personal.objects.select_related('usuario', 'especialidad', 'estatus'),
        "tipos_personal": Personal.TIPO_PERSONAL_CHOICES,
        "especialidades": Especialidad.objects.all(),
        "usuarios": User.objects.filter(is_active=True),
    })


@login_required
@permission_required('puede_atender_citas')
def vista_doctor(request):
    citas = Cita.objects.all()
    if not has_role(request.user, 'administrador'):
        citas = citas.filter(doctor__usuario=request.user)
    citas = citas.exclude(estado=Cita.ESTADO_CHOICES[2][0]).select_related(
        'paciente', 'doctor'
    ).order_by('fecha_cita', 'hora_inicio')
    return render(request, 'listas_citas.html', {'citas': citas, 'titulo': 'Agenda del doctor'})


@login_required
@role_required('secretaria')
def vista_secretaria(request):
    return redirect('listar_citas')


def _estatus_activo():
    estatus, _ = Estatus.objects.get_or_create(pk=1, defaults={'nombre': 'Activo'})
    return estatus


def _sync_access_defaults(user):
    config, _ = AccesoUsuario.objects.get_or_create(usuario=user)
    for field, value in default_permissions(user).items():
        setattr(config, field, value)
    config.vista_inicio = 'AUTO'
    config.save()


@login_required
@role_required('administrador')
def listar_accesos(request):
    usuarios = User.objects.filter(is_active=True).prefetch_related('groups').order_by('username')
    filas = []
    for usuario in usuarios:
        config = getattr(usuario, 'accesousuario', None)
        permisos = (
            {campo: getattr(config, campo) for campo in default_permissions(usuario)}
            if config is not None else default_permissions(usuario)
        )
        permisos['puede_registrar_urgencias'] = has_permission(usuario, 'puede_registrar_urgencias')
        filas.append({
            'usuario': usuario,
            'config': config,
            'permisos': permisos,
            'rol': 'Administrador' if has_role(usuario, 'administrador') else (
                usuario.groups.first().name if usuario.groups.exists() else 'Sin rol'
            ),
        })
    return render(request, 'lista_accesos.html', {'filas': filas})


@login_required
@role_required('administrador')
def editar_accesos_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    config = AccesoUsuario.objects.filter(usuario=usuario).first()
    if config is None:
        config = AccesoUsuario(usuario=usuario)
    form = AccesoUsuarioForm(request.POST or None, instance=config, usuario=usuario)
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    config = form.save(commit=False)
                    config.usuario = usuario
                    config.save()
                    usuario.groups.set([form.cleaned_data['rol']])
                    usuario.grupos_permiso.set(form.cleaned_data['grupos_permiso'])
            except IntegrityError:
                messages.error(request, 'No se guardaron los permisos. Actualiza la página e inténtalo nuevamente.')
            else:
                messages.success(request, f'Permisos y vista de {usuario.username} actualizados.')
                return redirect('crear_usuario')
        else:
            messages.error(request, 'No se guardaron los permisos. Corrige los campos marcados.')
    return render(request, 'editar_accesos_usuario.html', {
        'usuario_objetivo': usuario,
        'form': form,
    })


@login_required
@permission_required('puede_registrar_pacientes')
def listar_pacientes(request):
    pacientes = Paciente.objects.order_by('nombre', 'apellidopaterno')
    return render(request, 'lista_pacientes.html', {'pacientes': pacientes})


@login_required
@permission_required('puede_registrar_pacientes')
def crear_paciente(request):
    form = PacienteForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                paciente = form.save(commit=False)
                paciente.estatus = _estatus_activo()
                paciente.save()
            except IntegrityError:
                form.add_error(None, 'No se pudo registrar al paciente. Comprueba que la CURP o el tarjetón no estén duplicados.')
                messages.error(request, 'Paciente no guardado. Corrige los datos indicados.')
            else:
                messages.success(request, 'Paciente registrado correctamente.')
                return redirect('detalle_paciente', paciente_id=paciente.id)
        else:
            messages.error(request, 'Paciente no guardado. Corrige los campos marcados.')
    return render(request, 'crear_paciente.html', {'form': form})


@login_required
@permission_required('puede_ver_expedientes')
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    consultas = Consulta.objects.filter(cita__paciente=paciente).select_related(
        'cita', 'cita__doctor', 'cita__doctor__especialidad'
    ).prefetch_related('recetas__medicamento', 'estudios').order_by('-fecha_atencion')
    return render(request, 'detalle_paciente.html', {
        'paciente': paciente,
        'consultas': consultas,
        'citas': Cita.objects.filter(paciente=paciente).select_related('doctor').order_by('-fecha_cita'),
        'urgencias': RecepcionUrgencias.objects.filter(paciente=paciente).select_related(
            'registrado_por', 'valorado_por'
        ).order_by('-fecha_ingreso'),
    })


@login_required
@permission_required('puede_agendar_citas')
def crear_cita(request):
    paciente_id = request.GET.get('paciente')
    form = CitaForm(request.POST or None, initial={'paciente': paciente_id} if paciente_id else None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                cita = form.save(commit=False)
                cita.creada_por = request.user
                cita.estatus = _estatus_activo()
                cita.save()
            except IntegrityError:
                form.add_error(None, 'No se pudo guardar la cita. Verifica que los datos sigan disponibles e inténtalo nuevamente.')
                messages.error(request, 'Cita no guardada. Corrige los datos indicados.')
            else:
                messages.success(request, 'Cita creada correctamente.')
                return redirect('listar_citas')
        else:
            messages.error(request, 'Cita no guardada. Corrige los campos marcados.')
    return render(request, 'crear_cita.html', {'form': form})


@login_required
@permission_required('puede_agendar_citas')
def listar_citas(request):
    citas = Cita.objects.select_related('paciente', 'doctor').order_by('-fecha_cita', 'hora_inicio')
    return render(request, 'listas_citas.html', {'citas': citas, 'titulo': 'Citas médicas'})


def _render_consulta(request, cita, consulta_form, receta_formset, estudio_formset):
    return render(request, 'crear_consulta.html', {
        'cita': cita,
        'consulta_form': consulta_form,
        'receta_formset': receta_formset,
        'estudio_formset': estudio_formset,
    })


@login_required
@permission_required('puede_atender_citas')
def crear_consulta(request, cita_id):
    cita = get_object_or_404(
        Cita.objects.select_related('paciente', 'doctor'), id=cita_id
    )
    if not (has_role(request.user, 'administrador') or cita.doctor.usuario_id == request.user.id):
        messages.error(request, 'Solo el doctor asignado puede registrar esta consulta.')
        return redirect('listar_citas')
    if hasattr(cita, 'consulta'):
        return redirect('detalle_paciente', paciente_id=cita.paciente_id)

    consulta_form = ConsultaForm(request.POST or None)
    receta_formset = RecetaFormSet(request.POST or None, instance=Consulta())
    estudio_formset = EstudioFormSet(request.POST or None, instance=Consulta())
    if request.method == 'POST' and consulta_form.is_valid() and receta_formset.is_valid() and estudio_formset.is_valid():
        receta_datos = [form.cleaned_data for form in receta_formset if form.cleaned_data]
        cantidades = {}
        for item in receta_datos:
            medicamento = item['medicamento']
            cantidades[medicamento.id] = cantidades.get(medicamento.id, 0) + item['cantidad']

        with transaction.atomic():
            medicamentos = {
                med.id: med for med in Medicamento.objects.select_for_update().filter(
                    id__in=cantidades
                ).order_by('id')
            }
            faltantes = []
            for med_id, cantidad in cantidades.items():
                medicamento = medicamentos.get(med_id)
                if medicamento is None:
                    faltantes.append('Un medicamento seleccionado ya no está disponible.')
                elif medicamento.existencia < cantidad:
                    faltantes.append(
                        f"{medicamento.nombre}: disponibles {medicamento.existencia}, "
                        f"solicitados {cantidad}"
                    )
            if faltantes:
                messages.error(request, 'Existencia insuficiente. ' + '; '.join(faltantes))
                return _render_consulta(request, cita, consulta_form, receta_formset, estudio_formset)

            consulta = consulta_form.save(commit=False)
            consulta.cita = cita
            consulta.save()
            for form in receta_formset:
                if not form.cleaned_data:
                    continue
                receta = form.save(commit=False)
                receta.consulta = consulta
                receta.save()
                medicamento = medicamentos[receta.medicamento_id]
                medicamento.existencia -= receta.cantidad
                medicamento.save(update_fields=['existencia'])
                MovimientoInventario.objects.create(
                    medicamento=medicamento,
                    tipo=MovimientoInventario.DISPENSACION,
                    cantidad=receta.cantidad,
                    existencia_resultante=medicamento.existencia,
                    receta=receta,
                    usuario=request.user,
                    nota=f'Receta de la consulta {consulta.id}',
                )
            for form in estudio_formset:
                if form.cleaned_data:
                    estudio = form.save(commit=False)
                    estudio.consulta = consulta
                    estudio.save()
            cita.estado = 'ATENDIDA'
            cita.save(update_fields=['estado'])
        messages.success(request, 'Consulta registrada; recetas descontadas del inventario.')
        return redirect('detalle_paciente', paciente_id=cita.paciente_id)
    if request.method == 'POST':
        messages.error(request, 'La consulta no se guardó. Corrige los campos de consulta, recetas y estudios marcados.')
    return _render_consulta(request, cita, consulta_form, receta_formset, estudio_formset)


@login_required
@permission_required('puede_atender_citas')
def actualizar_resultado_estudio(request, estudio_id):
    estudio = get_object_or_404(
        Estudio.objects.select_related('consulta__cita__doctor'), id=estudio_id,
    )
    if not (has_role(request.user, 'administrador') or
            estudio.consulta.cita.doctor.usuario_id == request.user.id):
        messages.error(request, 'Solo el doctor asignado puede actualizar este estudio.')
        return redirect('detalle_paciente', paciente_id=estudio.consulta.cita.paciente_id)
    form = EstudioResultadoForm(request.POST or None, instance=estudio)
    if request.method == 'POST' and form.is_valid():
        estudio = form.save(commit=False)
        if estudio.estatus == 'REALIZADO' and estudio.fecha_resultado is None:
            estudio.fecha_resultado = timezone.now()
        estudio.save()
        messages.success(request, 'Resultado de estudio actualizado.')
        return redirect('detalle_paciente', paciente_id=estudio.consulta.cita.paciente_id)
    if request.method == 'POST':
        messages.error(request, 'El resultado no se guardó. Corrige los campos marcados.')
    return render(request, 'actualizar_estudio.html', {'form': form, 'estudio': estudio})


@login_required
@permission_required('puede_ver_inventario')
def inventario(request):
    return _render_inventario(request)


def _render_inventario(request, entrada_form=None, medicamento_form=None):
    medicamentos = Medicamento.objects.order_by('nombre')
    movimientos = MovimientoInventario.objects.select_related(
        'medicamento', 'usuario'
    ).order_by('-fecha')[:50]
    return render(request, 'inventario.html', {
        'medicamentos': medicamentos,
        'movimientos': movimientos,
        'form': entrada_form or EntradaInventarioForm(),
        'medicamento_form': medicamento_form or MedicamentoForm(),
    })


@login_required
@role_required('administrador')
def crear_medicamento(request):
    if not _solo_administracion(request.user):
        messages.error(request, 'No tienes permiso para modificar el inventario.')
        return redirect('inventario')
    form = MedicamentoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    medicamento = form.save(commit=False)
                    cantidad = form.cleaned_data['existencia_inicial']
                    medicamento.existencia = cantidad
                    medicamento.save()
                    if cantidad:
                        MovimientoInventario.objects.create(
                            medicamento=medicamento, tipo=MovimientoInventario.ENTRADA,
                            cantidad=cantidad, existencia_resultante=cantidad,
                            usuario=request.user, nota='Existencia inicial',
                        )
            except IntegrityError:
                form.add_error(None, 'No se pudo agregar el medicamento. Puede que ya exista un medicamento con ese nombre.')
                messages.error(request, 'Medicamento no guardado. Corrige los datos indicados.')
                return _render_inventario(request, medicamento_form=form)
            messages.success(request, 'Medicamento agregado al inventario.')
            return redirect('inventario')
        messages.error(request, 'Medicamento no guardado. Corrige los campos marcados.')
        return _render_inventario(request, medicamento_form=form)
    return redirect('inventario')


@login_required
@role_required('administrador')
def entrada_inventario(request):
    if not _solo_administracion(request.user):
        messages.error(request, 'No tienes permiso para modificar el inventario.')
        return redirect('inventario')
    form = EntradaInventarioForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    medicamento = Medicamento.objects.select_for_update().get(
                        id=form.cleaned_data['medicamento'].id
                    )
                    medicamento.existencia += form.cleaned_data['cantidad']
                    medicamento.save(update_fields=['existencia'])
                    MovimientoInventario.objects.create(
                        medicamento=medicamento, tipo=MovimientoInventario.ENTRADA,
                        cantidad=form.cleaned_data['cantidad'],
                        existencia_resultante=medicamento.existencia,
                        usuario=request.user, nota=form.cleaned_data['nota'],
                    )
            except (IntegrityError, Medicamento.DoesNotExist):
                form.add_error(None, 'No se pudo registrar la entrada. El medicamento pudo cambiar o eliminarse; actualiza la página.')
                messages.error(request, 'Entrada no guardada. Revisa los datos e inténtalo nuevamente.')
                return _render_inventario(request, entrada_form=form)
            messages.success(request, 'Entrada registrada correctamente.')
            return redirect('inventario')
        messages.error(request, 'Entrada no guardada. Corrige los campos marcados.')
        return _render_inventario(request, entrada_form=form)
    return redirect('inventario')


@login_required
@permission_required('puede_ver_urgencias')
def listar_urgencias(request):
    recepciones = RecepcionUrgencias.objects.select_related(
        'paciente', 'registrado_por', 'valorado_por', 'cita'
    ).order_by('fecha_salida', 'fecha_ingreso')
    return render(request, 'lista_urgencias.html', {'recepciones': recepciones})


@login_required
@permission_required('puede_registrar_urgencias')
def registrar_urgencias(request):
    personal_registrador = Personal.objects.filter(usuario=request.user).first()
    if personal_registrador is None:
        messages.error(
            request,
            'Tu cuenta tiene el permiso de Urgencias, pero debe vincularse con un registro de Personal para identificar quién recibió al paciente.',
        )
        return redirect('listar_urgencias')

    form = UrgenciasRecepcionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        periodo = timezone.localtime(form.cleaned_data['fecha_ingreso']).strftime('%y%m')
        for intento in range(3):
            try:
                with transaction.atomic():
                    ultimo_folio = RecepcionUrgencias.objects.select_for_update().filter(
                        folio__startswith=periodo
                    ).order_by('-folio').values_list('folio', flat=True).first()
                    consecutivo = int(ultimo_folio[-4:]) + 1 if ultimo_folio else 1
                    if consecutivo > 9999:
                        raise ValidationError('Se agotaron los folios disponibles para este mes.')
                    recepcion = form.save(commit=False)
                    recepcion.folio = f'{periodo}{consecutivo:04d}'
                    recepcion.registrado_por = personal_registrador
                    recepcion.save()
                messages.success(request, f'Recepción registrada con folio {recepcion.folio}.')
                return redirect('listar_urgencias')
            except IntegrityError:
                if intento == 2:
                    form.add_error(None, 'No se pudo asignar un folio único. Actualiza la página e inténtalo nuevamente.')
                    messages.error(request, 'El ingreso no se guardó. No se pudo reservar el folio.')
                    return render(request, 'registrar_urgencias.html', {'form': form})
            except ValidationError as error:
                form.add_error(None, error)
                messages.error(request, 'El ingreso no se guardó. Revisa el mensaje del formulario.')
                return render(request, 'registrar_urgencias.html', {'form': form})
    elif request.method == 'POST':
        messages.error(request, 'El ingreso no se guardó. Corrige los campos marcados.')
    return render(request, 'registrar_urgencias.html', {'form': form})


@login_required
@permission_required('puede_valorar_urgencias')
def valorar_urgencias(request, recepcion_id):
    medico = Personal.objects.filter(
        usuario=request.user, tipo_personal=Personal.DOCTOR
    ).first()
    if medico is None:
        return render(request, '403.html', status=403)
    recepcion = get_object_or_404(
        RecepcionUrgencias.objects.select_related('paciente', 'registrado_por'),
        id=recepcion_id,
    )
    form = UrgenciasValoracionForm(request.POST or None, instance=recepcion)
    if request.method == 'POST' and form.is_valid():
        recepcion = form.save(commit=False)
        if recepcion.cita_id and recepcion.paciente_id is None:
            recepcion.paciente = recepcion.cita.paciente
        recepcion.valorado_por = medico
        recepcion.fecha_valoracion = timezone.now()
        if recepcion.estado in {'HOSPITALIZADO', 'REFERIDO', 'EGRESO'}:
            recepcion.fecha_salida = recepcion.fecha_salida or timezone.now()
        else:
            recepcion.fecha_salida = None
        recepcion.save()
        messages.success(request, f'Triage y valoración médica guardados para el folio {recepcion.folio}.')
        return redirect('listar_urgencias')
    if request.method == 'POST':
        messages.error(request, 'La valoración no se guardó. Corrige los campos marcados.')
    return render(request, 'valorar_urgencias.html', {
        'recepcion': recepcion,
        'form': form,
    })
