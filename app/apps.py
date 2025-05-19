# /home/pablo/app/apps.py
import logging
import sys
import os
import importlib
from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings

logger = logging.getLogger(__name__)

class AppConfig(DjangoAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # Evitar ejecución en comandos de gestión como migrate, makemigrations, etc.
        if any(arg in sys.argv for arg in ['migrate', 'makemigrations', 'collectstatic']):
            logger.info("Ejecución mínima durante comandos de migración")
            return
        
        # Inicializar sistema de optimización integral
        self._initialize_optimization_systems()
        
        # Inicializar proyecto (gestionar __init__.py y registrar módulos)
        try:
            from app.module_registry import init_project
            init_project()
            logger.info("Proyecto inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando proyecto: {str(e)}")
        
        # Importar signals centralizados
        try:
            # Primero intentar importar sistema centralizado de señales
            import app.signals
            logger.info("Signals centralizados cargados correctamente")
        except ImportError as e:
            logger.error(f"Error importing signals: {str(e)}")
            try:
                from app.ml.core.optimizers import configure_tensorflow
                configure_tensorflow()
            except ImportError as e:
                logger.error(f"Error configuring TensorFlow: {str(e)}")
        
        # Configurar PDFKit
        try:
            import pdfkit
            pdfkit_config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
            pdfkit.configuration = pdfkit_config
        except Exception as e:
            logger.error(f"Error configurando PDFKit: {str(e)}")
        
        # Registrar handlers solo en entornos de ejecución
        if 'runserver' in sys.argv or 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
            try:
                self.register_startup_handlers()
            except Exception as e:
                logger.error(f"Error registering startup handlers: {str(e)}")
                
        # Aplicar optimizaciones de consultas a base de datos
        if 'runserver' in sys.argv or 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
            try:
                self._apply_database_optimizations()
            except Exception as e:
                logger.error(f"Error applying database optimizations: {str(e)}")

    def register_startup_handlers(self):
        from django.core.signals import request_started
        from django.db.models.signals import post_migrate
        if settings.DEBUG:
            request_started.connect(self._load_dynamic_settings, weak=False)
        post_migrate.connect(self._setup_periodic_tasks, weak=False)

    def _load_dynamic_settings(self, **kwargs):
        from django.core.signals import request_started
        request_started.disconnect(self._load_dynamic_settings)
        try:
            self._load_settings_from_db()
        except Exception as e:
            logger.error(f"Error loading dynamic settings: {e}")
            self._set_default_settings()

    def _load_settings_from_db(self):
        from django.apps import apps
        Configuracion = apps.get_model('app', 'Configuracion')
        config = Configuracion.objects.first()
        if config:
            settings.SECRET_KEY = config.secret_key or settings.SECRET_KEY
            settings.DEBUG = config.debug_mode if config.debug_mode is not None else settings.DEBUG
            settings.SENTRY_DSN = config.sentry_dsn or settings.SENTRY_DSN
            logger.info("Dynamic settings loaded successfully")
        else:
            logger.warning("No configuration found in database. Using defaults")
            self._set_default_settings()

    def _set_default_settings(self):
        DEFAULT_SETTINGS = {
            'SECRET_KEY': 'hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48',
            'DEBUG': False,
            'SENTRY_DSN': 'https://94c6575f877d16a00cc74bcaaab5ae79@o4508258791653376.ingest.us.sentry.io/4508258794471424',
        }
        for key, value in DEFAULT_SETTINGS.items():
            if not hasattr(settings, key) or getattr(settings, key) is None:
                setattr(settings, key, value)

    def _setup_periodic_tasks(self, **kwargs):
        from ai_huntred.celery import app
        try:
            # Importar de forma dinámica para evitar error si no existe
            try:
                from app.tasks.scheduler import setup_periodic_tasks
                app.on_after_configure.connect(setup_periodic_tasks)
                logger.info("Periodic tasks registered successfully")
            except ImportError:
                # Intentar método antiguo
                app.on_after_configure.connect(setup_periodic_tasks)
                logger.info("Periodic tasks registered with legacy method")
        except Exception as e:
            logger.error(f"Error registering periodic tasks: {e}")
            
    def _initialize_optimization_systems(self):
        """Inicializa todos los sistemas de optimización."""
        try:
            # Intentar cargar el integrador centralizado
            try:
                from app.utils.system_integrator import SystemIntegrator
                SystemIntegrator.initialize()
                logger.info("Sistema de optimización centralizado inicializado correctamente")
                return
            except ImportError:
                logger.debug("Integrador centralizado no disponible, inicializando sistemas individuales")
            
            # Inicializar componentes individuales si el integrador no está disponible
            optimizations_initialized = []
            
            # 1. Sistema de logging
            try:
                from app.utils.logging_manager import LoggingManager
                LoggingManager.setup_logging()
                optimizations_initialized.append("Sistema de logging")
            except ImportError:
                pass
                
            # 2. Configuración centralizada
            try:
                from app.utils.system_config import initialize_system_config
                initialize_system_config()
                optimizations_initialized.append("Configuración centralizada")
            except ImportError:
                pass
                
            # 3. Performance tracking
            try:
                from app.utils.system_optimization import PerformanceTracker
                tracker = PerformanceTracker()
                optimizations_initialized.append("Tracking de rendimiento")
            except ImportError:
                pass
                
            if optimizations_initialized:
                logger.info(f"Sistemas inicializados: {', '.join(optimizations_initialized)}")
                
        except Exception as e:
            logger.error(f"Error inicializando sistemas de optimización: {str(e)}")
            
    def _apply_database_optimizations(self):
        """Aplica optimizaciones a la base de datos."""
        try:
            # Intentar usar integrador centralizado
            try:
                from app.utils.integrations import apply_query_optimizations
                apply_query_optimizations()
                logger.info("Optimizaciones de base de datos aplicadas correctamente")
                return
            except ImportError:
                pass
                
            # Intentar aplicar optimizaciones individuales
            try:
                from app.utils.orm_optimizer import QueryPerformanceAnalyzer
                # Analizar modelos críticos
                from django.apps import apps
                critical_models = ['BusinessUnit', 'Person', 'Vacante', 'Pago']
                
                for model_name in critical_models:
                    try:
                        Model = apps.get_model('app', model_name)
                        QueryPerformanceAnalyzer.suggest_indexes(Model)
                    except Exception:
                        continue
                        
                logger.info("Análisis de modelos completado correctamente")
            except ImportError:
                pass
                
        except Exception as e:
            logger.error(f"Error aplicando optimizaciones de base de datos: {str(e)}")