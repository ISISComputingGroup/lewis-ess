|LeWIS System Tests|
=======
The system tests use the `Approval Tests Framework <https://approvaltests.com/>`__ to test a representative subset of
LeWIS's runtime functionality (i.e. not all of it) to give developers confidence that their changes do not break LeWIS
at the application level. The unit tests are responsible for checking everything works at a lower level.

To run the tests:

::

    $ pytest lewis_tests.py


