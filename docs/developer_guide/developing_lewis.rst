Developing Lewis
================

Begin by checking-out the source from GitHub:

::

    (lewis-dev)$ git clone https://github.com/ess-dmsc/lewis.git

To develop Lewis, it is strongly recommended to work in a dedicated virtual environment, otherwise
it is not possible to have another version of Lewis installed system wide in parallel. See
the :ref:`virtual_environments` section for a very quick introduction into creating and
activating a virtual environment.

With the virtual environment activated, Lewis can be installed as an editable package:

::

    (lewis-dev)$ cd lewis
    (lewis-dev)$ python -m pip install ".[dev]"

Now the Lewis package that resides in ``lewis`` can be modified, while it is still treated like a
normal package that has been installed via ``pip``.

Alternatively, Lewis can be run from source. For this it is necessary to install the requirements first:

::

    (lewis-dev)$ cd lewis
    (lewis-dev)$ python -m pip install -r requirements-dev.txt

Either way, to make sure that everything is working as
intended, run the unit tests and check for pep8 errors, as well as build the documentation:

::

    (lewis-dev)$ pytest test
    (lewis-dev)$ flake8 setup.py lewis scripts system-tests test
    (lewis-dev)$ sphinx-build -W -b html docs/ docs/_build/html

There are also system-tests that (partially) test Lewis from the application/run-time level. These tests are based on
the `Approval Tests Framework <https://approvaltests.com/>`__ which works by comparing a program's standard output
against a "golden master" - if the output doesn't match then the tests fail.
For ``lewis`` and ``lewis-control`` the tests check that the programs work together correctly. For example: if a value
on a simulated device in ``lewis`` is changed via ``lewis-control``` then by querying the status of the device the
values can be compared against the expected status (the "golden master"). The tests can be run like so:

::

    (lewis-dev)$ pytest system_tests\lewis_tests.py

It is good practice to run these tests regularly during development and, also, look for opportunities to add
more tests. The tests will also be run via Travis CI.

A more comprehensive way of running all tests is to use ``tox``, which creates fresh virtual
environments for all of these tasks:

::

    (lewis-dev)$ tox

The advantage of tox is that it generates a source package from the source tree and installs
it in the virtual environments that it creates, testing closer to the thing that is actually
installed in the end. Running all the verification steps this way takes a bit longer, so during
development it might be more desirable to just run the components that are necessary.

Before starting development it is important to install the pre-commit hooks, so that formatting and ``flake8`` checks
are performed before code is committed:

::

    (lewis-dev)$ pre-commit install

To test that the hooks are installed correctly and to run them manually use the following command:

::

   (lewis-dev)$ pre-commit run --all-files

Development should happen in a separate branch. If the work is related to a specific issue,
it is good practice to include the issue number in the branch name, along with a short
summary of a few words, for example:

::

    (lewis-dev)$ git checkout -b 123_enhance_logic_flow

It's also good practice to push the branch back to github from time to time, so that other
members of the development team can see what's going on (even before a pull request is opened):

::

    (lewis-dev)$ git push origin 123_enhance_logic_flow

During development it is good practice to regularly test that changes do not break existing
or new tests. Before opening a pull request on github (which will run all the tests again
under different Python environments via Travis CI), it is recommended to run tox one last time
locally, as that resembles the conditions in the CI environment quite closely.


