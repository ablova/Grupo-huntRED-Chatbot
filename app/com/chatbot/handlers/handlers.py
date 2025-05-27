async def handle_evaluations(self, platform: str, user_id: str, business_unit: str) -> bool:
    """Maneja la selección del menú de evaluaciones."""
    try:
        # Enviar menú de evaluaciones
        return await self.services.send_evaluations_menu(platform, user_id, business_unit)
    except Exception as e:
        logger.error(f"Error manejando menú de evaluaciones: {str(e)}")
        return False

async def handle_personality_test(self, platform: str, user_id: str, business_unit: str) -> bool:
    """Maneja la prueba de personalidad."""
    try:
        # Obtener usuario
        user = await Person.objects.filter(phone=user_id).first()
        if not user:
            return False

        # Verificar si ya completó la prueba
        if "prueba_personalidad" in (user.completed_evaluations or []):
            return await self.services.send_message(
                platform, 
                user_id, 
                "Ya has completado la prueba de personalidad. ¿Deseas realizarla nuevamente?"
            )

        # Iniciar prueba
        message = "🧠 *Prueba de Personalidad*\n\n"
        message += "Esta prueba te ayudará a descubrir tu perfil profesional.\n"
        message += "Se compone de 20 preguntas que debes responder con sinceridad.\n\n"
        message += "¿Estás listo para comenzar?"

        return await self.services.send_smart_options(
            platform,
            user_id,
            message,
            [
                {"title": "✅ Comenzar", "payload": "iniciar_prueba_personalidad"},
                {"title": "❌ Más tarde", "payload": "evaluaciones"}
            ]
        )
    except Exception as e:
        logger.error(f"Error manejando prueba de personalidad: {str(e)}")
        return False

async def handle_talent_analysis(self, platform: str, user_id: str, business_unit: str) -> bool:
    """Maneja el análisis de talento 360°."""
    try:
        # Solo disponible para huntRED
        if business_unit != "huntred":
            return await self.services.send_message(
                platform,
                user_id,
                "Esta evaluación solo está disponible para usuarios de huntRED®."
            )

        # Obtener usuario
        user = await Person.objects.filter(phone=user_id).first()
        if not user:
            return False

        # Verificar si ya completó la evaluación
        if "analisis_talento" in (user.completed_evaluations or []):
            return await self.services.send_message(
                platform,
                user_id,
                "Ya has completado el análisis de talento 360°. ¿Deseas realizarlo nuevamente?"
            )

        # Iniciar evaluación
        message = "🔄 *Análisis de Talento 360°*\n\n"
        message += "Esta evaluación integral te ayudará a identificar tus fortalezas y áreas de mejora.\n"
        message += "Se compone de 30 preguntas que evaluarán diferentes aspectos de tu perfil profesional.\n\n"
        message += "¿Estás listo para comenzar?"

        return await self.services.send_smart_options(
            platform,
            user_id,
            message,
            [
                {"title": "✅ Comenzar", "payload": "iniciar_analisis_talento"},
                {"title": "❌ Más tarde", "payload": "evaluaciones"}
            ]
        )
    except Exception as e:
        logger.error(f"Error manejando análisis de talento: {str(e)}")
        return False

async def handle_cultural_analysis(self, platform: str, user_id: str, business_unit: str) -> bool:
    """Maneja el análisis de compatibilidad cultural."""
    try:
        # Solo disponible para huntRED
        if business_unit != "huntred":
            return await self.services.send_message(
                platform,
                user_id,
                "Esta evaluación solo está disponible para usuarios de huntRED®."
            )

        # Obtener usuario
        user = await Person.objects.filter(phone=user_id).first()
        if not user:
            return False

        # Verificar si ya completó la evaluación
        if "analisis_cultural" in (user.completed_evaluations or []):
            return await self.services.send_message(
                platform,
                user_id,
                "Ya has completado el análisis de compatibilidad cultural. ¿Deseas realizarlo nuevamente?"
            )

        # Iniciar evaluación
        message = "🧩 *Análisis de Compatibilidad Cultural*\n\n"
        message += "Esta evaluación te ayudará a identificar el tipo de cultura empresarial que mejor se adapta a ti.\n"
        message += "Se compone de 15 preguntas sobre tus preferencias y valores en el entorno laboral.\n\n"
        message += "¿Estás listo para comenzar?"

        return await self.services.send_smart_options(
            platform,
            user_id,
            message,
            [
                {"title": "✅ Comenzar", "payload": "iniciar_analisis_cultural"},
                {"title": "❌ Más tarde", "payload": "evaluaciones"}
            ]
        )
    except Exception as e:
        logger.error(f"Error manejando análisis cultural: {str(e)}")
        return False

async def handle_mobility_analysis(self, platform: str, user_id: str, business_unit: str) -> bool:
    """Maneja el análisis de movilidad."""
    try:
        # Solo disponible para amigro
        if business_unit != "amigro":
            return await self.services.send_message(
                platform,
                user_id,
                "Esta evaluación solo está disponible para usuarios de amigro."
            )

        # Obtener usuario
        user = await Person.objects.filter(phone=user_id).first()
        if not user:
            return False

        # Verificar si ya completó la evaluación
        if "analisis_movilidad" in (user.completed_evaluations or []):
            return await self.services.send_message(
                platform,
                user_id,
                "Ya has completado el análisis de movilidad. ¿Deseas realizarlo nuevamente?"
            )

        # Iniciar evaluación
        message = "🌍 *Análisis de Movilidad*\n\n"
        message += "Esta evaluación te ayudará a identificar tu disposición y preferencias para la movilidad laboral.\n"
        message += "Se compone de 10 preguntas sobre tu experiencia y disposición a la movilidad.\n\n"
        message += "¿Estás listo para comenzar?"

        return await self.services.send_smart_options(
            platform,
            user_id,
            message,
            [
                {"title": "✅ Comenzar", "payload": "iniciar_analisis_movilidad"},
                {"title": "❌ Más tarde", "payload": "evaluaciones"}
            ]
        )
    except Exception as e:
        logger.error(f"Error manejando análisis de movilidad: {str(e)}")
        return False

