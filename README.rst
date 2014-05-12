pid
===

.. image:: https://travis-ci.org/trbs/pid.svg?branch=master
    :target: https://travis-ci.org/trbs/pid

PidFile class featuring:

 - stale detection
 - pidfile locking (fcntl)
 - chmod (default is 0o644)
 - chown
 - custom exceptions

Context Manager
---------------

PidFile can be used as a context manager::

  with PidFile():
    do_something()


Exception Order
---------------

In default mode PidFile will try to acquire a file lock before anything else.
This means that normally you get a PidFileAlreadyLockedError instead of the
PidFileAlreadyRunningError when running a program twice.

If you just want to know if a program is already running its easiest to use
just PidFileError since it will capture all possible PidFile exceptions.

