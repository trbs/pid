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

Context Manager
---------------

PidFile can be used as a context manager::

  from pid import PidFile
  import os

  with PidFile('foo') as p:
    print(p.pidname) # -> 'foo'
    print(p.piddir) # -> '/var/run' But you can modify it when initialize PidFile.
    print(os.listdir('/var/run')) # -> ['foo.pid']

  # pid file will delete after 'with' literal.

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
