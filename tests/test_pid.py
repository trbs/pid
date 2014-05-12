from contextlib import contextmanager
from nose.tools import raises
import pid


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
        raise AssertionError("Failed to throw exception of type(s) %s." % (
                ", ".join(exc_type.__name__ for exc_type in exc_types),))


def test_pid_class():
    pidfile = pid.PidFile()
    pidfile.create()
    pidfile.close()

def test_pid_context_manager():
    with pid.PidFile() as pidfile:
        pass

def test_pid_custom_name():
    with pid.PidFile(pidname="testpidfile") as pidfile:
        pass

def test_pid_custom_dir():
    with pid.PidFile(piddir="/tmp") as pidfile:
        pass

def test_pid_no_term_signal():
    with pid.PidFile(register_term_signal_handler=False) as pidfile:
        pass

def test_pid_chmod():
    with pid.PidFile(chmod=0o600) as pidfile:
        pass

def test_pid_already_locked():
    with pid.PidFile() as pidfile1:
        with raising(pid.PidFileAlreadyLockedError):
            with pid.PidFile() as pidfile2:
                pass

def test_pid_already_locked_custom_name():
    with pid.PidFile(pidname="testpidfile") as pidfile1:
        with raising(pid.PidFileAlreadyLockedError):
            with pid.PidFile(pidname="testpidfile") as pidfile2:
                pass

def test_pid_already_running():
    with pid.PidFile(lock_pidfile=False) as pidfile1:
        with raising(pid.PidFileAlreadyRunningError):
            with pid.PidFile(lock_pidfile=False) as pidfile2:
                pass

def test_pid_already_running_custom_name():
    with pid.PidFile(lock_pidfile=False, pidname="testpidfile") as pidfile1:
        with raising(pid.PidFileAlreadyRunningError):
            with pid.PidFile(lock_pidfile=False, pidname="testpidfile") as pidfile2:
                pass
