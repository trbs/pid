pid
===

.. image:: https://travis-ci.org/trbs/pid.svg?branch=master
    :target: https://travis-ci.org/trbs/pid

.. image:: https://coveralls.io/repos/trbs/pid/badge.png
    :target: https://coveralls.io/r/trbs/pid

.. image:: https://img.shields.io/pypi/v/pid.svg
    :target: https://pypi.python.org/pypi/pid/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/pid.svg
    :target: https://pypi.python.org/pypi/pid/
    :alt: Number of PyPI downloads

PidFile class featuring:

 - stale detection
 - pidfile locking (fcntl)
 - chmod (default is 0o644)
 - chown
 - custom exceptions

Context Manager, Daemons and Logging
------------------------------------

PidFile can be used as a context manager::

  from pid import PidFile
  import os

  with PidFile('foo') as p:
    print(p.pidname) # -> 'foo'
    print(p.piddir) # -> '/var/run' But you can modify it when initialize PidFile.
    print(os.listdir('/var/run')) # -> ['foo.pid']

  # pid file will delete after 'with' literal.

|

Logging to file is also possible when using PidFile with a daemon context manager
(e.g. `python-daemon <https://pypi.python.org/pypi/python-daemon/>`_). This requires some care in
handling the open files when the daemon starts to avoid closing them, which causes problems with the
logging. In particular, the open handlers should be preserved::

  import sys
  import logging
  import logging.config

  import daemon
  from pid impor PidFile

  logging.config.fileConfig(fname="logging.conf", disable_existing_loggers=False)
  log = logging.getLogger(__name__)

  PIDNAME = "/tmp/mydaemon.pid"

  def get_logging_handles(logger):
      handles = []
      for handler in logger.handlers:
          handles.append(handler.stream.fileno())
      if logger.parent:
          handles += get_logging_handles(logger.parent)
      return handles

  def daemonize():
    file_preserve = get_logging_handles(logging.root)
    pid_file = PidFile(pidname=PIDNAME)

    with daemon.DaemonContext(stdout=sys.stdout,
                              stderr=sys.stderr,
                              stdin=sys.stdin,
                              pidfile=_pid_file,
                              files_preserve=files_preserve):

      run_daemon_job()
    print("DONE!")

  if __name__ == "__main__":
    daemonize()

This assumes a `logging.conf` file has been created, see e.g. `basic tutorial
<https://docs.python.org/3/howto/logging.html#logging-basic-tutorial>`_ for logging.


Decorator
---------

PidFile can also be used a a decorator::

  from pid.decorator import pidfile
  
  @pidfile()
  def main():
    pass

  if __name__ == "__main__":
    main()


Exception Order
---------------

In default mode PidFile will try to acquire a file lock before anything else.
This means that normally you get a PidFileAlreadyLockedError instead of the
PidFileAlreadyRunningError when running a program twice.

If you just want to know if a program is already running its easiest to catch
just PidFileError since it will capture all possible PidFile exceptions.

Behaviour
---------

Changes in version 2.0.0 and going forward:

* pid is now friendly with daemon context managers such as
  `python-daemon <https://pypi.python.org/pypi/python-daemon/>`_ where
  the PidFile context manager is passed as a parameter. The
  new corrected behaviour will ensure the process environment is
  determined at the time of acquiring/checking the lock. Prior
  behaviour would determine the process environment when
  instancing the class which may result in incorrect determination
  of the PID in the case of a process forking after instancing
  PidFile.

\

* Cleanup of pidfile on termination is done using `atexit` module.
  The default SIGTERM handler doesn't cleanly exit and therefore
  the atexit registered functions will not execute. A custom
  handler which triggers the atexit registered functions for cleanup
  will override the default SIGTERM handler. If a prior signal handler
  has been configured, then it will not be overridden.
