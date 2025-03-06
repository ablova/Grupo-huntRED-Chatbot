# /home/app/utilidades/salario.py

import requests

# Constantes y tablas aplicables para 2025
UMA_DIARIA_2025 = 108.00  # Valor diario de la UMA en 2025 (aprox.).
ISR_BRACKETS_2025 = [
    (0.01, 7735.00, 0.00, 0.0192),  # Hasta $7,735.00 -> 1.92%
    (7735.01, 65651.07, 148.51, 0.0640),  # >$7,735 hasta $65,651 -> 6.40%
    (65651.08, 115375.90, 3844.02, 0.1088),  # >$65,651 hasta $115,375 -> 10.88%
    (115375.91, 134119.41, 9264.16, 0.16),   # ... (tramos intermedios) 16%
    (134119.42, 160577.65, 12264.16, 0.1792), # 17.92%
    (160577.66, 323862.00, 17005.47, 0.2136), # 21.36%
    (323862.01, 510451.00, 51883.01, 0.2352), # 23.52%
    (510451.01, 974535.03, 95768.74, 0.30),   # 30.00%
    (974535.04, 1291380.04, 234993.95, 0.32), # 32.00%
    (1291380.05, float('inf'), 338944.34, 0.35) # >$1,291,380 -> 35.00%
]

SUBSIDIO_EMPLEO_MAX = 475.00    # Monto max de subsidio al empleo mensual en 2025
SUBSIDIO_EMPLEO_LIMITE = 10171.00  # Ingreso mensual máximo para recibir subsidio

# Obtener tipo de cambio actualizado de MXN a la moneda deseada (USD, EUR, BRL, COP, etc.)
def obtener_tipo_cambio(moneda_destino="USD"):
    """
    Obtiene el tipo de cambio actualizado desde MXN a la moneda de destino.
    Utiliza un servicio como ExchangeRate-API o cualquier otra fuente confiable.
    """
    # Usamos un servicio como ExchangeRate-API para obtener la tasa de cambio
    api_url = f"https://api.exchangerate-api.com/v4/latest/MXN"  # Aquí usamos MXN como base
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        # Devuelve la tasa de la moneda de destino
        return data['rates'].get(moneda_destino, 1.0)  # Si no encuentra, devuelve 1.0
    else:
        raise ValueError("No se pudo obtener el tipo de cambio.")
    
def calcular_isr_mensual(base_gravable: float) -> float:
    """
    Calcula el ISR mensual antes de subsidio para un ingreso gravable dado (base gravable en MXN).
    Se usa la tabla ISR_BRACKETS_2025 definida.
    """
    impuesto = 0.0
    for lim_inf, lim_sup, cuota_fija, tasa in ISR_BRACKETS_2025:
        if base_gravable >= lim_inf and base_gravable <= lim_sup:
            # Encontró el rango donde cae la base gravable
            excedente = base_gravable - lim_inf
            impuesto = cuota_fija + excedente * tasa
            break
    return impuesto

def calcular_cuotas_imss(salario_bruto: float) -> float:
    """
    Calcula aproximadamente las cuotas obrero (trabajador) del IMSS a retener.
    Usa porcentajes aproximados para 2025 sobre el salario bruto.
    """
    cuota_obrero = salario_bruto * 0.027
    return cuota_obrero

def calcular_neto(
    salario_bruto: float,
    tipo_trabajador: str = 'asalariado',
    incluye_prestaciones: bool = False,
    monto_vales: float = 0.0,
    fondo_ahorro: bool = False,
    porcentaje_fondo: float = 0.13,
    credito_infonavit: float = 0.0,
    pension_alimenticia: float = 0.0,
    aplicar_subsidio: bool = True,
    moneda: str = 'MXN',
    tipo_cambio: float = 1.0
) -> float:
    """
    Calcula el salario neto a partir del salario bruto, considerando todos los elementos posibles
    como bonos, prestaciones y deducciones.
    """
    bruto = salario_bruto
    base_gravable = bruto

    # Restar vales si se consideran
    if incluye_prestaciones and monto_vales > 0:
        base_gravable -= monto_vales

    # Calcular ISR, IMSS y otras deducciones
    isr = calcular_isr_mensual(base_gravable)
    imss = calcular_cuotas_imss(bruto)

    # Descuentos adicionales como INFONAVIT, pensión alimenticia y fondo de ahorro
    infonavit_descuento = 0.0
    if credito_infonavit:
        if 0 < credito_infonavit < 1:
            infonavit_descuento = bruto * credito_infonavit
        else:
            infonavit_descuento = credito_infonavit

    pension_desc = 0.0
    if pension_alimenticia:
        if 0 < pension_alimenticia <= 1:
            pension_desc = bruto * pension_alimenticia
        else:
            pension_desc = pension_alimenticia

    ahorro_desc = 0.0
    if fondo_ahorro:
        ahorro_desc = porcentaje_fondo * bruto

    # Calcular salario neto en MXN
    salario_neto_mxn = bruto - isr - imss - infonavit_descuento - pension_desc - ahorro_desc

    # Si la moneda no es MXN, convertimos usando el tipo de cambio
    if moneda != 'MXN':
        salario_neto_mxn /= tipo_cambio

    return salario_neto_mxn