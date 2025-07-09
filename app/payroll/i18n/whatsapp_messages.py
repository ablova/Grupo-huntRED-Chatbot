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
            'pt': '✅ Idioma alterado para Português.',
            'de': '✅ Sprache auf Deutsch geändert.',
            'zh': '✅ 语言已更改为中文。',
            'ar': '✅ تم تغيير اللغة إلى العربية.'
        },
        'unsupported_language': {
            'es': '❌ Idioma no soportado. Idiomas disponibles: Español, English, Français, Português.',
            'en': '❌ Unsupported language. Available languages: Español, English, Français, Português.',
            'fr': '❌ Langue non prise en charge. Langues disponibles: Español, English, Français, Português.',
            'pt': '❌ Idioma não suportado. Idiomas disponíveis: Español, English, Français, Português.',
            'de': '❌ Nicht unterstützte Sprache. Verfügbare Sprachen: Español, English, Français, Português.',
            'zh': '❌ 不支持的语言。可用语言：Español, English, Français, Português。',
            'ar': '❌ لغة غير مدعومة. اللغات المتاحة: Español, English, Français, Português.'
        },
        'welcome': {
            'es': '👋 ¡Bienvenido/a al servicio de nómina por WhatsApp!',
            'en': '👋 Welcome to the Payroll WhatsApp service!',
            'fr': '👋 Bienvenue au service de paie par WhatsApp!',
            'pt': '👋 Bem-vindo/a ao serviço de folha de pagamento por WhatsApp!',
            'de': '👋 Willkommen beim Lohnabrechnungsservice über WhatsApp!',
            'zh': '👋 欢迎使用WhatsApp工资服务！',
            'ar': '👋 مرحبًا بك في خدمة الرواتب عبر WhatsApp!'
        },
        'user_not_found': {
            'es': '❌ No podemos identificar tu número en nuestro sistema. Por favor, contacta a RH.',
            'en': '❌ We cannot identify your number in our system. Please contact HR.',
            'fr': '❌ Nous ne pouvons pas identifier votre numéro dans notre système. Veuillez contacter RH.',
            'pt': '❌ Não podemos identificar seu número em nosso sistema. Entre em contato com RH.',
            'de': '❌ Wir können Ihre Nummer in unserem System nicht identifizieren. Bitte kontaktieren Sie die Personalabteilung.',
            'zh': '❌ 我们无法在系统中识别您的号码。请联系人力资源部门。',
            'ar': '❌ لا يمكننا التعرف على رقمك في نظامنا. يرجى التواصل مع إدارة الموارد البشرية.'
        },
        'error': {
            'es': '❌ Error procesando tu mensaje. Por favor intenta nuevamente.',
            'en': '❌ Error processing your message. Please try again.',
            'fr': '❌ Erreur lors du traitement de votre message. Veuillez réessayer.',
            'pt': '❌ Erro ao processar sua mensagem. Por favor, tente novamente.',
            'de': '❌ Fehler beim Verarbeiten Ihrer Nachricht. Bitte versuchen Sie es erneut.',
            'zh': '❌ 处理您的消息时出错。请重试。',
            'ar': '❌ خطأ في معالجة رسالتك. يرجى المحاولة مرة أخرى.'
        }
    },
    
    # Mensajes de asistencia
    'attendance': {
        'checkin_request': {
            'es': '📍 Por favor, comparte tu ubicación para registrar tu entrada.',
            'en': '📍 Please share your location to register your check-in.',
            'fr': '📍 Veuillez partager votre emplacement pour enregistrer votre arrivée.',
            'pt': '📍 Por favor, compartilhe sua localização para registrar sua entrada.',
            'de': '📍 Bitte teilen Sie Ihren Standort, um Ihre Ankunft zu registrieren.',
            'zh': '📍 请分享您的位置以登记入场。',
            'ar': '📍 يرجى مشاركة موقعك لتسجيل دخولك.'
        },
        'checkin_success': {
            'es': '✅ ¡Entrada registrada con éxito! Hora: {time}',
            'en': '✅ Check-in successfully registered! Time: {time}',
            'fr': '✅ Entrée enregistrée avec succès! Heure: {time}',
            'pt': '✅ Entrada registrada com sucesso! Hora: {time}',
            'de': '✅ Ankunft erfolgreich registriert! Uhrzeit: {time}',
            'zh': '✅ 入场登记成功！时间：{time}',
            'ar': '✅ تم تسجيل الدخول بنجاح! الوقت: {time}'
        },
        'checkout_request': {
            'es': '📍 Por favor, comparte tu ubicación para registrar tu salida.',
            'en': '📍 Please share your location to register your check-out.',
            'fr': '📍 Veuillez partager votre emplacement pour enregistrer votre départ.',
            'pt': '📍 Por favor, compartilhe sua localização para registrar sua saída.',
            'de': '📍 Bitte teilen Sie Ihren Standort, um Ihren Abgang zu registrieren.',
            'zh': '📍 请分享您的位置以登记离场。',
            'ar': '📍 يرجى مشاركة موقعك لتسجيل خروجك.'
        },
        'checkout_success': {
            'es': '✅ ¡Salida registrada con éxito! Hora: {time}',
            'en': '✅ Check-out successfully registered! Time: {time}',
            'fr': '✅ Sortie enregistrée avec succès! Heure: {time}',
            'pt': '✅ Saída registrada com sucesso! Hora: {time}',
            'de': '✅ Abgang erfolgreich registriert! Uhrzeit: {time}',
            'zh': '✅ 离场登记成功！时间：{time}',
            'ar': '✅ تم تسجيل الخروج بنجاح! الوقت: {time}'
        },
        'already_checked_in': {
            'es': '⚠️ Ya tienes una entrada registrada hoy a las {time}.',
            'en': '⚠️ You already have a check-in registered today at {time}.',
            'fr': '⚠️ Vous avez déjà une entrée enregistrée aujourd\'hui à {time}.',
            'pt': '⚠️ Você já tem uma entrada registrada hoje às {time}.',
            'de': '⚠️ Sie haben heute bereits um {time} eine Ankunft registriert.',
            'zh': '⚠️ 您今天已在{time}登记过入场。',
            'ar': '⚠️ لقد سجلت دخولك اليوم بالفعل في الساعة {time}.'
        },
        'no_checkin': {
            'es': '⚠️ No tienes entrada registrada hoy. No puedes registrar salida.',
            'en': '⚠️ You don\'t have a check-in registered today. You cannot check out.',
            'fr': '⚠️ Vous n\'avez pas d\'entrée enregistrée aujourd\'hui. Vous ne pouvez pas enregistrer de sortie.',
            'pt': '⚠️ Você não tem entrada registrada hoje. Não pode registrar saída.',
            'de': '⚠️ Sie haben heute keine Ankunft registriert. Sie können keinen Abgang registrieren.',
            'zh': '⚠️ 您今天没有登记入场，无法登记离场。',
            'ar': '⚠️ لم يتم تسجيل دخولك اليوم. لا يمكنك تسجيل الخروج.'
        },
        'invalid_location': {
            'es': '⚠️ Tu ubicación está demasiado lejos de la oficina. Se notificará a tu supervisor.',
            'en': '⚠️ Your location is too far from the office. Your supervisor will be notified.',
            'fr': '⚠️ Votre emplacement est trop éloigné du bureau. Votre superviseur sera notifié.',
            'pt': '⚠️ Sua localização está muito longe do escritório. Seu supervisor será notificado.',
            'de': '⚠️ Ihr Standort ist zu weit vom Büro entfernt. Ihr Vorgesetzter wird benachrichtigt.',
            'zh': '⚠️ 您的位置离办公室太远，将通知您的主管。',
            'ar': '⚠️ موقعك بعيد جدًا عن المكتب. سيتم إبلاغ مشرفك.'
        }
    },
    
    # Mensajes de nómina
    'payroll': {
        'payslip_request': {
            'es': '📄 ¿Qué recibo de nómina necesitas?',
            'en': '📄 Which payslip do you need?',
            'fr': '📄 De quelle fiche de paie avez-vous besoin?',
            'pt': '📄 Qual holerite você precisa?',
            'de': '📄 Welche Lohnabrechnung benötigen Sie?',
            'zh': '📄 您需要哪份工资单？',
            'ar': '📄 أي إيصال راتب تحتاج؟'
        },
        'payslip_sent': {
            'es': '✅ Tu recibo ha sido enviado a tu correo registrado: {email}',
            'en': '✅ Your payslip has been sent to your registered email: {email}',
            'fr': '✅ Votre fiche de paie a été envoyée à votre e-mail enregistré: {email}',
            'pt': '✅ Seu holerite foi enviado para seu e-mail registrado: {email}',
            'de': '✅ Ihre Lohnabrechnung wurde an Ihre registrierte E-Mail gesendet: {email}',
            'zh': '✅ 您的工资单已发送至您的注册邮箱：{email}',
            'ar': '✅ تم إرسال إيصال راتبك إلى بريدك الإلكتروني المسجل: {email}'
        },
        'no_payslips': {
            'es': '❌ No encontramos recibos de nómina para tu cuenta.',
            'en': '❌ We couldn\'t find any payslips for your account.',
            'fr': '❌ Nous n\'avons pas trouvé de fiches de paie pour votre compte.',
            'pt': '❌ Não encontramos holerites para sua conta.',
            'de': '❌ Wir konnten keine Lohnabrechnungen für Ihr Konto finden.',
            'zh': '❌ 我们找不到您账户的工资单。',
            'ar': '❌ لم نجد أي إيصالات رواتب لحسابك.'
        },
        'balance_info': {
            'es': '📊 *Balance actual*:\n• Vacaciones: {vacation} días\n• Permisos: {permissions} horas\n• Incapacidad: {sick_days} días',
            'en': '📊 *Current balance*:\n• Vacation: {vacation} days\n• Permissions: {permissions} hours\n• Sick leave: {sick_days} days',
            'fr': '📊 *Solde actuel*:\n• Vacances: {vacation} jours\n• Permissions: {permissions} heures\n• Congé maladie: {sick_days} jours',
            'pt': '📊 *Saldo atual*:\n• Férias: {vacation} dias\n• Permissões: {permissions} horas\n• Licença médica: {sick_days} dias',
            'de': '📊 *Aktueller Stand*:\n• Urlaub: {vacation} Tage\n• Genehmigungen: {permissions} Stunden\n• Krankheitsurlaub: {sick_days} Tage',
            'zh': '📊 *当前余额*:\n• 假期: {vacation} 天\n• 许可: {permissions} 小时\n• 病假: {sick_days} 天',
            'ar': '📊 *الرصيد الحالي*:\n• الإجازات: {vacation} أيام\n• التصاريح: {permissions} ساعات\n• الإجازة المرضية: {sick_days} أيام'
        }
    },
    
    # Mensajes HR/RH
    'hr': {
        'dashboard_menu': {
            'es': '📊 *Dashboard RH* - Selecciona un reporte:',
            'en': '📊 *HR Dashboard* - Select a report:',
            'fr': '📊 *Tableau de bord RH* - Sélectionnez un rapport:',
            'pt': '📊 *Dashboard RH* - Selecione um relatório:',
            'de': '📊 *HR-Dashboard* - Wählen Sie einen Bericht aus:',
            'zh': '📊 *人力资源仪表板* - 选择一个报告：',
            'ar': '📊 *لوحة تحكم الموارد البشرية* - اختر تقريرًا:'
        },
        'attendance_report': {
            'es': '📋 *Reporte de Asistencia*\nPeriodo: {period}\nTotal empleados: {total}\nPresentes: {present}\nAusentes: {absent}\nRetardos: {late}',
            'en': '📋 *Attendance Report*\nPeriod: {period}\nTotal employees: {total}\nPresent: {present}\nAbsent: {absent}\nLate: {late}',
            'fr': '📋 *Rapport de présence*\nPériode: {period}\nTotal employés: {total}\nPrésents: {present}\nAbsents: {absent}\nRetards: {late}',
            'pt': '📋 *Relatório de Presença*\nPeríodo: {period}\nTotal funcionários: {total}\nPresentes: {present}\nAusentes: {absent}\nAtrasados: {late}',
            'de': '📋 *Anwesenheitsbericht*\nZeitraum: {period}\nGesamtmitarbeiter: {total}\nAnwesend: {present}\nAbwesend: {absent}\nVerspätet: {late}',
            'zh': '📋 *出勤报告*\n期间: {period}\n总员工: {total}\n在场: {present}\n缺席: {absent}\n迟到: {late}',
            'ar': '📋 *تقرير الحضور*\nالفترة: {period}\nإجمالي الموظفين: {total}\nالحاضرين: {present}\nالغائبين: {absent}\nالمتأخرين: {late}'
        },
        'report_sent': {
            'es': '✅ Reporte enviado a tu correo: {email}',
            'en': '✅ Report sent to your email: {email}',
            'fr': '✅ Rapport envoyé à votre e-mail: {email}',
            'pt': '✅ Relatório enviado para seu e-mail: {email}',
            'de': '✅ Bericht an Ihre E-Mail gesendet: {email}',
            'zh': '✅ 报告已发送至您的邮箱：{email}',
            'ar': '✅ تم إرسال التقرير إلى بريدك الإلكتروني: {email}'
        },
        'unauthorized': {
            'es': '🔒 No tienes permisos para acceder a esta funcionalidad de RH.',
            'en': '🔒 You don\'t have permissions to access this HR functionality.',
            'fr': '🔒 Vous n\'avez pas les permissions pour accéder à cette fonctionnalité RH.',
            'pt': '🔒 Você não tem permissões para acessar esta funcionalidade de RH.',
            'de': '🔒 Sie haben keine Berechtigung, auf diese HR-Funktion zuzugreifen.',
            'zh': '🔒 您没有权限访问此人力资源功能。',
            'ar': '🔒 ليس لديك إذن للوصول إلى هذه الوظيفة في الموارد البشرية.'
        }
    },
    
    # Mensajes de ayuda
    'help': {
        'menu': {
            'es': '❓ *Ayuda* - ¿Qué necesitas saber?',
            'en': '❓ *Help* - What do you need to know?',
            'fr': '❓ *Aide* - Que voulez-vous savoir?',
            'pt': '❓ *Ajuda* - O que você precisa saber?',
            'de': '❓ *Hilfe* - Was möchten Sie wissen?',
            'zh': '❓ *帮助* - 您想知道什么？',
            'ar': '❓ *المساعدة* - ماذا تريد أن تعرف؟'
        },
        'basic_commands': {
            'es': '*Comandos básicos:*\n• entrada - Registrar entrada\n• salida - Registrar salida\n• recibo - Solicitar recibo de nómina\n• balance - Consultar saldos\n• ayuda - Ver este menú',
            'en': '*Basic commands:*\n• checkin - Register arrival\n• checkout - Register departure\n• payslip - Request payslip\n• balance - Check balances\n• help - View this menu',
            'fr': '*Commandes de base:*\n• entrée - Enregistrer l\'arrivée\n• sortie - Enregistrer le départ\n• fiche - Demander fiche de paie\n• solde - Vérifier les soldes\n• aide - Voir ce menu',
            'pt': '*Comandos básicos:*\n• entrada - Registrar entrada\n• saída - Registrar saída\n• holerite - Solicitar holerite\n• saldo - Consultar saldos\n• ajuda - Ver este menu',
            'de': '*Grundbefehle:*\n• einchecken - Ankunft registrieren\n• auschecken - Abgang registrieren\n• lohnabrechnung - Lohnabrechnung anfordern\n• kontostand - Kontostände prüfen\n• hilfe - Dieses Menü anzeigen',
            'zh': '*基本命令:*\n• 入场 - 登记入场\n• 离场 - 登记离场\n• 工资单 - 请求工资单\n• 余额 - 检查余额\n• 帮助 - 查看此菜单',
            'ar': '*الأوامر الأساسية:*\n• تسجيل الدخول - تسجيل الوصول\n• تسجيل الخروج - تسجيل المغادرة\n• إيصال الراتب - طلب إيصال الراتب\n• الرصيد - التحقق من الأرصدة\n• المساعدة - عرض هذه القائمة'
        }
    },
    
    # Quick replies y botones
    'buttons': {
        'yes': {
            'es': 'Sí',
            'en': 'Yes',
            'fr': 'Oui',
            'pt': 'Sim',
            'de': 'Ja',
            'zh': '是',
            'ar': 'نعم'
        },
        'no': {
            'es': 'No',
            'en': 'No',
            'fr': 'Non',
            'pt': 'Não',
            'de': 'Nein',
            'zh': '否',
            'ar': 'لا'
        },
        'cancel': {
            'es': 'Cancelar',
            'en': 'Cancel',
            'fr': 'Annuler',
            'pt': 'Cancelar',
            'de': 'Abbrechen',
            'zh': '取消',
            'ar': 'إلغاء'
        },
        'help': {
            'es': 'Ayuda',
            'en': 'Help',
            'fr': 'Aide',
            'pt': 'Ajuda',
            'de': 'Hilfe',
            'zh': '帮助',
            'ar': 'مساعدة'
        },
        'main_menu': {
            'es': 'Menú principal',
            'en': 'Main menu',
            'fr': 'Menu principal',
            'pt': 'Menu principal',
            'de': 'Hauptmenü',
            'zh': '主菜单',
            'ar': 'القائمة الرئيسية'
        },
        'send_email': {
            'es': 'Enviar por email',
            'en': 'Send by email',
            'fr': 'Envoyer par e-mail',
            'pt': 'Enviar por e-mail',
            'de': 'Per E-Mail senden',
            'zh': '通过电子邮件发送',
            'ar': 'إرسال عبر البريد الإلكتروني'
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
        'pt': ['ajuda', 'português', 'entrada', 'saída', 'holerite', 'saldo'],
        'de': ['hilfe', 'deutsch', 'einchecken', 'auschecken', 'lohnabrechnung', 'kontostand'],
        'zh': ['帮助', '中文', '入场', '离场', '工资单', '余额'],
        'ar': ['مساعدة', 'عربي', 'تسجيل الدخول', 'تسجيل الخروج', 'إيصال الراتب', 'رصيد']
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
    elif 'lang:de' in text or 'language:de' in text or 'deutsch' in text:
        return 'de'
    elif 'lang:zh' in text or 'language:zh' in text or '中文' in text:
        return 'zh'
    elif 'lang:ar' in text or 'language:ar' in text or 'عربي' in text:
        return 'ar'
    
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