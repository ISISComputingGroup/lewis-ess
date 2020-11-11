Usage with Python
=================

To use Lewis directly via Python you must first install its dependencies:

-  Python 2.7+ or 3.4+
-  PIP 8.1+

On most linux systems these can be installed via the distribution's package manager.

.. _virtual_environments:

Virtual environments
--------------------

The two sections below describe installation and use of Lewis using two different methods,
installation via pip and from source. For both methods we recommend setting up a virtual
environment, which provide a great way of keeping packages outside the system directories and
at the same time have more control over the environment a script is running in.

To setup a virtual environment for Lewis:

::

    $ python -m venv lewis-env

To actually begin using the environment, a script file containing environment variables and so on
needs to be sourced:

::

    $ source lewis-env/bin/activate

By default this modifies the terminal display, showing the name of the environment. To leave the
environment and go back to the "normal" terminal type the following:

::

    (lewis-env)$ deactivate

The packages that are installed in the virtual environment are only available when it has been
activated. Inside the virtual environment you do not need the ``--user``-flag of pip, because
the directories the packages are installed to are in a location that is writable with your
normal user account.

There are some packages to make managing multiple virtual environments easier and some IDEs also
have builtin support.


Installation via pip
--------------------

Lewis is available on the `Python Package Index <https://pypi.python.org/pypi/lewis>`__. That means
it can be installed using pip:

::

    $ pip install lewis

This will install lewis along with its dependencies. If you would like to use EPICS based devices
and have a working EPICS environment on your machine, you can install it like this to get the
additional required dependencies:

::

    $ pip install lewis[epics]

This will install two scripts in the path, ``lewis`` and ``lewis-control``. Both scripts provide
command line help:

::

    $ lewis --help
    $ lewis-control --help

To list available devices, just type ``lewis`` in the command line, a list of devices that are
available for simulation will be printed.

All following sections of this user manual assume that Lewis has been installed via pip and that
the ``lewis`` command is available.

Installation from source
------------------------

Clone the repository in a location of your choice, we recommend that you do it inside a virtual
environment (see above) so that you can keep track of the dependencies:

::

    $ git clone https://github.com/ess-dmsc/lewis.git

If you do not have `git <https://git-scm.com/>`__ available, you can
also download this repository as an archive and unpack it somewhere. A
few additional dependencies must be installed. This can be done through
pip in the top level directory of Lewis, which contains the ``setup.py``-file:

::

    $ pip install .

.. note::

    There are a few optional dependencies for certain adapter types. Currently the only
    optional dependency is ``pcaspy`` for using devices with an EPICS interface, it requires a
    working installation of EPICS base. Please refer to the `installation instructions
    <https://pcaspy.readthedocs.io/en/latest/installation.html>`__ of the module.
    To include ``pcaspy`` in the installation of dependencies, use:

    ::

        $ pip install ".[epics]"

If you also want to develop Lewis, the workflow is a bit different. Please refer to the
:ref:`developer_guide` for details.

If you want to use the EPICS adapter, you will also need to configure a few more
EPICS environment variables correctly. If you only want to communicate
using EPICS locally via the loopback device, you can configure it like
this:

::

    $ export EPICS_CA_AUTO_ADDR_LIST=NO
    $ export EPICS_CA_ADDR_LIST=localhost
    $ export EPICS_CAS_INTF_ADDR_LIST=localhost

Once all dependencies and requirements are satisfied, Lewis can be
run using the following general format (from inside the Lewis
directory):

::

    $ python -m lewis device_name [arguments]

You can then run Lewis as follows (from within the lewis
directory):

::

    $ python -m lewis chopper -p epics

Details about parameters for the various adapters, and differences
between OSes are covered in the "Adapter Specifics" sections.

If you decided to install Lewis this way, please be aware that the ``lewis`` and ``lewis-control``
calls in the other parts of the guide have to be replaced with ``python lewis.py``.

Running from source
-------------------

Lewis can be run directly from source. First it is necessary to install the basic requirements:

::

    $ pip install -r requirements.txt

If you would like to use EPICS based devices
and have a working EPICS environment on your machine then it is necessary to install ``pcaspy`` like so:

    ::

        $ pip install pcaspy


There are Python scripts for running both ``lewis`` and ``lewis-control`` in the top-level scripts directory.
These scripts work exactly the same as when Lewis is installed via pip (see above). For example:

::

    $ python scripts/lewis.py --help
    $ python scripts/lewis-control.py --help

