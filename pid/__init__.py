import os
import sys
import errno
import fcntl
import atexit
import signal
import logging
import tempfile


__version__ = "2.0.0"

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
    __slots__ = ("pid", "pidname", "piddir", "enforce_dotpid_postfix", "register_term_signal_handler",
                 "filename", "fh", "lock_pidfile", "chmod", "uid", "gid", "force_tmpdir",
                 "_logger", "_is_setup")

    def __init__(self, pidname=None, piddir=None, enforce_dotpid_postfix=True,
                 register_term_signal_handler='auto', lock_pidfile=True, chmod=0o644,
                 uid=-1, gid=-1, force_tmpdir=False):
        self.pidname = pidname
        self.piddir = piddir
        self.enforce_dotpid_postfix = enforce_dotpid_postfix
        self.register_term_signal_handler = register_term_signal_handler
        self.lock_pidfile = lock_pidfile
        self.chmod = chmod
        self.uid = uid
        self.gid = gid
        self.force_tmpdir = force_tmpdir

        self.fh = None
        self.filename = None
        self.pid = None

        self._logger = None
        self._is_setup = False

    @property
    def logger(self):
        if not self._logger:
            self._logger = logging.getLogger("PidFile")

        return self._logger

    def setup(self):
        if not self._is_setup:
            self.logger.debug("%r entering setup", self)
            if self.filename is None:
                self.pid = os.getpid()
                self.filename = self._make_filename()
                self._register_term_signal()

            # setup should only be performed once
            self._is_setup = True

    def _make_filename(self):
        pidname = self.pidname
        piddir = self.piddir
        if pidname is None:
            pidname = "%s.pid" % os.path.basename(sys.argv[0])
        if self.enforce_dotpid_postfix and not pidname.endswith(".pid"):
            pidname = "%s.pid" % pidname
        if piddir is None:
            if os.path.isdir(DEFAULT_PID_DIR) and self.force_tmpdir is False:
                piddir = DEFAULT_PID_DIR
            else:
                piddir = tempfile.gettempdir()

        if not os.path.isdir(piddir):
            os.makedirs(piddir)
        if not os.access(piddir, os.R_OK):
            raise IOError("Pid file directory '%s' cannot be read" % piddir)
        if not os.access(piddir, os.W_OK):
            raise IOError("Pid file directory '%s' cannot be written to" % piddir)

        filename = os.path.abspath(os.path.join(piddir, pidname))
        return filename

    def _register_term_signal(self):
        register_term_signal_handler = self.register_term_signal_handler
        if register_term_signal_handler == 'auto':
            if signal.getsignal(signal.SIGTERM) == signal.SIG_DFL:
                register_term_signal_handler = True
            else:
                register_term_signal_handler = False

        if callable(register_term_signal_handler):
            signal.signal(signal.SIGTERM, register_term_signal_handler)
        elif register_term_signal_handler:
            # Register TERM signal handler to make sure atexit runs on TERM signal
            def sigterm_noop_handler(*args, **kwargs):
                raise SystemExit(1)

            signal.signal(signal.SIGTERM, sigterm_noop_handler)

    def check(self):
        def inner_check(fh):
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

        self.setup()

        self.logger.debug("%r check pidfile: %s", self, self.filename)

        if self.fh is None:
            if self.filename and os.path.isfile(self.filename):
                with open(self.filename, "r") as fh:
                    inner_check(fh)
        else:
            inner_check(self.fh)

    def create(self):
        self.setup()

        self.logger.debug("%r create pidfile: %s", self, self.filename)
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
        self.logger.debug("%r closing pidfile: %s", self, self.filename)

        if not fh:
            fh = self.fh
        try:
            if fh is None:
                return
            fh.close()
        except IOError as exc:
            # ignore error when file was already closed
            if exc.errno != errno.EBADF:
                raise
        finally:
            if self.filename and os.path.isfile(self.filename) and cleanup:
                os.remove(self.filename)

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
        self.close()
