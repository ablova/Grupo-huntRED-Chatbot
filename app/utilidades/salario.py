# /home/pablo/app/utilidades/salario.py
# Paquetes de importación
import requests  # Para obtener tipos de cambio desde una API externa


# Diccionarios de datos estáticos (actualizar periódicamente con fuentes confiables)
DATOS_PPA = {
    "México": 0.48, "USA": 1.0, "Nicaragua": 0.35, "Colombia": 0.45, "Argentina": 0.52, "Brasil": 0.60
}

DATOS_COLI = {
    "Ciudad de México": 50.2, "Nueva York": 100.0, "Managua": 40.0, 
    "Bogotá": 45.0, "Buenos Aires": 45.0, "São Paulo": 48.5
}

DATOS_BIGMAC = {
    "México": 4.5, "USA": 5.7, "Nicaragua": 3.0, "Colombia": 3.5, "Argentina": 3.8, "Brasil": 4.2
}
DIVISA_BASE = {
    "MXN": 20, "USD": 1.0, "Nicaragua": 36.82
}

# Constantes y tablas aplicables para 2025
UMA_DIARIA_2025 = 108.00  # Unidad de Medida y Actualización diaria
ISR_BRACKETS_2025 = [     # Tabla de ISR mensual (limite inferior, limite superior, cuota fija, tasa)
    (0.01, 7735.00, 0.00, 0.0192),
    (7735.01, 65651.07, 148.51, 0.0640),
    (65651.08, 115375.90, 3844.02, 0.1088),
    (115375.91, 134119.41, 9264.16, 0.16),
    (134119.42, 160577.65, 12264.16, 0.1792),
    (160577.66, 323862.00, 17005.47, 0.2136),
    (323862.01, 510451.00, 51883.01, 0.2352),
    (510451.01, 974535.03, 95768.74, 0.30),
    (974535.04, 1291380.04, 234993.95, 0.32),
    (1291380.05, float('inf'), 338944.34, 0.35)
]

SUBSIDIO_EMPLEO_MAX = 475.00      # Subsidio al empleo máximo
SUBSIDIO_EMPLEO_LIMITE = 10171.00 # Límite para aplicar subsidio

# Funciones para obtener datos externos
def obtener_tipo_cambio(moneda_origen):
    if moneda_origen == 'MXN':
        return 1.0
    try:
        api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(api_url)
        response.raise_for_status()  # Levanta excepción si hay error HTTP
        rates = response.json()['rates']
        usd_to_mxn = rates.get('MXN', 20.3)  # Default a 20.31 si falla
        usd_to_origen = rates.get(moneda_origen, 1.0)  # Default a 1.0 si no está la moneda
        if usd_to_origen == 0:  # Evitar división por cero
            raise ValueError(f"Tasa inválida para {moneda_origen}")
        return usd_to_mxn / usd_to_origen  # Tipo de cambio moneda_origen -> MXN
    except Exception as e:
        print(f"Advertencia: Fallo al obtener tipo de cambio para {moneda_origen} -> MXN ({str(e)}). Usando valor por defecto.")
        return 20.3 if moneda_origen == 'USD' else 1.0  # Default para USD, 1.0 para MXN u otras


# Funciones de cálculo
def calcular_isr_mensual(base_gravable: float) -> float:
    """
    Calcula el ISR mensual antes de subsidio para un ingreso gravable dado.
    
    Args:
        base_gravable (float): Ingreso gravable mensual.
    
    Returns:
        float: ISR calculado.
    """
    impuesto = 0.0
    for lim_inf, lim_sup, cuota_fija, tasa in ISR_BRACKETS_2025:
        if base_gravable >= lim_inf and base_gravable <= lim_sup:
            excedente = base_gravable - lim_inf
            impuesto = cuota_fija + excedente * tasa
            break
    return impuesto

