TITULO = "Alerta de pago"

MENSAJE = (
    "Hola {client[name]},\n\n"
    "Te recordamos que tienes un pago pendiente de ${alert[amount]:,.2f} con fecha límite {alert[due_date]}.\n"
    "Tipo de alerta: {alert[type]}\n\n"
    "Por favor, realiza tu pago a la brevedad para evitar interrupciones en el servicio.\n"
    "Si ya realizaste el pago, ignora este mensaje.\n"
) 