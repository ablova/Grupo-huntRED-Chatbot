from app.payroll.models.permiso_especial import PermisoEspecial
from app.payroll.models import PayrollEmployee
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

class PermisoEspecialService:
    """
    Servicio para gestionar permisos especiales, workflow y notificaciones
    """
    def solicitar_permiso(self, empleado: PayrollEmployee, tipo: str, motivo: str, fecha_inicio, fecha_fin=None):
        permiso = PermisoEspecial.objects.create(
            empleado=empleado,
            tipo=tipo,
            motivo=motivo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        self.notificar_supervisor(permiso)
        return permiso

    def aprobar_permiso(self, permiso: PermisoEspecial, usuario, respuesta: str = ""):
        permiso.estado = 'aprobado'
        permiso.supervisor = usuario
        permiso.respuesta_supervisor = respuesta
        permiso.fecha_respuesta = timezone.now()
        permiso.save()
        self.notificar_rh(permiso)
        return permiso

    def rechazar_permiso(self, permiso: PermisoEspecial, usuario, respuesta: str = ""):
        permiso.estado = 'rechazado'
        permiso.supervisor = usuario
        permiso.respuesta_supervisor = respuesta
        permiso.fecha_respuesta = timezone.now()
        permiso.save()
        self.notificar_empleado(permiso)
        return permiso

    def finalizar_permiso(self, permiso: PermisoEspecial, usuario, reconocimiento: str = ""):
        permiso.estado = 'finalizado'
        permiso.rh = usuario
        permiso.reconocimiento = reconocimiento
        permiso.save()
        self.notificar_empleado(permiso, reconocimiento=True)
        return permiso

    def notificar_supervisor(self, permiso: PermisoEspecial):
        # Notificar al supervisor (correo o WhatsApp)
        pass
    def notificar_rh(self, permiso: PermisoEspecial):
        # Notificar a RH
        pass
    def notificar_empleado(self, permiso: PermisoEspecial, reconocimiento=False):
        # Notificar al empleado
        pass 