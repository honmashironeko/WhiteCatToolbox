import os
import sys

original_path = list(sys.path)
cleaned_path = []

for path in original_path:
    if not any(x in path.lower() for x in [
        'appdata\\roaming\\python',
        'program files\\python',
        'programdata\\anaconda',
        'site-packages'
    ]):
        cleaned_path.append(path)

sys.path = cleaned_path

env_vars_to_clear = [
    'PYTHONPATH',
    'PYTHONHOME',
    'PYTHONSTARTUP',
    'PYTHONUSERBASE',
]

for var in env_vars_to_clear:
    if var in os.environ:
        del os.environ[var]