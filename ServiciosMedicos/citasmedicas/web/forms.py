from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.forms import CheckboxSelectMultiple

from .access import default_permissions
from .models import (
    AccesoUsuario, Cita, Consulta, Estudio, GrupoPermiso, Medicamento, Paciente, Personal,
    RecepcionUrgencias, Receta,
)

UserModel = get_user_model()


class UsuarioAdminForm(forms.Form):
    username = forms.CharField(max_length=150, label='Usuario')
    password = forms.CharField(
        required=False, label='Contraseña',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password1 = forms.CharField(
        required=False, label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    rol = forms.ModelChoiceField(queryset=Group.objects.none(), label='Rol')

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        self.fields['rol'].queryset = Group.objects.exclude(
            name__in=['Urgencias', 'Seguridad']
        ).order_by('name')
        if instance:
            self.fields['username'].initial = instance.username
            self.fields['rol'].initial = instance.groups.first()
            self.fields['password'].help_text = 'Deja vacío para conservar la contraseña actual.'
        else:
            self.fields['password'].required = True
            self.fields['password1'].required = True

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        UserModel._meta.get_field('username').clean(username, self.instance)
        duplicates = UserModel.objects.filter(username=username)
        if self.instance and self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('Ese nombre de usuario ya está ocupado.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password', '')
        confirmation = cleaned_data.get('password1', '')
        if not self.instance and not password:
            self.add_error('password', 'La contraseña es obligatoria al crear la cuenta.')
        if password or confirmation:
            if password != confirmation:
                self.add_error('password1', 'Las contraseñas no coinciden.')
            elif password:
                try:
                    password_user = self.instance or UserModel(username=cleaned_data.get('username', ''))
                    validate_password(password, password_user)
                except forms.ValidationError as error:
                    self.add_error('password', error)
        return cleaned_data

    def save(self):
        user = self.instance or UserModel()
        user.username = self.cleaned_data['username']
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        elif not self.instance:
            raise ValueError('La contraseña es obligatoria al crear la cuenta.')
        user.save()
        user.groups.set([self.cleaned_data['rol']])
        return user


class AccesoUsuarioForm(forms.ModelForm):
    rol = forms.ModelChoiceField(queryset=Group.objects.all(), label='Rol')
    grupos_permiso = forms.ModelMultipleChoiceField(
        queryset=GrupoPermiso.objects.none(),
        required=False,
        label='Grupos de permisos adicionales',
        help_text='Asigna permisos de operación sin cambiar el rol laboral de la persona.',
        widget=CheckboxSelectMultiple,
    )

    class Meta:
        model = AccesoUsuario
        fields = [
            'vista_inicio', 'puede_registrar_pacientes', 'puede_ver_expedientes',
            'puede_agendar_citas', 'puede_atender_citas', 'puede_ver_inventario',
            'puede_ver_urgencias', 'puede_valorar_urgencias',
        ]
        labels = {
            'puede_ver_expedientes': 'Puede consultar expedientes médicos',
            'puede_agendar_citas': 'Puede abrir y agendar citas',
            'puede_atender_citas': 'Puede abrir agenda y atender citas',
            'puede_ver_inventario': 'Puede consultar el inventario',
            'puede_ver_urgencias': 'Puede consultar la bitácora de urgencias',
            'puede_valorar_urgencias': 'Puede valorar y asignar triage (personal médico)',
        }

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario_objetivo = usuario
        self.fields['rol'].initial = usuario.groups.first()
        permission_groups = GrupoPermiso.objects.filter(puede_registrar_urgencias=True).order_by('nombre')
        self.fields['grupos_permiso'].queryset = permission_groups
        self.fields['grupos_permiso'].initial = usuario.grupos_permiso.filter(
            puede_registrar_urgencias=True
        )
        if not self.fields['rol'].initial and usuario.is_superuser:
            self.fields['rol'].initial = Group.objects.filter(name='Administrador').first()
        if not self.instance.pk:
            defaults = default_permissions(usuario)
            for field, value in defaults.items():
                self.fields[field].initial = value
        self.fields['rol'].queryset = Group.objects.exclude(
            name__in=['Urgencias', 'Seguridad']
        ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        vista = cleaned_data.get('vista_inicio')
        needs_permission = {
            'AGENDA': 'puede_atender_citas',
            'CITAS': 'puede_agendar_citas',
            'PACIENTES': 'puede_registrar_pacientes',
            'INVENTARIO': 'puede_ver_inventario',
            'URGENCIAS': 'puede_ver_urgencias',
        }
        permission = needs_permission.get(vista)
        if permission and not cleaned_data.get(permission):
            self.add_error('vista_inicio', 'La vista de inicio requiere activar el permiso correspondiente.')
        grupos = cleaned_data.get('grupos_permiso', [])
        if (any(grupo.puede_registrar_urgencias for grupo in grupos) and
                not cleaned_data.get('puede_ver_urgencias')):
            self.add_error(
                'grupos_permiso',
                'Para registrar ingresos también se requiere acceso de consulta a la bitácora.',
            )
        if (any(grupo.puede_registrar_urgencias for grupo in grupos) and
                not Personal.objects.filter(usuario=self.usuario_objetivo).exists()):
            self.add_error(
                'grupos_permiso',
                'Vincula primero esta cuenta con un registro de Personal para dejar constancia de quién recibe al paciente.',
            )
        return cleaned_data


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'tarjeton', 'nombre', 'apellidopaterno', 'apellidomaterno',
            'fecha_nacimiento', 'sexo', 'curp', 'telefono', 'correo',
            'domicilio', 'alergias', 'antecedentes',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'domicilio': forms.Textarea(attrs={'rows': 2}),
            'alergias': forms.Textarea(attrs={'rows': 2}),
            'antecedentes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True

    def clean_tarjeton(self):
        tarjeton = self.cleaned_data.get('tarjeton')
        if tarjeton is not None:
            existentes = Paciente.objects.filter(tarjeton=tarjeton)
            if self.instance.pk:
                existentes = existentes.exclude(pk=self.instance.pk)
            if existentes.exists():
                raise forms.ValidationError('Ya existe un paciente con ese número de tarjetón.')
        return tarjeton

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError('La fecha de nacimiento no puede ser futura.')
        return fecha

    def clean_curp(self):
        curp = (self.cleaned_data.get('curp') or '').strip().upper()
        if curp:
            existentes = Paciente.objects.filter(curp=curp)
            if self.instance.pk:
                existentes = existentes.exclude(pk=self.instance.pk)
            if existentes.exists():
                raise forms.ValidationError('Ya existe un paciente registrado con esa CURP.')
        return curp or None


class PersonalForm(forms.ModelForm):
    class Meta:
        model = Personal
        fields = [
            'usuario', 'tipo_personal', 'nombre', 'apellidopaterno',
            'apellidomaterno', 'telefono', 'numempleado',
            'cedula_profesional', 'especialidad', 'correo',
        ]

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_personal')
        if tipo == Personal.DOCTOR and not cleaned_data.get('usuario'):
            self.add_error('usuario', 'Asocia una cuenta para que este personal pueda iniciar sesión y operar el módulo asignado.')
        for field, label in [('numempleado', 'número de empleado'), ('cedula_profesional', 'cédula profesional')]:
            value = cleaned_data.get(field)
            if value:
                existing = Personal.objects.filter(**{field: value})
                if self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    self.add_error(field, f'Ya existe personal registrado con ese {label}.')
        if tipo == Personal.DOCTOR and not cleaned_data.get('especialidad'):
            self.add_error('especialidad', 'Selecciona la especialidad del doctor.')
        return cleaned_data


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['paciente', 'doctor', 'fecha_cita', 'hora_inicio', 'motivo', 'estado']
        widgets = {
            'fecha_cita': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'motivo': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paciente'].queryset = Paciente.objects.order_by('nombre', 'apellidopaterno')
        self.fields['doctor'].queryset = Personal.objects.filter(
            tipo_personal=Personal.DOCTOR
        ).order_by('nombre', 'apellidopaterno')
        for field_name in ['paciente', 'doctor', 'fecha_cita', 'hora_inicio', 'motivo']:
            self.fields[field_name].required = True

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        fecha = cleaned_data.get('fecha_cita')
        hora = cleaned_data.get('hora_inicio')
        estado = cleaned_data.get('estado')
        if fecha and fecha < timezone.localdate() and (not self.instance.pk or self.instance.fecha_cita != fecha):
            self.add_error('fecha_cita', 'No se puede agendar una cita en una fecha pasada.')
        if doctor and fecha and hora and estado != Cita.ESTADO_CHOICES[2][0]:
            ocupada = Cita.objects.filter(
                doctor=doctor, fecha_cita=fecha, hora_inicio=hora,
            ).exclude(estado='CANCELADA')
            if self.instance.pk:
                ocupada = ocupada.exclude(pk=self.instance.pk)
            if ocupada.exists():
                self.add_error('hora_inicio', 'El doctor ya tiene una cita en esa fecha y hora.')
        return cleaned_data


class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = [
            'sintomas', 'diagnostico', 'notas', 'peso_kg', 'talla_cm',
            'presion_arterial', 'temperatura_c',
        ]
        widgets = {
            'sintomas': forms.Textarea(attrs={'rows': 3}),
            'diagnostico': forms.Textarea(attrs={'rows': 3}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }


class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['medicamento', 'dosis', 'frecuencia', 'duracion', 'cantidad', 'indicaciones']
        widgets = {'indicaciones': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['medicamento'].queryset = Medicamento.objects.filter(activo=True).order_by('nombre')


class EstudioForm(forms.ModelForm):
    class Meta:
        model = Estudio
        fields = ['nombre', 'indicaciones']
        widgets = {'indicaciones': forms.Textarea(attrs={'rows': 2})}


class EstudioResultadoForm(forms.ModelForm):
    class Meta:
        model = Estudio
        fields = ['resultado', 'estatus']
        widgets = {'resultado': forms.Textarea(attrs={'rows': 4})}

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('estatus') == 'REALIZADO' and not (cleaned_data.get('resultado') or '').strip():
            self.add_error('resultado', 'Captura el resultado antes de marcar el estudio como realizado.')
        return cleaned_data


class UrgenciasRecepcionForm(forms.ModelForm):
    class Meta:
        model = RecepcionUrgencias
        fields = [
            'nombre_completo', 'paciente', 'fecha_ingreso', 'medio_ingreso',
            'ambulancia_institucion', 'ambulancia_unidad', 'ambulancia_procedencia',
            'ambulancia_entrega', 'ambulancia_observaciones',
        ]
        widgets = {
            'fecha_ingreso': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'ambulancia_observaciones': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'nombre_completo': 'Nombre completo del paciente',
            'paciente': 'Paciente registrado (opcional)',
            'fecha_ingreso': 'Fecha y hora de ingreso',
            'medio_ingreso': 'Medio de ingreso',
            'ambulancia_institucion': 'Institución / servicio de ambulancia',
            'ambulancia_unidad': 'Número o identificación de unidad',
            'ambulancia_procedencia': 'Procedencia / lugar de traslado',
            'ambulancia_entrega': 'Persona que entrega al paciente',
            'ambulancia_observaciones': 'Observaciones del traslado',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_ingreso'].input_formats = ['%Y-%m-%dT%H:%M']
        if not self.is_bound and not self.instance.pk:
            self.initial.setdefault('fecha_ingreso', timezone.localtime().strftime('%Y-%m-%dT%H:%M'))
        self.fields['paciente'].queryset = Paciente.objects.order_by('nombre', 'apellidopaterno')

    def clean(self):
        cleaned_data = super().clean()
        fecha_ingreso = cleaned_data.get('fecha_ingreso')
        if fecha_ingreso and fecha_ingreso > timezone.now():
            self.add_error('fecha_ingreso', 'La fecha y hora de ingreso no pueden ser futuras.')
        if cleaned_data.get('medio_ingreso') == RecepcionUrgencias.AMBULANCIA:
            for field in ['ambulancia_institucion', 'ambulancia_unidad', 'ambulancia_procedencia']:
                if not cleaned_data.get(field):
                    self.add_error(field, 'Este dato es requerido cuando el ingreso es por ambulancia.')
        paciente = cleaned_data.get('paciente')
        nombre = cleaned_data.get('nombre_completo')
        if paciente and not nombre:
            cleaned_data['nombre_completo'] = str(paciente)
        return cleaned_data


class UrgenciasValoracionForm(forms.ModelForm):
    class Meta:
        model = RecepcionUrgencias
        fields = [
            'paciente', 'cita', 'triage', 'diagnostico_presuntivo',
            'manejo_inicial', 'pronostico_inicial', 'estado',
        ]
        widgets = {
            'diagnostico_presuntivo': forms.Textarea(attrs={'rows': 3}),
            'manejo_inicial': forms.Textarea(attrs={'rows': 3}),
            'pronostico_inicial': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'paciente': 'Vincular al expediente del paciente (opcional)',
            'cita': 'Cita relacionada (opcional)',
            'triage': 'Prioridad de atención / triage',
            'diagnostico_presuntivo': 'Diagnóstico presuntivo',
            'manejo_inicial': 'Manejo inicial',
            'pronostico_inicial': 'Pronóstico inicial',
            'estado': 'Estado de atención',
        }
        help_texts = {
            'triage': 'Seleccione la prioridad conforme al protocolo institucional.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cita'].queryset = Cita.objects.select_related('paciente', 'doctor').order_by('-fecha_cita')
        self.fields['cita'].required = False
        self.fields['paciente'].required = False
        self.fields['triage'].required = True
        self.fields['diagnostico_presuntivo'].required = True
        self.fields['manejo_inicial'].required = True
        self.fields['pronostico_inicial'].required = True

    def clean(self):
        cleaned_data = super().clean()
        paciente = cleaned_data.get('paciente')
        cita = cleaned_data.get('cita')
        if cita and paciente and cita.paciente_id != paciente.id:
            self.add_error('cita', 'La cita seleccionada no pertenece al paciente elegido.')
        if cita and not paciente:
            cleaned_data['paciente'] = cita.paciente
        if self.instance.pk and not cleaned_data.get('triage'):
            self.add_error('triage', 'El médico debe asignar una prioridad de triage.')
        return cleaned_data


RecetaFormSet = inlineformset_factory(
    Consulta, Receta, form=RecetaForm, extra=1, can_delete=False, max_num=10,
)
EstudioFormSet = inlineformset_factory(
    Consulta, Estudio, form=EstudioForm, extra=1, can_delete=False, max_num=10,
)


class MedicamentoForm(forms.ModelForm):
    existencia_inicial = forms.IntegerField(min_value=0, initial=0, label='Existencia inicial')

    class Meta:
        model = Medicamento
        fields = ['nombre', 'presentacion', 'existencia_minima', 'existencia_inicial']


class EntradaInventarioForm(forms.Form):
    medicamento = forms.ModelChoiceField(queryset=Medicamento.objects.none())
    cantidad = forms.IntegerField(min_value=1)
    nota = forms.CharField(max_length=250, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['medicamento'].queryset = Medicamento.objects.filter(activo=True).order_by('nombre')