async def handle_skills_analysis(self, platform: str, user_id: str, business_unit: str) -> bool:
    """Maneja el análisis de habilidades."""
    try:
        # Solo disponible para huntu
        if business_unit != "huntu":
            return await self.services.send_message(
                platform,
                user_id,
                "Esta evaluación solo está disponible para usuarios de huntu."
            )

        # Obtener usuario
        user = await Person.objects.filter(phone=user_id).first()
        if not user:
            return False

        # Verificar si ya completó la evaluación
        if "analisis_habilidades" in (user.completed_evaluations or []):
            return await self.services.send_message(
                platform,
                user_id,
                "Ya has completado el análisis de habilidades. ¿Deseas realizarlo nuevamente?"
            )

        # Iniciar evaluación
        message = "🎓 *Análisis de Habilidades*\n\n"
        message += "Esta evaluación te ayudará a identificar tus competencias y áreas de expertise.\n"
        message += "Se compone de 25 preguntas sobre tus habilidades técnicas y blandas.\n\n"
        message += "¿Estás listo para comenzar?"

        return await self.services.send_smart_options(
            platform,
            user_id,
            message,
            [
                {"title": "✅ Comenzar", "payload": "iniciar_analisis_habilidades"},
                {"title": "❌ Más tarde", "payload": "evaluaciones"}
            ]
        )
    except Exception as e:
        logger.error(f"Error manejando análisis de habilidades: {str(e)}")
        return False

async def handle_generational_analysis(self, platform: str, user_id: str, business_unit: str) -> bool:
    """Maneja el análisis generacional."""
    try:
        # Obtener usuario
        user = await Person.objects.filter(phone=user_id).first()
        if not user:
            return False

        # Verificar si ya completó la evaluación
        if "analisis_generacional" in (user.completed_evaluations or []):
            return await self.services.send_message(
                platform,
                user_id,
                "Ya has completado el análisis generacional. ¿Deseas realizarlo nuevamente?"
            )

        # Iniciar evaluación
        message = "👥 *Análisis Generacional*\n\n"
        message += "Esta evaluación te ayudará a entender tu perfil generacional y sus características.\n"
        message += "Se compone de 10 preguntas sobre tus preferencias y comportamientos.\n\n"
        message += "¿Estás listo para comenzar?"

        return await self.services.send_smart_options(
            platform,
            user_id,
            message,
            [
                {"title": "✅ Comenzar", "payload": "iniciar_analisis_generacional"},
                {"title": "❌ Más tarde", "payload": "evaluaciones"}
            ]
        )
    except Exception as e:
        logger.error(f"Error manejando análisis generacional: {str(e)}")
        return False

async def handle_motivational_analysis(self, platform: str, user_id: str, business_unit: str) -> bool:
    """Maneja el análisis motivacional."""
    try:
        # Obtener usuario
        user = await Person.objects.filter(phone=user_id).first()
        if not user:
            return False

        # Verificar si ya completó la evaluación
        if "analisis_motivacional" in (user.completed_evaluations or []):
            return await self.services.send_message(
                platform,
                user_id,
                "Ya has completado el análisis motivacional. ¿Deseas realizarlo nuevamente?"
            )

        # Iniciar evaluación
        message = "💪 *Análisis Motivacional*\n\n"
        message += "Esta evaluación te ayudará a descubrir tus principales motivadores.\n"
        message += "Se compone de 15 preguntas sobre tus preferencias y comportamientos.\n\n"
        message += "¿Estás listo para comenzar?"

        return await self.services.send_smart_options(
            platform,
            user_id,
            message,
            [
                {"title": "✅ Comenzar", "payload": "iniciar_analisis_motivacional"},
                {"title": "❌ Más tarde", "payload": "evaluaciones"}
            ]
        )
    except Exception as e:
        logger.error(f"Error manejando análisis motivacional: {str(e)}")
        return False

async def handle_work_style_analysis(self, platform: str, user_id: str, business_unit: str) -> bool:
    """Maneja el análisis de estilos de trabajo."""
    try:
        # Obtener usuario
        user = await Person.objects.filter(phone=user_id).first()
        if not user:
            return False

        # Verificar si ya completó la evaluación
        if "analisis_estilos" in (user.completed_evaluations or []):
            return await self.services.send_message(
                platform,
                user_id,
                "Ya has completado el análisis de estilos de trabajo. ¿Deseas realizarlo nuevamente?"
            )

        # Iniciar evaluación
        message = "🎯 *Análisis de Estilos de Trabajo*\n\n"
        message += "Esta evaluación te ayudará a identificar tu estilo de trabajo preferido.\n"
        message += "Se compone de 12 preguntas sobre tus preferencias en el entorno laboral.\n\n"
        message += "¿Estás listo para comenzar?"

        return await self.services.send_smart_options(
            platform,
            user_id,
            message,
            [
                {"title": "✅ Comenzar", "payload": "iniciar_analisis_estilos"},
                {"title": "❌ Más tarde", "payload": "evaluaciones"}
            ]
        )
    except Exception as e:
        logger.error(f"Error manejando análisis de estilos: {str(e)}")
        return False 