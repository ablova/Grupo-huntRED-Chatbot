PAYROLL_MENU = [
    {"title": "📈 Mis Reportes",   "payload": "mis_reportes",    "type": "action"},
    {"title": "👥 Reportes Equipo","payload": "reportes_equipo", "type": "action",
     "required_permissions": ["view_team_reports"]},
    {"title": "📧 Reporte RH",     "payload": "enviar_reporte_rh","type": "action",
     "required_permissions": ["rh_admin"]},