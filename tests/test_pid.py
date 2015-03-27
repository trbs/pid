import os
import os.path
import signal
from contextlib import contextmanager

import pid

pid.DEFAULT_PID_DIR = "/tmp"


# https://code.google.com/p/python-nose/issues/detail?id=175
@contextmanager
def raising(*exc_types):
    """
    A context manager to ensure that an exception of a given list of
    types is thrown.

    Instead of::

      @nose.tools.raises(ValueError)
      def test_that_raises():
        # ... lengthy setup
        raise ValueError

    you can write::

      def test_that_raises_at_the_end():
        # ... lengthy setup
        with raising(ValueError):
          raise ValueError

    to make the scope for catching exceptions as small as possible.
    """
    try:
        yield
    except exc_types:
        pass
    except:
        raise
    else:
        raise AssertionError("Failed to throw exception of type(s) %s." % (", ".join(exc_type.__name__ for exc_type in exc_types),))


def test_pid_class():
    pidfile = pid.PidFile()
    pidfile.create()
    pidfile.close()


def test_pid_context_manager():
    with pid.PidFile():
        pass


def test_pid_pid():
    with pid.PidFile() as pidfile:
        pidnr = int(open(pidfile.filename, "r").readline().strip())
        assert pidnr == os.getpid(), "%s != %s" % (pidnr, os.getpid())


def test_pid_custom_name():
    with pid.PidFile(pidname="testpidfile"):
        pass


def test_pid_enforce_dotpid_postfix():
    with pid.PidFile(pidname="testpidfile", enforce_dotpid_postfix=False) as pidfile:
        assert not pidfile.filename.endswith(".pid")


def test_pid_force_tmpdir():
    with pid.PidFile(force_tmpdir=True):
        pass


def test_pid_custom_dir():
    with pid.PidFile(piddir="/tmp/testpidfile.dir/"):
        pass


def test_pid_no_term_signal():
    def _noop(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, _noop)
    with pid.PidFile(register_term_signal_handler=False):
        assert signal.getsignal(signal.SIGTERM) is _noop


def test_pid_term_signal():
    def _noop(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, _noop)
    with pid.PidFile(register_term_signal_handler=True):
        assert signal.getsignal(signal.SIGTERM) is not _noop


def test_pid_custom_term_signal():
    def _noop(*args, **kwargs):
        pass

    def _custom_signal_func(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, _custom_signal_func)
    assert signal.getsignal(signal.SIGTERM) is _custom_signal_func
    with pid.PidFile(register_term_signal_handler=True):
        assert signal.getsignal(signal.SIGTERM) is not _custom_signal_func


def test_pid_chmod():
    with pid.PidFile(chmod=0o600):
        pass


def test_pid_already_locked():
    with pid.PidFile() as _pid:
        with raising(pid.PidFileAlreadyLockedError):
            with pid.PidFile():
                pass
        assert os.path.exists(_pid.filename)
    assert not os.path.exists(_pid.filename)


def test_pid_already_locked_custom_name():
    with pid.PidFile(pidname="testpidfile") as _pid:
        with raising(pid.PidFileAlreadyLockedError):
            with pid.PidFile(pidname="testpidfile"):
                pass
        assert os.path.exists(_pid.filename)
    assert not os.path.exists(_pid.filename)


def test_pid_already_running():
    with pid.PidFile(lock_pidfile=False) as _pid:
        with raising(pid.PidFileAlreadyRunningError):
            with pid.PidFile(lock_pidfile=False):
                pass
        assert os.path.exists(_pid.filename)
    assert not os.path.exists(_pid.filename)


def test_pid_already_running_custom_name():
    with pid.PidFile(lock_pidfile=False, pidname="testpidfile") as _pid:
        with raising(pid.PidFileAlreadyRunningError):
            with pid.PidFile(lock_pidfile=False, pidname="testpidfile"):
                pass
        assert os.path.exists(_pid.filename)
    assert not os.path.exists(_pid.filename)


def test_pid_decorator():
    from pid.decorator import pidfile

    @pidfile()
    def test_decorator():
        pass

    test_decorator()


def test_pid_decorator_already_locked():
    from pid.decorator import pidfile

    @pidfile("testpiddecorator")
    def test_decorator():
        with raising(pid.PidFileAlreadyLockedError):
            @pidfile("testpiddecorator")
            def test_decorator2():
                pass
            test_decorator2()

    test_decorator()


def test_pid_already_closed():
    pidfile = pid.PidFile()
    pidfile.create()
    pidfile.fh.close()
    pidfile.close()


# def test_pid_gid():
#     import grp
#     gid = grp.getgrnam("nobody").gr_gid
#     pidfile = pid.PidFile(gid=gid)
#     pidfile.create()
#     pidfile.close()


def test_pid_check_already_running():
    with pid.PidFile():
        pidfile2 = pid.PidFile()
        with raising(pid.PidFileAlreadyRunningError):
            pidfile2.check()
