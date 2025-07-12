import sys
import os
from types import MethodType

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
