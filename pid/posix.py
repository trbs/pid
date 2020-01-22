import os
import errno
import fcntl
from .base import (
    PidFileBase,
    PidFileAlreadyRunningError,
)


class PidFile(PidFileBase):
    def _pid_exists(self, pid):
        try:
            os.kill(pid, 0)
        except OSError as exc:
            if exc.errno == errno.ESRCH:
                # this pid is not running
                return False
            raise PidFileAlreadyRunningError(exc)
        return True

    def _flock(self, fileno):
        fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _chmod(self):
        if self.chmod:
            os.fchmod(self.fh.fileno(), self.chmod)

    def _chown(self):
        if self.uid >= 0 or self.gid >= 0:
            os.fchown(self.fh.fileno(), self.uid, self.gid)
