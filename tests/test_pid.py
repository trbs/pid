import os
import os.path
import sys
import signal
import tempfile
import pytest
from contextlib import contextmanager
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

try:
    from subprocess import run
except ImportError:
    # python2 support
    from subprocess import call as run

import pid

pid.DEFAULT_PID_DIR = tempfile.gettempdir()

if sys.platform == "win32":
    # Fix backslashes on windows to properly execute "run" command
    pid.DEFAULT_PID_DIR = pid.DEFAULT_PID_DIR.replace("\\", "/")


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
    except Exception:
        raise
    else:
        raise AssertionError("Failed to throw exception of type(s) %s." % (", ".join(exc_type.__name__ for exc_type in exc_types),))


@contextmanager
def raising_windows_io_error():
    try:
        yield
    except IOError as exc:
        if exc.errno != 13:
            raise
    except Exception:
        raise
    else:
        raise AssertionError("Failed to throw exception")


def test_pid_class():
    pidfile = pid.PidFile()
    pidfile.create()
    pidfile.close()
    assert not os.path.exists(pidfile.filename)


def test_pid_context_manager():
    with pid.PidFile() as pidfile:
        pass

    assert not os.path.exists(pidfile.filename)


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def test_pid_pid():
    with pid.PidFile() as pidfile:
        pidnr = int(open(pidfile.filename, "r").readline().strip())
        assert pidnr == os.getpid(), "%s != %s" % (pidnr, os.getpid())
    assert not os.path.exists(pidfile.filename)


@pytest.mark.skipif(sys.platform != "win32", reason="only runs on windows")
def test_pid_pid_win32():
    def read_pidfile_data():
        return open(pidfile.filename, "r").readline().strip()

    with pid.PidFile() as pidfile:
        # On windows Python2 opens a file but reads an empty line from it
        # Python3 throws IOError(13, Access denied) instead, which we are catching with raising_windows_io_error()
        if sys.version_info.major < 3:
            pidtext = read_pidfile_data()
            assert pidtext == "", "Read '%s' from locked file on Windows with Python2" % (pidtext)
        else:
            with raising_windows_io_error():
                pidtext = read_pidfile_data()
    assert not os.path.exists(pidfile.filename)


def test_pid_custom_name():
    with pid.PidFile(pidname="testpidfile") as pidfile:
        pass
    assert not os.path.exists(pidfile.filename)


def test_pid_enforce_dotpid_postfix():
    with pid.PidFile(pidname="testpidfile", enforce_dotpid_postfix=False) as pidfile:
        assert not pidfile.filename.endswith(".pid")
    assert not os.path.exists(pidfile.filename)


def test_pid_force_tmpdir():
    with pid.PidFile(force_tmpdir=True) as pidfile:
        pass
    assert not os.path.exists(pidfile.filename)


def test_pid_custom_dir():
    with pid.PidFile(piddir=os.path.join(pid.DEFAULT_PID_DIR, "testpidfile.dir")) as pidfile:
        pass
    assert not os.path.exists(pidfile.filename)


def test_pid_piddir_exists_as_file():
    with tempfile.NamedTemporaryFile() as tmpfile:
        with raising(IOError):
            with pid.PidFile(piddir=tmpfile.name):
                pass


def test_pid_no_term_signal():
    def _noop(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, _noop)
    with pid.PidFile(register_term_signal_handler=False) as pidfile:
        assert signal.getsignal(signal.SIGTERM) is _noop
    assert not os.path.exists(pidfile.filename)


def test_pid_term_signal():
    def _noop(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, _noop)
    with pid.PidFile(register_term_signal_handler=True) as pidfile:
        assert signal.getsignal(signal.SIGTERM) is not _noop
    assert not os.path.exists(pidfile.filename)


def test_pid_force_register_term_signal_handler():
    def _noop(*args, **kwargs):
        pass

    def _custom_signal_func(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, _custom_signal_func)
    assert signal.getsignal(signal.SIGTERM) is _custom_signal_func
    with pid.PidFile(register_term_signal_handler=True) as pidfile:
        assert signal.getsignal(signal.SIGTERM) is not _custom_signal_func
    assert not os.path.exists(pidfile.filename)


