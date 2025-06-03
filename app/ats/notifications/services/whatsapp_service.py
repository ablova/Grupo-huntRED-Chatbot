def send_portal_access_notification(self, phone, name, email):
    """
    Envía una notificación por WhatsApp sobre el acceso al portal.
    """
    template = """
    ¡Bienvenido al Portal huntRED®!

    Hola {name},

    Tu acceso al Portal del Cliente huntRED® ha sido creado exitosamente.

    📧 Correo: {email}
    🔑 Se ha enviado una contraseña temporal a tu correo

    En el portal podrás:
    ✅ Ver el estado de tus contrataciones
    📊 Acceder a métricas y benchmarks
    📄 Gestionar documentos
    💡 Recibir insights personalizados

    Si tienes alguna duda, no dudes en contactarnos.

    Saludos,
    El equipo de huntRED®
    """
    
    message = template.format(
        name=name,
        email=email
    )
    
    return self.send_message(phone, message) 