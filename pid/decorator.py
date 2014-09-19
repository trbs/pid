import types
from functools import wraps
from . import PidFile


def pidfile(*pid_args, **pid_kwargs):
    if len(pid_args) > 0:
        assert not isinstance(pid_args[0], types.FunctionType), "pidfile decorator must be called with parentheses, like: @pidfile()"

    def wrapper(func):
        @wraps(func)
        def decorator(*func_args, **func_kwargs):
            with PidFile(*pid_args, **pid_kwargs):
                return func(*func_args, **func_kwargs)
        return decorator
    return wrapper
