Release 1.1.2
=============

After releasing 1.1.0 and 1.1.1, we decided to move to a more reproducible testing workflow that
is operating closer to the packages that are released in the end. This only affects developers
who work on the Lewis code base. In addition, :mod:`lewis.adapters.epics` was improved a bit
with better error messages and more reasonable PV update frequencies.

Bugfixes and other improvements
-------------------------------
 - Error messages in the binding step of :class:`PV` have been improved. It is now easier to find
   the source of common problems (missing properties, spelling errors).
 
 - PVs are only updated if the underlying value has actually changed. Changes to metadata are processed
   and logged separately. This leads to cleaner logs even at small values for ``poll_interval``.

Changes for developers
----------------------
 - The ``lewis.py`` and ``lewis-control.py`` files have been removed, because especially the former
   created some problems with the new package structure by interfering with the tests and docs-
   generation.

   For using Lewis when it's installed through pip, this does not change anything, but for
   development of the Lewis framework (not of devices), it is now strongly recommended to do so
   in a separate virtual environment, installing Lewis from source as an editable package. Details
   on this can be found in the updated :ref:`developer_guide`.

 - Tests are now run with pytest_ instead of nose_. In addition, a tox_ configuration has been
   added for more reproducible tests with different interpreters. To run all tests:

   ::

      $ tox

   The first run may take a bit longer, since each step is run in a fresh virtualenv that tox
   creates automatically.

   To run specific tests, for example to verify that building the docs works, use the ``-e`` flag
   of tox:

   ::

      $ tox -e docs

   To see all tests that are available, including a short description, use ``tox -l -v``.


.. _pytest: https://docs.pytest.org/en/latest/
.. _nose: http://nose.readthedocs.io/en/latest/
.. _tox: https://tox.readthedocs.io/en/latest/
