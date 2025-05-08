from ..lazy_imports import lazy_imports, register_module

# Register milkyleak modules for lazy loading
lazy_imports.register('milkyleak', '.milkyleak')
lazy_imports.register('templates', '.templates')
