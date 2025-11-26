"""
Utilidades para el módulo de auditoría
"""
from api.models import AuditLog


def create_audit_log(
    user,
    action,
    model_name,
    object_id=None,
    object_repr='',
    changes=None,
    description='',
    request=None
):
    """
    Crear un registro de auditoría
    
    Args:
        user: Usuario que realizó la acción
        action: Tipo de acción (CREATE, UPDATE, DELETE, etc.)
        model_name: Nombre del modelo
        object_id: ID del objeto afectado
        object_repr: Representación del objeto
        changes: Diccionario de cambios
        description: Descripción legible
        request: Request HTTP (para obtener IP y user agent)
    """
    # Obtener IP y user agent del request
    ip_address = None
    user_agent = None
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Obtener rol del usuario
    user_role = getattr(user, 'role', 'UNKNOWN') if user else 'SYSTEM'
    username = user.username if user else 'SYSTEM'
    
    # Crear log
    AuditLog.objects.create(
        user=user,
        username=username,
        user_role=user_role,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        changes=changes,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )
