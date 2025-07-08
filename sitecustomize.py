import sys
import os
from types import MethodType
import locale
try:
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def _always_true(*args, **kwargs): 
    return True

for stream_name in ("stdout", "stderr", "stdin", "__stdout__", "__stderr__", "__stdin__"):
    stream = getattr(sys, stream_name, None)
    if stream is not None and hasattr(stream, "isatty"):
        try:
            setattr(stream, "isatty", MethodType(lambda self: True, stream))
        except Exception:
            pass

try:
    os.isatty = _always_true  
except Exception:
    pass
