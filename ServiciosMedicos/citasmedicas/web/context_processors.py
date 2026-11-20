from .access import has_permission, has_role


def role_flags(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'is_administrator': False,
            'can_manage_patients': False,
            'can_schedule_appointments': False,
            'is_doctor': False,
            'is_secretary': False,
            'can_view_urgencias': False,
            'can_register_urgencias': False,
            'can_triage_urgencias': False,
        }

    administrator = has_role(user, 'administrador')
    doctor = has_role(user, 'doctor')
    secretary = has_role(user, 'secretaria')
    return {
        'is_administrator': administrator,
        'can_manage_patients': has_permission(user, 'puede_registrar_pacientes'),
        'can_schedule_appointments': has_permission(user, 'puede_agendar_citas'),
        'can_attend_appointments': has_permission(user, 'puede_atender_citas'),
        'can_view_inventory': has_permission(user, 'puede_ver_inventario'),
        'can_view_urgencias': has_permission(user, 'puede_ver_urgencias'),
        'can_register_urgencias': has_permission(user, 'puede_registrar_urgencias'),
        'can_triage_urgencias': has_permission(user, 'puede_valorar_urgencias'),
        'is_doctor': doctor,
        'is_secretary': secretary,
    }
