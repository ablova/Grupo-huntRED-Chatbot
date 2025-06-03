"""
Opciones de menú por unidad de negocio
"""

# Menús dinámicos por unidad de negocio con submenús
MENU_OPTIONS_BY_BU = {
    "amigro": [
        {
            "title": "👤 Mi Perfil",
            "payload": "mi_perfil",
            "description": "Crea y gestiona tu perfil profesional.",
            "submenu": [
                {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                {"title": "👀 Ver Perfil", "payload": "ver_perfil"},
                {"title": "✏️ Editar Perfil", "payload": "editar_perfil"},
                {"title": "📊 Ver Evaluaciones", "payload": "ver_evaluaciones"}
            ]
        },
        {
            "title": "🎯 Evaluaciones",
            "payload": "evaluaciones",
            "description": "Completa evaluaciones para mejorar tu perfil.",
            "submenu": [
                {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad"},
                {"title": "🌍 Análisis de Movilidad", "payload": "analisis_movilidad"},
                {"title": "👥 Análisis Generacional", "payload": "analisis_generacional"},
                {"title": "💪 Análisis Motivacional", "payload": "analisis_motivacional"},
                {"title": "🎯 Análisis de Estilos", "payload": "analisis_estilos"}
            ]
        },
        {
            "title": "💰 Calcular Salario",
            "payload": "calcular_salario",
            "description": "Calcula salario neto o bruto.",
            "submenu": [
                {"title": "💵 Neto a Bruto", "payload": "neto_a_bruto"},
                {"title": "💵 Bruto a Neto", "payload": "bruto_a_neto"}
            ]
        },
        {
            "title": "📄 Cargar CV",
            "payload": "cargar_cv",
            "description": "Sube tu currículum.",
            "submenu": [
                {"title": "📤 Subir Nuevo CV", "payload": "subir_cv"},
                {"title": "📋 Ver CV Actual", "payload": "ver_cv"},
                {"title": "✏️ Editar CV", "payload": "editar_cv"}
            ]
        },
        {
            "title": "🔍 Ver Vacantes",
            "payload": "ver_vacantes",
            "description": "Explora oportunidades laborales disponibles.",
            "submenu": [
                {"title": "🔎 Buscar Vacantes", "payload": "buscar_vacantes"},
                {"title": "⭐ Vacantes Recomendadas", "payload": "vacantes_recomendadas"},
                {"title": "📊 Mis Postulaciones", "payload": "mis_postulaciones"}
            ]
        },
        {
            "title": "📊 Consultar Estatus",
            "payload": "consultar_estatus",
            "description": "Revisa el estado de tus aplicaciones.",
            "submenu": [
                {"title": "📈 Estado de Postulaciones", "payload": "estado_postulaciones"},
                {"title": "📅 Próximas Entrevistas", "payload": "proximas_entrevistas"},
                {"title": "📝 Historial de Aplicaciones", "payload": "historial_aplicaciones"}
            ]
        },
        {
            "title": "📞 Contacto",
            "payload": "contacto",
            "description": "Habla con un asesor.",
            "submenu": [
                {"title": "💬 Chat con Asesor", "payload": "chat_asesor"},
                {"title": "📧 Enviar Mensaje", "payload": "enviar_mensaje"},
                {"title": "📞 Llamar Asesor", "payload": "llamar_asesor"}
            ]
        },
        {
            "title": "❓ Ayuda",
            "payload": "ayuda",
            "description": "Resuelve dudas generales.",
            "submenu": [
                {"title": "❔ Preguntas Frecuentes", "payload": "faq"},
                {"title": "📚 Guías de Uso", "payload": "guias"},
                {"title": "📝 Tutoriales", "payload": "tutoriales"}
            ]
        }
    ],
    "huntred": [
        {
            "title": "👤 Mi Perfil",
            "payload": "mi_perfil",
            "description": "Crea y gestiona tu perfil profesional.",
            "submenu": [
                {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                {"title": "👀 Ver Perfil", "payload": "ver_perfil"},
                {"title": "✏️ Editar Perfil", "payload": "editar_perfil"},
                {"title": "📊 Ver Evaluaciones", "payload": "ver_evaluaciones"}
            ]
        },
        {
            "title": "🎯 Evaluaciones",
            "payload": "evaluaciones",
            "description": "Completa evaluaciones para mejorar tu perfil.",
            "submenu": [
                {
                    "title": "🧬 ADN Profesional",
                    "payload": "adn_profesional",
                    "description": "Evaluación integral de tu perfil profesional",
                    "submenu": [
                        {"title": "👥 Liderazgo", "payload": "analisis_liderazgo"},
                        {"title": "💡 Innovación", "payload": "analisis_innovacion"},
                        {"title": "🗣️ Comunicación", "payload": "analisis_comunicacion"},
                        {"title": "🔄 Resiliencia", "payload": "analisis_resiliencia"},
                        {"title": "📈 Resultados", "payload": "analisis_resultados"},
                        {"title": "📊 Reporte Completo", "payload": "reporte_adn_profesional"}
                    ]
                },
                {
                    "title": "🧠 Personalidad",
                    "payload": "personalidad",
                    "description": "Descubre tu perfil de personalidad",
                    "submenu": [
                        {"title": "🎭 Rasgos de Personalidad", "payload": "analisis_rasgos"},
                        {"title": "🤝 Estilos de Comportamiento", "payload": "analisis_estilos"},
                        {"title": "💼 Preferencias Laborales", "payload": "analisis_preferencias"},
                        {"title": "📊 Reporte Completo", "payload": "reporte_personalidad"}
                    ]
                },
                {
                    "title": "💫 Talento",
                    "payload": "talento",
                    "description": "Evalúa tus competencias y potencial",
                    "submenu": [
                        {"title": "🔧 Habilidades Técnicas", "payload": "analisis_habilidades"},
                        {"title": "🌟 Competencias Clave", "payload": "analisis_competencias"},
                        {"title": "🌱 Potencial de Desarrollo", "payload": "analisis_potencial"},
                        {"title": "📊 Reporte Completo", "payload": "reporte_talento"}
                    ]
                },
                {
                    "title": "🌍 Cultural",
                    "payload": "cultural",
                    "description": "Analiza tu adaptación cultural",
                    "submenu": [
                        {"title": "🎯 Valores", "payload": "analisis_valores"},
                        {"title": "💼 Estilo de Trabajo", "payload": "analisis_estilo_trabajo"},
                        {"title": "🗣️ Preferencias de Comunicación", "payload": "analisis_comunicacion_cultural"},
                        {"title": "🔄 Adaptabilidad", "payload": "analisis_adaptabilidad"},
                        {"title": "📊 Reporte Completo", "payload": "reporte_cultural"}
                    ]
                },
                {
                    "title": "👥 Análisis Generacional",
                    "payload": "analisis_generacional",
                    "description": "Descubre tu perfil generacional",
                    "submenu": [
                        {"title": "📊 Perfil Generacional", "payload": "perfil_generacional"},
                        {"title": "🔄 Patrones de Comportamiento", "payload": "patrones_generacionales"},
                        {"title": "💡 Insights Generacionales", "payload": "insights_generacionales"},
                        {"title": "📈 Reporte Completo", "payload": "reporte_generacional"}
                    ]
                },
                {
                    "title": "💰 Compensación",
                    "payload": "compensacion",
                    "description": "Análisis y satisfacción salarial",
                    "submenu": [
                        {"title": "📊 Competitividad Salarial", "payload": "competitividad_salarial"},
                        {"title": "😊 Satisfacción", "payload": "satisfaccion_salarial"},
                        {"title": "📈 Proyecciones", "payload": "proyecciones_salariales"},
                        {"title": "🔍 Recomendaciones", "payload": "recomendaciones_salariales"},
                        {"title": "📑 Reporte Completo", "payload": "reporte_compensacion"}
                    ]
                }
            ]
        },
        {
            "title": "🔍 Buscar Empleo",
            "payload": "buscar_empleo",
            "description": "Encuentra trabajos específicos.",
            "submenu": [
                {"title": "🔎 Búsqueda Avanzada", "payload": "busqueda_avanzada"},
                {"title": "⭐ Recomendados", "payload": "trabajos_recomendados"},
                {"title": "📊 Mis Postulaciones", "payload": "mis_postulaciones"}
            ]
        }
    ]
}

# Menú de evaluaciones
EVALUATIONS_MENU = {
    "title": "🎯 Evaluaciones Disponibles",
    "description": "Selecciona una evaluación para comenzar",
    "options": [
        {
            "title": "🧬 ADN Profesional",
            "payload": "adn_profesional",
            "description": "Evaluación integral de tu perfil profesional"
        },
        {
            "title": "🧠 Personalidad",
            "payload": "personalidad",
            "description": "Descubre tu perfil de personalidad"
        },
        {
            "title": "💫 Talento",
            "payload": "talento",
            "description": "Evalúa tus competencias y potencial"
        },
        {
            "title": "🌍 Cultural",
            "payload": "cultural",
            "description": "Analiza tu adaptación cultural"
        },
        {
            "title": "👥 Generacional",
            "payload": "generacional",
            "description": "Descubre tu perfil generacional"
        },
        {
            "title": "💰 Compensación",
            "payload": "compensacion",
            "description": "Análisis y satisfacción salarial"
        }
    ]
} 