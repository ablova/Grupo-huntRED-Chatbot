import sys
from functools import wraps

def skip_on_migrate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return None
        return func(*args, **kwargs)
    return wrapper 