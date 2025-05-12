# /home/pablo/app/import_config.py
import importlib
import sys
from typing import Dict, Any, Callable, Optional
from pathlib import Path
import logging
import os
from datetime import datetime

# Configure logger
logger = logging.getLogger('import_config')
logger.setLevel(logging.INFO)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(ch)

class ModuleRegistry:
    def __init__(self):
        self._modules = {}
        self._logger = logging.getLogger('module_registry')
        self._initialized = False

    def register_module(self, name: str, module_path: str) -> None:
        """
        Register a module for lazy loading.
        
        Args:
            name: The name to use when accessing the module
            module_path: The full module path (e.g., 'app.com.chatbot.chatbot')
        """
        if name in self._modules:
            self._logger.warning(f"Module {name} already registered")
            return
        self._modules[name] = module_path
        self._logger.debug(f"Registered module {name} from {module_path}")

    def get_module(self, name: str) -> Any:
        """
        Get a registered module.
        
        Args:
            name: The name of the module to get
            
        Returns:
            The lazy-loaded module
            
        Raises:
            ImportError: If the module is not registered
        """
        if name not in self._modules:
            self._logger.error(f"Module {name} not registered")
            raise ImportError(f"Module {name} not registered")
            
        module_path = self._modules[name]
        try:
            if module_path not in sys.modules:
                module = importlib.import_module(module_path)
                sys.modules[module_path] = module
            return sys.modules[module_path]
        except ImportError as e:
            self._logger.error(f"Error importing {module_path}: {str(e)}")
            raise

    def register_from_config(self, config_path: str) -> None:
        """
        Register modules from a configuration file.
        
        Args:
            config_path: Path to the configuration file containing module mappings
        """
        try:
            config_module = importlib.import_module(config_path)
            for name, module_path in config_module.__dict__.items():
                if not name.startswith('_') and isinstance(module_path, str):
                    self.register_module(name, module_path)
        except ImportError as e:
            self._logger.error(f"Error loading config from {config_path}: {str(e)}")
            raise

    def initialize(self) -> None:
        """
        Initialize all registered modules.
        This method should be called during application startup.
        """
        if self._initialized:
            return
            
        self._logger.info("Initializing module registry...")
        start_time = datetime.now()
        
        for name, module_path in self._modules.items():
            try:
                self.get_module(name)
                self._logger.info(f"Successfully initialized {name} from {module_path}")
            except Exception as e:
                self._logger.error(f"Failed to initialize {name}: {str(e)}")
                
        self._initialized = True
        end_time = datetime.now()
        self._logger.info(f"Module registry initialization completed in {end_time - start_time}")

# Create a global instance of ModuleRegistry
module_registry = ModuleRegistry()

def register_module(name: str, module_path: str) -> None:
    """
    Register a module for lazy loading.
    
    Args:
        name: The name to use when accessing the module
        module_path: The full module path (e.g., 'app.com.chatbot.chatbot')
    """
    module_registry.register_module(name, module_path)

def get_module(name: str) -> Any:
    """
    Get a registered module.
    
    Args:
        name: The name of the module to get
        
    Returns:
        The lazy-loaded module
        
    Raises:
        ImportError: If the module is not registered
    """
    return module_registry.get_module(name)

def register_from_config(config_path: str) -> None:
    """
    Register modules from a configuration file.
    
    Args:
        config_path: Path to the configuration file containing module mappings
    """
    module_registry.register_from_config(config_path)

def initialize_all() -> None:
    """
    Initialize all registered modules.
    This method should be called during application startup.
    """
    module_registry.initialize()

def validate_imports() -> bool:
    """
    Validate and register essential modules.
    
    Returns:
        bool: True if validation passed, False otherwise
    """
    # List of essential packages to register
    essential_packages = ['ml', 'sexsi', 'com', 'pagos', 'publish']
    
    # Register essential modules
    for package in essential_packages:
        try:
            config_path = f"app.{package}.import_config"
            register_from_config(config_path)
            logger.info(f"Successfully registered modules from package {package}")
        except Exception as e:
            logger.error(f"Error registering modules from {package}: {str(e)}")
            continue
    
    # Initialize all modules
    try:
        initialize_all()
        return True
    except Exception as e:
        logger.error(f"Error initializing modules: {str(e)}")
        return False

# Register essential modules at startup
if os.environ.get('DJANGO_SETTINGS_MODULE'):
    validate_imports()
