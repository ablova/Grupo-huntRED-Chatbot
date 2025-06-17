from datetime import datetime, timedelta

# Configuración general del admin
ADMIN_CONFIG = {
    'date_format': '%Y-%m-%d',
    'datetime_format': '%Y-%m-%d %H:%M:%S',
    'items_per_page': 50,
    'max_items_per_page': 100,
}

def get_date_ranges():
    """
    Retorna rangos de fechas comunes para filtros en el admin
    """
    today = datetime.now()
    return {
        'today': today.date(),
        'yesterday': (today - timedelta(days=1)).date(),
        'last_7_days': (today - timedelta(days=7)).date(),
        'last_30_days': (today - timedelta(days=30)).date(),
        'this_month': today.replace(day=1).date(),
        'last_month': (today.replace(day=1) - timedelta(days=1)).replace(day=1).date(),
    } 