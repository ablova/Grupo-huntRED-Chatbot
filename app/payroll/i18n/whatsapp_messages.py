"""
Traducciones para mensajes de WhatsApp huntRED® Payroll
Soporte multilingüe: Español, Inglés, Francés, Portugués, Alemán, Mandarín y Árabe
"""

# Códigos ISO de idiomas soportados
SUPPORTED_LANGUAGES = {
    'es': 'Español',
    'en': 'English',
    'fr': 'Français',
    'pt': 'Português',
    'de': 'Deutsch',
    'zh': '中文',
    'ar': 'العربية'
}

# Idioma por defecto
DEFAULT_LANGUAGE = 'es'

# Diccionario de traducciones
MESSAGES = {
    # Mensajes de sistema
    'system': {
        'language_changed': {
            'es': '✅ Idioma cambiado a Español.',
            'en': '✅ Language changed to English.',
            'fr': '✅ Langue changée en Français.',
            'pt': '✅ Idioma alterado para Português.'
        },
        'unsupported_language': {
            'es': '❌ Idioma no soportado. Idiomas disponibles: Español, English, Français, Português.',
            'en': '❌ Unsupported language. Available languages: Español, English, Français, Português.',
            'fr': '❌ Langue non prise en charge. Langues disponibles: Español, English, Français, Português.',
            'pt': '❌ Idioma não suportado. Idiomas disponíveis: Español, English, Français, Português.'
        },
        'welcome': {
            'es': '👋 ¡Bienvenido/a al servicio de nómina por WhatsApp!',
            'en': '👋 Welcome to the Payroll WhatsApp service!',
            'fr': '👋 Bienvenue au service de paie par WhatsApp!',
            'pt': '👋 Bem-vindo/a ao serviço de folha de pagamento por WhatsApp!'
        },
        'user_not_found': {
            'es': '❌ No podemos identificar tu número en nuestro sistema. Por favor, contacta a RH.',
            'en': '❌ We cannot identify your number in our system. Please contact HR.',
            'fr': '❌ Nous ne pouvons pas identifier votre numéro dans notre système. Veuillez contacter RH.',
            'pt': '❌ Não podemos identificar seu número em nosso sistema. Entre em contato com RH.'
        },
        'error': {
            'es': '❌ Error procesando tu mensaje. Por favor intenta nuevamente.',
            'en': '❌ Error processing your message. Please try again.',
            'fr': '❌ Erreur lors du traitement de votre message. Veuillez réessayer.',
            'pt': '❌ Erro ao processar sua mensagem. Por favor, tente novamente.'
        }
    },
    
    # Mensajes de asistencia
    'attendance': {
        'checkin_request': {
            'es': '📍 Por favor, comparte tu ubicación para registrar tu entrada.',
            'en': '📍 Please share your location to register your check-in.',
            'fr': '📍 Veuillez partager votre emplacement pour enregistrer votre arrivée.',
            'pt': '📍 Por favor, compartilhe sua localização para registrar sua entrada.'
        },
        'checkin_success': {
            'es': '✅ ¡Entrada registrada con éxito! Hora: {time}',
            'en': '✅ Check-in successfully registered! Time: {time}',
            'fr': '✅ Entrée enregistrée avec succès! Heure: {time}',
            'pt': '✅ Entrada registrada com sucesso! Hora: {time}'
        },
        'checkout_request': {
            'es': '📍 Por favor, comparte tu ubicación para registrar tu salida.',
            'en': '📍 Please share your location to register your check-out.',
            'fr': '📍 Veuillez partager votre emplacement pour enregistrer votre départ.',
            'pt': '📍 Por favor, compartilhe sua localização para registrar sua saída.'
        },
        'checkout_success': {
            'es': '✅ ¡Salida registrada con éxito! Hora: {time}',
            'en': '✅ Check-out successfully registered! Time: {time}',
            'fr': '✅ Sortie enregistrée avec succès! Heure: {time}',
            'pt': '✅ Saída registrada com sucesso! Hora: {time}'
        },
        'already_checked_in': {
            'es': '⚠️ Ya tienes una entrada registrada hoy a las {time}.',
            'en': '⚠️ You already have a check-in registered today at {time}.',
            'fr': '⚠️ Vous avez déjà une entrée enregistrée aujourd\'hui à {time}.',
            'pt': '⚠️ Você já tem uma entrada registrada hoje às {time}.'
        },
        'no_checkin': {
            'es': '⚠️ No tienes entrada registrada hoy. No puedes registrar salida.',
            'en': '⚠️ You don\'t have a check-in registered today. You cannot check out.',
            'fr': '⚠️ Vous n\'avez pas d\'entrée enregistrée aujourd\'hui. Vous ne pouvez pas enregistrer de sortie.',
            'pt': '⚠️ Você não tem entrada registrada hoje. Não pode registrar saída.'
        },
        'invalid_location': {
            'es': '⚠️ Tu ubicación está demasiado lejos de la oficina. Se notificará a tu supervisor.',
            'en': '⚠️ Your location is too far from the office. Your supervisor will be notified.',
            'fr': '⚠️ Votre emplacement est trop éloigné du bureau. Votre superviseur sera notifié.',
            'pt': '⚠️ Sua localização está muito longe do escritório. Seu supervisor será notificado.'
        }
    },
    
    # Mensajes de nómina
    'payroll': {
        'payslip_request': {
            'es': '📄 ¿Qué recibo de nómina necesitas?',
            'en': '📄 Which payslip do you need?',
            'fr': '📄 De quelle fiche de paie avez-vous besoin?',
            'pt': '📄 Qual holerite você precisa?'
        },
        'payslip_sent': {
            'es': '✅ Tu recibo ha sido enviado a tu correo registrado: {email}',
            'en': '✅ Your payslip has been sent to your registered email: {email}',
            'fr': '✅ Votre fiche de paie a été envoyée à votre e-mail enregistré: {email}',
            'pt': '✅ Seu holerite foi enviado para seu e-mail registrado: {email}'
        },
        'no_payslips': {
            'es': '❌ No encontramos recibos de nómina para tu cuenta.',
            'en': '❌ We couldn\'t find any payslips for your account.',
            'fr': '❌ Nous n\'avons pas trouvé de fiches de paie pour votre compte.',
            'pt': '❌ Não encontramos holerites para sua conta.'
        },
        'balance_info': {
            'es': '📊 *Balance actual*:\n• Vacaciones: {vacation} días\n• Permisos: {permissions} horas\n• Incapacidad: {sick_days} días',
            'en': '📊 *Current balance*:\n• Vacation: {vacation} days\n• Permissions: {permissions} hours\n• Sick leave: {sick_days} days',
            'fr': '📊 *Solde actuel*:\n• Vacances: {vacation} jours\n• Permissions: {permissions} heures\n• Congé maladie: {sick_days} jours',
            'pt': '📊 *Saldo atual*:\n• Férias: {vacation} dias\n• Permissões: {permissions} horas\n• Licença médica: {sick_days} dias'
        }
    },
    
    # Mensajes HR/RH
    'hr': {
        'dashboard_menu': {
            'es': '📊 *Dashboard RH* - Selecciona un reporte:',
            'en': '📊 *HR Dashboard* - Select a report:',
            'fr': '📊 *Tableau de bord RH* - Sélectionnez un rapport:',
            'pt': '📊 *Dashboard RH* - Selecione um relatório:'
        },
        'attendance_report': {
            'es': '📋 *Reporte de Asistencia*\nPeriodo: {period}\nTotal empleados: {total}\nPresentes: {present}\nAusentes: {absent}\nRetardos: {late}',
            'en': '📋 *Attendance Report*\nPeriod: {period}\nTotal employees: {total}\nPresent: {present}\nAbsent: {absent}\nLate: {late}',
            'fr': '📋 *Rapport de présence*\nPériode: {period}\nTotal employés: {total}\nPrésents: {present}\nAbsents: {absent}\nRetards: {late}',
            'pt': '📋 *Relatório de Presença*\nPeríodo: {period}\nTotal funcionários: {total}\nPresentes: {present}\nAusentes: {absent}\nAtrasados: {late}'
        },
        'report_sent': {
            'es': '✅ Reporte enviado a tu correo: {email}',
            'en': '✅ Report sent to your email: {email}',
            'fr': '✅ Rapport envoyé à votre e-mail: {email}',
            'pt': '✅ Relatório enviado para seu e-mail: {email}'
        },
        'unauthorized': {
            'es': '🔒 No tienes permisos para acceder a esta funcionalidad de RH.',
            'en': '🔒 You don\'t have permissions to access this HR functionality.',
            'fr': '🔒 Vous n\'avez pas les permissions pour accéder à cette fonctionnalité RH.',
            'pt': '🔒 Você não tem permissões para acessar esta funcionalidade de RH.'
        }
    },
    
    # Mensajes de ayuda
    'help': {
        'menu': {
            'es': '❓ *Ayuda* - ¿Qué necesitas saber?',
            'en': '❓ *Help* - What do you need to know?',
            'fr': '❓ *Aide* - Que voulez-vous savoir?',
            'pt': '❓ *Ajuda* - O que você precisa saber?'
        },
        'basic_commands': {
            'es': '*Comandos básicos:*\n• entrada - Registrar entrada\n• salida - Registrar salida\n• recibo - Solicitar recibo de nómina\n• balance - Consultar saldos\n• ayuda - Ver este menú',
            'en': '*Basic commands:*\n• checkin - Register arrival\n• checkout - Register departure\n• payslip - Request payslip\n• balance - Check balances\n• help - View this menu',
            'fr': '*Commandes de base:*\n• entrée - Enregistrer l\'arrivée\n• sortie - Enregistrer le départ\n• fiche - Demander fiche de paie\n• solde - Vérifier les soldes\n• aide - Voir ce menu',
            'pt': '*Comandos básicos:*\n• entrada - Registrar entrada\n• saída - Registrar saída\n• holerite - Solicitar holerite\n• saldo - Consultar saldos\n• ajuda - Ver este menu'
        }
    },
    
    # Quick replies y botones
    'buttons': {
        'yes': {
            'es': 'Sí',
            'en': 'Yes',
            'fr': 'Oui',
            'pt': 'Sim'
        },
        'no': {
            'es': 'No',
            'en': 'No',
            'fr': 'Non',
            'pt': 'Não'
        },
        'cancel': {
            'es': 'Cancelar',
            'en': 'Cancel',
            'fr': 'Annuler',
            'pt': 'Cancelar'
        },
        'help': {
            'es': 'Ayuda',
            'en': 'Help',
            'fr': 'Aide',
            'pt': 'Ajuda'
        },
        'main_menu': {
            'es': 'Menú principal',
            'en': 'Main menu',
            'fr': 'Menu principal',
            'pt': 'Menu principal'
        },
        'send_email': {
            'es': 'Enviar por email',
            'en': 'Send by email',
            'fr': 'Envoyer par e-mail',
            'pt': 'Enviar por e-mail'
        }
    }
}


