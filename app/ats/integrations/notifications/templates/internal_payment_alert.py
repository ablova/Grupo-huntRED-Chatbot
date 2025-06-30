TITULO = "Alerta interna de pago"

MENSAJE = (
    "Alerta para el equipo interno:\n\n"
    "Cliente: {client[name]}\n"
    "Monto: ${alert[amount]:,.2f}\n"
    "Fecha límite: {alert[due_date]}\n"
    "Tipo de alerta: {alert[type]}\n"
    "Por favor, dar seguimiento inmediato.\n"
) 