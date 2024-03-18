# Release 1.2
After releasing 1.1.0 and 1.1.1, we decided to move to a more reproducible testing workflow that
is operating closer to the packages that are released in the end. This only affects developers
who work on the Lewis code base. In addition, `lewis.adapters.epics` was improved a bit
with better error messages and more reasonable PV update frequencies. The ``lewis-control``
server now runs in its own thread, which has made it more responsive.

## New Features
- `StreamInterface` has been improved to support a ``readtimeout`` attribute which is analogous
   to the ReadTimeout system variable in Protocol files. The value of ``readtimeout`` determines how
   many milliseconds to wait for more input, once we have started receiving data for a command. Under
   normal circumstances, this timeout being triggered is an error and causes the incoming buffer to be
   flushed and a ``handle_error`` call in the device interface. However, if the ``in_terminator``
   attribute is empty, this timeout is treated as the command terminator instead.

   ``readtimeout`` defaults to 100 (ms).
   ``readtimeout = 0`` disables this feature entirely.

   The effective resolution is currently limited 10 ms increments due to the fixed adapter cycle rate.

- The `lewis.core.control_server.ControlServer` is now running in its own thread, separate
   from the simulation. As a result, ``lewis-control`` and the Python Control API are now much more
   responsive. This is because requests are processed asynchronously and, therefore, multiple
   requests can be processed per simulation cycle.

## Bugfixes and other improvements
- Error messages in the binding step of :class:`PV` have been improved. It is now easier to find
   the source of common problems (missing properties, spelling errors).

- PVs are only updated if the underlying value has actually changed. Changes to metadata are processed
   and logged separately. This leads to cleaner logs even at small values for ``poll_interval``.

- Using ``yaml.safe_load`` instead of ``yaml.load`` as a security precaution.


## Changes for developers
- The ``lewis.py`` and ``lewis-control.py`` files have been removed, because especially the former
   created some problems with the new package structure by interfering with the tests and docs-
   generation.

   For using Lewis when it's installed through pip, this does not change anything, but for
   development of the Lewis framework (not of devices), it is now strongly recommended to do so
   in a separate virtual environment, installing Lewis from source as an editable package. Details
   on this can be found in the updated `developer_guide`.

- Tests are now run with pytest instead of nose. In addition, a tox configuration has been
   added for more reproducible tests with different interpreters.

   The first run may take a bit longer, since each step is run in a fresh virtual environment that tox
   creates automatically.

   To run specific tests, for example to verify that building the docs works, use the ``-e`` flag
   of tox

   To see all tests that are available, including a short description, use ``tox -l -v``.
