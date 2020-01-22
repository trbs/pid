import msvcrt  # NOQA
# Using psutil library for windows instead of os.kill call
import psutil
from .base import (
    PidFileBase,
    PidFileAlreadyRunningError,
    SamePidFileNotSupported,
    PidFileConfigurationError,
)


class PidFile(PidFileBase):
    def __init__(self):
        super(PidFile, self).__init__()
        if self.allow_samepid:
            raise SamePidFileNotSupported("Flag allow_samepid is not supported on non-POSIX systems")

    def _inner_check(self, fh):
        # Try to read from file to check if it is locked by the same process
        try:
            fh.seek(0)
            fh.read(1)
        except IOError as exc:
            self.close(fh=fh, cleanup=False)
            if exc.errno == 13:
                raise PidFileAlreadyRunningError(exc)
            raise
        return super(PidFile, self)._inner_check(fh)

    def _pid_exists(self, pid):
        return psutil.pid_exists(pid)

    def _flock(self, fileno):
        msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
        # Try to read from file to check if it is actually locked
        self.fh.seek(0)
        self.fh.read(1)

    def _chmod(self):
        if self.chmod:
            raise PidFileConfigurationError("chmod supported on win32")

    def _chown(self):
        if self.uid >= 0 or self.gid >= 0:
            raise PidFileConfigurationError("chown supported on win32")