# Funciones de utilidad para la internacionalización
def get_message(category: str, key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Obtiene un mensaje traducido para la categoría, clave e idioma especificados.
    Permite sustitución de variables en el mensaje usando kwargs.
    
    Args:
        category: Categoría del mensaje ('system', 'attendance', etc.)
        key: Clave específica del mensaje
        language: Código ISO del idioma (2 caracteres)
        kwargs: Variables para sustituir en el mensaje
        
    Returns:
        Mensaje traducido con variables sustituidas
    """
    # Si el idioma no está soportado, usar el idioma por defecto
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
        
    # Obtener categoría
    category_dict = MESSAGES.get(category, {})
    
    # Obtener mensaje por clave
    message_dict = category_dict.get(key, {})
    
    # Obtener mensaje traducido
    message = message_dict.get(language, message_dict.get(DEFAULT_LANGUAGE, f"Missing translation: {category}.{key}"))
    
    # Sustituir variables
    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError as e:
            # Si falta alguna variable, lo notificamos pero devolvemos el mensaje
            print(f"Warning: Missing variable {e} in message {category}.{key}")
    
    return message


def get_button_text(key: str, language: str = DEFAULT_LANGUAGE) -> str:
    """
    Obtiene el texto traducido para un botón.
    
    Args:
        key: Clave del botón
        language: Código ISO del idioma
        
    Returns:
        Texto traducido del botón
    """
    return get_message('buttons', key, language)


def detect_language(text: str) -> str:
    """
    Detecta el idioma del texto basándose en palabras clave.
    Muy básico pero funcional para comandos simples.
    
    Args:
        text: Texto a analizar
        
    Returns:
        Código ISO del idioma detectado o idioma por defecto
    """
    text = text.lower()
    
    # Palabras clave por idioma para detección básica
    language_keywords = {
        'en': ['help', 'english', 'checkin', 'checkout', 'payslip', 'balance'],
        'es': ['ayuda', 'español', 'entrada', 'salida', 'recibo', 'balance', 'nómina'],
        'fr': ['aide', 'français', 'entrée', 'sortie', 'fiche', 'solde'],
        'pt': ['ajuda', 'português', 'entrada', 'saída', 'holerite', 'saldo']
    }
    
    # Comandos explícitos de cambio de idioma
    if 'lang:en' in text or 'language:en' in text or 'english' in text:
        return 'en'
    elif 'lang:es' in text or 'language:es' in text or 'español' in text or 'espanol' in text:
        return 'es'
    elif 'lang:fr' in text or 'language:fr' in text or 'français' in text or 'francais' in text:
        return 'fr'
    elif 'lang:pt' in text or 'language:pt' in text or 'português' in text or 'portugues' in text:
        return 'pt'
    
    # Detección por palabras clave
    matches = {}
    for lang, keywords in language_keywords.items():
        matches[lang] = sum(1 for kw in keywords if kw in text)
    
    # Devolver el idioma con más coincidencias, o el default si hay empate o ninguna coincidencia
    if any(matches.values()):
        max_matches = max(matches.values())
        if max_matches > 0:
            for lang, count in matches.items():
                if count == max_matches:
                    return lang
    
    # Si no se detecta ningún idioma, devolver el por defecto
    return DEFAULT_LANGUAGE
