pid
===

.. image:: https://travis-ci.org/trbs/pid.svg?branch=master
    :target: https://travis-ci.org/trbs/pid

.. image:: https://coveralls.io/repos/trbs/pid/badge.png
    :target: https://coveralls.io/r/trbs/pid


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
  
  with PidFile():
    do_something()


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
