import os
import sys
import errno
import fcntl
import atexit
import signal
import logging
import tempfile


__version__ = "1.0.9"

DEFAULT_PID_DIR = "/var/run/"


class PidFileError(Exception):
    pass


class PidFileUnreadableError(PidFileError):
    pass


class PidFileAlreadyRunningError(PidFileError):
    pass


class PidFileAlreadyLockedError(PidFileError):
    pass


class PidFile(object):
    __slots__ = ("pid", "filename", "fh", "logger", "lock_pidfile", "chmod", "uid", "gid")

    def __init__(self, pidname=None, piddir=None, enforce_dotpid_postfix=True,
                 register_term_signal_handler=True, lock_pidfile=True,
                 chmod=0o644, uid=-1, gid=-1, force_tmpdir=False):
        self.logger = logging.getLogger("PidFile")
        if pidname is None:
            pidname = "%s.pid" % os.path.basename(sys.argv[0])
        if enforce_dotpid_postfix and not pidname.endswith(".pid"):
            pidname = "%s.pid" % pidname
        if piddir is None:
            if os.path.isdir(DEFAULT_PID_DIR) and force_tmpdir is False:
                piddir = DEFAULT_PID_DIR
            else:
                piddir = tempfile.gettempdir()

        if not os.path.isdir(piddir):
            os.makedirs(piddir)
        if not os.access(piddir, os.R_OK):
            raise IOError("Pid file directory '%s' cannot be read" % piddir)
        if not os.access(piddir, os.W_OK):
            raise IOError("Pid file directory '%s' cannot be written to" % piddir)

        self.lock_pidfile = lock_pidfile
        self.chmod = chmod
        self.uid = uid
        self.gid = gid
        self.filename = os.path.abspath(os.path.join(piddir, pidname))
        self.pid = os.getpid()
        self.fh = None

        if register_term_signal_handler:
            # Register TERM signal handler to make sure atexit runs on TERM signal
            def sigterm_noop_handler(*args, **kwargs):
                raise SystemExit(1)

            signal.signal(signal.SIGTERM, sigterm_noop_handler)

    def check(self):
        def __check(fh):
            try:
                fh.seek(0)
                pid_str = fh.read(16).split("\n", 1)[0].strip()
                if not pid_str:
                    return None
                pid = int(pid_str)
            except (IOError, ValueError) as exc:
                self.close(fh=fh)
                raise PidFileUnreadableError(exc)
            try:
                os.kill(pid, 0)
            except OSError as exc:
                if exc.errno == errno.ESRCH:
                    # this pid is not running
                    return None
                self.close(fh=fh, cleanup=False)
                raise PidFileAlreadyRunningError(exc)
            self.close(fh=fh, cleanup=False)
            raise PidFileAlreadyRunningError("Program already running with pid: %d" % pid)
        if self.fh is None:
            if os.path.isfile(self.filename):
                with open(self.filename, "r") as fh:
                    __check(fh)
        else:
            __check(self.fh)

    def create(self):
        self.fh = open(self.filename, 'a+')
        if self.lock_pidfile:
            try:
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError as exc:
                self.close(cleanup=False)
                raise PidFileAlreadyLockedError(exc)
        self.check()
        if self.chmod:
            os.fchmod(self.fh.fileno(), self.chmod)
        if self.uid >= 0 or self.gid >= 0:
            os.fchown(self.fh.fileno(), self.uid, self.gid)
        self.fh.seek(0)
        self.fh.truncate()
        # pidfile must consist of the pid and a newline character
        self.fh.write("%d\n" % self.pid)
        self.fh.flush()
        self.fh.seek(0)
        atexit.register(self.close)

    def close(self, fh=None, cleanup=True):
        if not fh:
            fh = self.fh
        try:
            fh.close()
        except IOError as exc:
            # ignore error when file was already closed
            if exc.errno != errno.EBADF:
                raise
        finally:
            if os.path.isfile(self.filename) and cleanup:
                os.remove(self.filename)

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
        self.close()