def test_pid_supply_term_signal_handler():
    def _noop(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    with pid.PidFile(register_term_signal_handler=_noop) as pidfile:
        assert signal.getsignal(signal.SIGTERM) is _noop
    assert not os.path.exists(pidfile.filename)


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def test_pid_chmod():
    with pid.PidFile(chmod=0o600) as pidfile:
        pass
    assert not os.path.exists(pidfile.filename)


@pytest.mark.skipif(sys.platform != "win32", reason="only runs on windows")
def test_pid_chmod_win32():
    with raising(pid.PidFileConfigurationError):
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


def test_pid_already_locked_multi_process():
    pidname = "test_pid_already_locked_multi_process"
    piddir = pid.DEFAULT_PID_DIR
    with pid.PidFile(pidname=pidname, piddir=piddir) as _pid:
        s = """
import sys, pid
try:
    with pid.PidFile(pidname="%s", piddir="%s"):
        pass
except pid.PidFileAlreadyLockedError:
    sys.exit(123)
""" % (pidname, piddir)
        result = run([sys.executable, '-c', s])
        returncode = result if isinstance(result, int) else result.returncode
        assert returncode == 123
        assert os.path.exists(_pid.filename)
    assert not os.path.exists(_pid.filename)


def test_pid_two_locks_multi_process():
    with pid.PidFile() as _pid:
        s = """
import os, pid
with pid.PidFile("pytest2", piddir="%s") as _pid:
    assert os.path.exists(_pid.filename)
assert not os.path.exists(_pid.filename)
""" % pid.DEFAULT_PID_DIR
        result = run([sys.executable, '-c', s])
        returncode = result if isinstance(result, int) else result.returncode
        assert returncode == 0
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
    try:
        pidfile.fh.close()
    finally:
        pidfile.close()
    assert not os.path.exists(pidfile.filename)


def test_pid_multiplecreate():
    pidfile = pid.PidFile()
    pidfile.create()
    try:
        with raising(pid.PidFileAlreadyRunningError, pid.PidFileAlreadyLockedError):
            pidfile.create()
    finally:
        pidfile.close()
    assert not os.path.exists(pidfile.filename)


@pytest.mark.skipif(sys.platform == "win32", reason="os.getgid() does not exist on windows")
def test_pid_gid():
    gid = os.getgid()
    with pid.PidFile(gid=gid) as pidfile:
        pass
    assert not os.path.exists(pidfile.filename)


@pytest.mark.skipif(sys.platform != "win32", reason="only runs on windows")
def test_pid_gid_win32():
    gid = 123
    with raising(pid.PidFileConfigurationError):
        with pid.PidFile(gid=gid):
            pass


def test_pid_check_const_empty():
    pidfile = pid.PidFile()
    pidfile.setup()
    try:
        with open(pidfile.filename, "w") as f:
            f.write("\n")
        assert pidfile.check() == pid.PID_CHECK_EMPTY
    finally:
        pidfile.close(cleanup=True)
    assert not os.path.exists(pidfile.filename)


def test_pid_check_const_nofile():
    pidfile = pid.PidFile()
    assert pidfile.check() == pid.PID_CHECK_NOFILE


def test_pid_check_const_samepid():
    def check_const_samepid():
        with pid.PidFile(allow_samepid=True) as pidfile:
            assert pidfile.check() == pid.PID_CHECK_SAMEPID
        assert not os.path.exists(pidfile.filename)

    if sys.platform != "win32":
        check_const_samepid()
    else:
        with raising(pid.PidFileConfigurationError):
            check_const_samepid()


def test_pid_check_const_notrunning():
    def check_const_notrunning():
        with pid.PidFile() as pidfile:
            with open(pidfile.filename, "w") as f:
                # hope this does not clash
                f.write("999999999\n")
                f.flush()
                assert pidfile.check() == pid.PID_CHECK_NOTRUNNING
        assert not os.path.exists(pidfile.filename)

    if sys.platform != "win32":
        check_const_notrunning()
    else:
        with raising_windows_io_error():
            check_const_notrunning()


def test_pid_check_already_running():
    with pid.PidFile() as pidfile:
        pidfile2 = pid.PidFile()
        with raising(pid.PidFileAlreadyRunningError):
            pidfile2.check()
    assert not os.path.exists(pidfile.filename)


def test_pid_check_samepid_with_blocks():
    def check_samepid_with_blocks_separate_objects():
        with pid.PidFile(allow_samepid=True):
            with pid.PidFile(allow_samepid=True):
                pass

    def check_samepid_with_blocks_same_objects():
        pidfile = pid.PidFile(allow_samepid=True)
        with pidfile:
            with pidfile:
                pass

        assert not os.path.exists(pidfile.filename)

    if sys.platform != "win32":
        check_samepid_with_blocks_separate_objects()
    else:
        with raising(pid.PidFileConfigurationError):
            check_samepid_with_blocks_separate_objects()

    if sys.platform != "win32":
        check_samepid_with_blocks_same_objects()
    else:
        with raising(pid.PidFileConfigurationError):
            check_samepid_with_blocks_same_objects()


def test_pid_check_samepid():
    def check_samepid():
        pidfile = pid.PidFile(allow_samepid=True)

        try:
            pidfile.create()
            pidfile.create()
        finally:
            pidfile.close()

        assert not os.path.exists(pidfile.filename)

    if sys.platform != "win32":
        check_samepid()
    else:
        with raising(pid.PidFileConfigurationError):
            check_samepid()


@pytest.mark.skipif(sys.platform == "win32", reason="test not supported on win32")
@patch("os.getpid")
@patch("os.kill")
def test_pid_raises_already_running_when_samepid_and_two_different_pids(mock_getpid, mock_kill):
    pidfile_proc1 = pid.PidFile()
    pidfile_proc2 = pid.PidFile(allow_samepid=True)

    try:
        mock_getpid.return_value = 1
        pidfile_proc1.create()

        mock_getpid.return_value = 2
        with raising(pid.PidFileAlreadyRunningError):
            pidfile_proc2.create()

    finally:
        pidfile_proc1.close()
        pidfile_proc2.close()

    assert not os.path.exists(pidfile_proc1.filename)
    assert not os.path.exists(pidfile_proc2.filename)


def test_pid_default_term_signal():
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    with pid.PidFile() as pidfile:
        assert callable(signal.getsignal(signal.SIGTERM)) is True

    assert not os.path.exists(pidfile.filename)


def test_pid_ignore_term_signal():
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    with pid.PidFile() as pidfile:
        assert signal.getsignal(signal.SIGTERM) == signal.SIG_IGN

    assert not os.path.exists(pidfile.filename)


def test_pid_custom_term_signal():
    def _noop(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, _noop)

    with pid.PidFile() as pidfile:
        assert signal.getsignal(signal.SIGTERM) == _noop

    assert not os.path.exists(pidfile.filename)


# def test_pid_unknown_term_signal():
#     # Not sure how to properly test this when signal.getsignal returns None
#     #  - perhaps by writing a C extension which might get ugly
#     #
#     with pid.PidFile():
#         assert signal.getsignal(signal.SIGTERM) == None


def test_double_close_race_condition():
    # https://github.com/trbs/pid/issues/22
    pidfile1 = pid.PidFile()
    pidfile2 = pid.PidFile()

    try:
        pidfile1.create()
        assert os.path.exists(pidfile1.filename)
    finally:
        pidfile1.close()
        assert not os.path.exists(pidfile1.filename)

    try:
        pidfile2.create()
        assert os.path.exists(pidfile2.filename)

        # simulate calling atexit in process of pidfile1
        pidfile1.close()

        assert os.path.exists(pidfile2.filename)
    finally:
        pidfile2.close()

    assert not os.path.exists(pidfile1.filename)
    assert not os.path.exists(pidfile2.filename)


@pytest.mark.skipif(sys.version_info < (3, 5), reason="requires python3.5 or higher")
@patch("atexit.register", autospec=True)
def test_register_atexit_false(mock_atexit_register):
    with pid.PidFile(register_atexit=False):
        mock_atexit_register.assert_not_called()


@patch("atexit.register", autospec=True)
def test_register_atexit_true(mock_atexit_register):
    with pid.PidFile(register_atexit=True) as pidfile:
        mock_atexit_register.assert_called_once_with(pidfile.close)
