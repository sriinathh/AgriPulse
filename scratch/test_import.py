import sys, os
# Ensure the project root (one level up from scratch) is on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
import app
print('app init path:', getattr(app, '__file__', 'builtin'))
import importlib
cfg = importlib.import_module('app.config')
print('config loaded, DB URL:', cfg.get_settings().database_url)


