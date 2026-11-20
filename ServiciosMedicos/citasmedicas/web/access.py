ROLE_ALIASES = {
    'administrador': {'admin', 'administrador', 'sa'},
    'doctor': {'doctor'},
    'secretaria': {'secretaria', 'secretario'},
}

PERMISSION_FIELDS = (
    'puede_registrar_pacientes',
    'puede_ver_expedientes',
    'puede_agendar_citas',
    'puede_atender_citas',
    'puede_ver_inventario',
    'puede_ver_urgencias',
    'puede_valorar_urgencias',
)


def assigned_roles(user):
    if not user.is_authenticated:
        return set()
    return {
        name.strip().lower().replace(':', '')
        for name in user.groups.values_list('name', flat=True)
    }


def has_role(user, role):
    if not user.is_authenticated:
        return False
    if role == 'administrador' and user.is_superuser:
        return True
    return bool(assigned_roles(user).intersection(ROLE_ALIASES.get(role, {role})))


def default_permissions(user):
    admin = has_role(user, 'administrador')
    doctor = has_role(user, 'doctor')
    secretary = has_role(user, 'secretaria')
    return {
        'puede_registrar_pacientes': admin or doctor or secretary,
        'puede_ver_expedientes': admin or doctor or secretary,
        'puede_agendar_citas': admin or secretary,
        'puede_atender_citas': admin or doctor,
        'puede_ver_inventario': admin or doctor or secretary,
        'puede_ver_urgencias': admin or doctor,
        'puede_valorar_urgencias': doctor,
    }


def has_permission(user, permission):
    if not user.is_authenticated:
        return False
    if permission == 'puede_registrar_urgencias':
        return user.grupos_permiso.filter(puede_registrar_urgencias=True).exists()
    if has_role(user, 'administrador'):
        return True
    config = getattr(user, 'accesousuario', None)
    if config is not None:
        return bool(getattr(config, permission, False))
    return default_permissions(user).get(permission, False)


def landing_view(user):
    config = getattr(user, 'accesousuario', None)
    requested = config.vista_inicio if config is not None else 'AUTO'
    destinations = {
        'INICIO': ('home', None),
        'AGENDA': ('vista_doctor', 'puede_atender_citas'),
        'CITAS': ('listar_citas', 'puede_agendar_citas'),
        'PACIENTES': ('listar_pacientes', 'puede_registrar_pacientes'),
        'INVENTARIO': ('inventario', 'puede_ver_inventario'),
        'URGENCIAS': ('listar_urgencias', 'puede_ver_urgencias'),
    }
    if requested in destinations:
        name, permission = destinations[requested]
        if permission is None or has_permission(user, permission):
            return name
    if has_role(user, 'administrador'):
        return 'home'
    if has_permission(user, 'puede_atender_citas') and has_role(user, 'doctor'):
        return 'vista_doctor'
    if has_permission(user, 'puede_agendar_citas'):
        return 'listar_citas'
    if (has_permission(user, 'puede_registrar_urgencias') and
            has_permission(user, 'puede_ver_urgencias')):
        return 'listar_urgencias'
    return 'home'
