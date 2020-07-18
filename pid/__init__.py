import sys
from .base import (
    DEFAULT_PID_DIR,
    PID_CHECK_EMPTY,
    PID_CHECK_NOFILE,
    PID_CHECK_SAMEPID,
    PID_CHECK_NOTRUNNING,
    PidFileError,
    PidFileConfigurationError,
    PidFileUnreadableError,
    PidFileAlreadyRunningError,
    PidFileAlreadyLockedError,
)

if sys.platform == "win32":
    from .win32 import PidFile  # NOQA
else:
    from .posix import PidFile  # NOQA

__version__ = "3.0.4"
__all__ = [
    '__version__',
    'DEFAULT_PID_DIR',
    'PID_CHECK_EMPTY',
    'PID_CHECK_NOFILE',
    'PID_CHECK_SAMEPID',
    'PID_CHECK_NOTRUNNING',
    'PidFile',
    'PidFileError',
    'PidFileConfigurationError',
    'PidFileUnreadableError',
    'PidFileAlreadyRunningError',
    'PidFileAlreadyLockedError',
]
