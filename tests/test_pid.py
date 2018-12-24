import os
import os.path
import signal
from contextlib import contextmanager
from mock import patch

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
    except Exception:
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
        try:
            file = open(pidfile.filename, "r")
            pidnr = int(file.readline().strip())
            assert pidnr == os.getpid(), "%s != %s" % (pidnr, os.getpid())
        except IOError as exc:
            if exc.errno == 13:
                file.close()
                pass
            else:
                raise
        finally:
            file.close()


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


def test_pid_force_register_term_signal_handler():
    def _noop(*args, **kwargs):
        pass

    def _custom_signal_func(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, _custom_signal_func)
    assert signal.getsignal(signal.SIGTERM) is _custom_signal_func
    with pid.PidFile(register_term_signal_handler=True):
        assert signal.getsignal(signal.SIGTERM) is not _custom_signal_func


def test_pid_supply_term_signal_handler():
    def _noop(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    with pid.PidFile(register_term_signal_handler=_noop):
        assert signal.getsignal(signal.SIGTERM) is _noop


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
    try:
        pidfile.fh.close()
    finally:
        pidfile.close()


def test_pid_multiplecreate():
    pidfile = pid.PidFile()
    pidfile.create()
    try:
        with raising(pid.PidFileAlreadyRunningError, pid.PidFileAlreadyLockedError):
            pidfile.create()
    finally:
        pidfile.close()


def test_pid_gid():
    # os.getgid() does not exist on windows
    if os.name == "posix":
        gid = os.getgid()
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
        pidfile.close()


def test_pid_check_const_nofile():
    pidfile = pid.PidFile()
    assert pidfile.check() == pid.PID_CHECK_NOFILE


def test_pid_check_const_samepid():
    if os.name == "posix":
        with pid.PidFile(allow_samepid=True) as pidfile:
            assert pidfile.check() == pid.PID_CHECK_SAMEPID
    else:
        with raising(pid.SamePidFileNotSupported):
            with pid.PidFile(allow_samepid=True) as pidfile:
                assert pidfile.check() == pid.PID_CHECK_SAMEPID


def test_pid_check_const_notrunning():
    with pid.PidFile() as pidfile:
        try:
            with open(pidfile.filename, "w") as f:
                # hope this does not clash
                f.write("999999999\n")
                f.flush()
                assert pidfile.check() == pid.PID_CHECK_NOTRUNNING
        except IOError as exc:
            if exc.errno != 13:
                raise


def test_pid_check_already_running():
    with pid.PidFile():
        pidfile2 = pid.PidFile()
        with raising(pid.PidFileAlreadyRunningError):
            pidfile2.check()


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

    if os.name == "posix":
        check_samepid_with_blocks_separate_objects()
    else:
        with raising(pid.SamePidFileNotSupported):
            check_samepid_with_blocks_separate_objects()

    if os.name == "posix":
        check_samepid_with_blocks_same_objects()
    else:
        with raising(pid.SamePidFileNotSupported):
            check_samepid_with_blocks_same_objects()


def test_pid_check_samepid():
    def check_samepid():
        pidfile = pid.PidFile(allow_samepid=True)
        try:
            pidfile.create()
            pidfile.create()
        finally:
            pidfile.close()

    if os.name == "posix":
        check_samepid()
    else:
        with raising(pid.SamePidFileNotSupported):
            check_samepid()


def test_pid_check_samepid_two_processes():
    def check_samepid_two_processes():
        pidfile_proc1 = pid.PidFile()
        pidfile_proc2 = pid.PidFile(allow_samepid=True)

        try:
            with patch('pid.os.getpid') as mgetpid:
                mgetpid.return_value = 1
                pidfile_proc1.create()

                mgetpid.return_value = 2
                with raising(pid.PidFileAlreadyRunningError, pid.PidFileAlreadyLockedError):
                    pidfile_proc2.create()
        finally:
            pidfile_proc1.close()
            pidfile_proc2.close()

    if os.name == "posix":
        check_samepid_two_processes()
    else:
        with raising(pid.SamePidFileNotSupported):
            check_samepid_two_processes()


def test_pid_default_term_signal():
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    with pid.PidFile():
        assert callable(signal.getsignal(signal.SIGTERM)) is True


def test_pid_ignore_term_signal():
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    with pid.PidFile():
        assert signal.getsignal(signal.SIGTERM) == signal.SIG_IGN


def test_pid_custom_term_signal():
    def _noop(*args, **kwargs):
        pass

    signal.signal(signal.SIGTERM, _noop)

    with pid.PidFile():
        assert signal.getsignal(signal.SIGTERM) == _noop


# def test_pid_unknown_term_signal():
#     # Not sure how to properly test this when signal.getsignal returns None
#     #  - perhaps by writing a C extension which might get ugly
#     #
#     with pid.PidFile():
#         assert signal.getsignal(signal.SIGTERM) == None