def calcular_cuotas_imss(salario_bruto: float) -> float:
    """
    Calcula aproximadamente las cuotas obrero (trabajador) del IMSS a retener.
    
    Args:
        salario_bruto (float): Salario bruto mensual.
    
    Returns:
        float: Cuotas del IMSS a descontar.
    """
    cuota_obrero = salario_bruto * 0.027  # Aproximación simple
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
    Calcula el salario neto a partir del salario bruto, considerando todos los elementos posibles.
    
    Args:
        salario_bruto (float): Salario bruto mensual.
        tipo_trabajador (str): Tipo de trabajador (default: 'asalariado').
        incluye_prestaciones (bool): Si incluye vales u otras prestaciones (default: False).
        monto_vales (float): Monto de vales exentos (default: 0.0).
        fondo_ahorro (bool): Si incluye fondo de ahorro (default: False).
        porcentaje_fondo (float): Porcentaje del fondo de ahorro (default: 0.13).
        credito_infonavit (float): Monto o porcentaje del crédito Infonavit (default: 0.0).
        pension_alimenticia (float): Monto o porcentaje de pensión alimenticia (default: 0.0).
        aplicar_subsidio (bool): Si aplica subsidio al empleo (default: True).
        moneda (str): Moneda del salario (default: 'MXN').
        tipo_cambio (float): Tipo de cambio a MXN (default: 1.0).
    
    Returns:
        float: Salario neto calculado en MXN o en la moneda especificada.
    """
    bruto = salario_bruto
    base_gravable = bruto

    # Exención de vales si aplica
    if incluye_prestaciones and monto_vales > 0:
        base_gravable -= monto_vales

    # Cálculo de impuestos y retenciones
    isr = calcular_isr_mensual(base_gravable)
    imss = calcular_cuotas_imss(bruto)

    # Descuento por Infonavit
    infonavit_descuento = 0.0
    if credito_infonavit:
        if 0 < credito_infonavit < 1:  # Si es porcentaje
            infonavit_descuento = bruto * credito_infonavit
        else:  # Si es monto fijo
            infonavit_descuento = credito_infonavit

    # Descuento por pensión alimenticia
    pension_desc = 0.0
    if pension_alimenticia:
        if 0 < pension_alimenticia <= 1:  # Si es porcentaje
            pension_desc = bruto * pension_alimenticia
        else:  # Si es monto fijo
            pension_desc = pension_alimenticia

    # Descuento por fondo de ahorro
    ahorro_desc = 0.0
    if fondo_ahorro:
        ahorro_desc = porcentaje_fondo * bruto

    # Salario neto en MXN
    salario_neto_mxn = bruto - isr - imss - infonavit_descuento - pension_desc - ahorro_desc

    # Conversión a otra moneda si aplica
    if moneda != 'MXN':
        salario_neto_mxn /= tipo_cambio

    return salario_neto_mxn

def calcular_bruto(
    salario_neto: float,
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
    Calcula el salario bruto requerido para obtener un salario neto deseado usando búsqueda iterativa.
    
    Args:
        salario_neto (float): Salario neto deseado.
        (Otros parámetros son idénticos a calcular_neto)
    
    Returns:
        float: Salario bruto necesario.
    """
    objetivo = salario_neto
    bruto_min = salario_neto
    bruto_max = salario_neto * 2
    bruto_calculado = None

    # Búsqueda binaria para encontrar el bruto
    for _ in range(50):
        guess = (bruto_min + bruto_max) / 2.0
        neto_calculado = calcular_neto(
            guess,
            tipo_trabajador=tipo_trabajador,
            incluye_prestaciones=incluye_prestaciones,
            monto_vales=monto_vales,
            fondo_ahorro=fondo_ahorro,
            porcentaje_fondo=porcentaje_fondo,
            credito_infonavit=credito_infonavit,
            pension_alimenticia=pension_alimenticia,
            aplicar_subsidio=aplicar_subsidio,
            moneda=moneda,
            tipo_cambio=tipo_cambio
        )
        diferencia = neto_calculado - objetivo
        if abs(diferencia) < 1.0:  # Tolerancia de 1 peso
            bruto_calculado = guess
            break
        elif diferencia < 0:
            bruto_min = guess
        else:
            bruto_max = guess

    return bruto_calculado if bruto_calculado is not None else guess

def calcular_neto_equivalente(neto_origen: float, moneda_origen: str, modelo: str, datos_modelo: dict, tipo_cambio: float) -> float:
    """
    Calcula el salario neto equivalente en MXN ajustado por poder adquisitivo según el modelo seleccionado.
    
    Args:
        neto_origen (float): Salario neto en la moneda de origen.
        moneda_origen (str): Moneda del salario original (ej. 'USD').
        modelo (str): Modelo de ajuste ('PPA', 'COLI', 'BigMac').
        datos_modelo (dict): Datos necesarios según el modelo (ppa, coli_origen, etc.).
        tipo_cambio (float): Tipo de cambio a MXN.
    
    Returns:
        float: Salario neto equivalente en MXN.
    
    Raises:
        ValueError: Si el modelo no es reconocido.
    """
    if modelo == 'PPA':
        ppa = datos_modelo['ppa']
        return neto_origen * ppa
    elif modelo == 'COLI':
        coli_origen = datos_modelo['coli_origen']
        coli_destino = datos_modelo['coli_destino']
        neto_mxn = neto_origen * tipo_cambio
        return neto_mxn * (coli_destino / coli_origen)
    elif modelo == 'BigMac':
        precio_bigmac_origen = datos_modelo['precio_bigmac_origen']
        precio_bigmac_destino = datos_modelo['precio_bigmac_destino']
        neto_mxn = neto_origen * tipo_cambio
        return neto_mxn * (precio_bigmac_destino / (precio_bigmac_origen * tipo_cambio))
    else:
        raise ValueError("Modelo no reconocido")
