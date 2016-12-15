Usage with Python
=================

To use Lewis directly via Python you must first install its
dependencies:

-  Python 2.7+ or 3.4+
-  PIP 8.1+

Clone the repository in a location of your choice:

::

    $ git clone https://github.com/DMSC-Instrument-Data/lewis.git

If you do not have `git <https://git-scm.com/>`__ available, you can
also download this repository as an archive and unpack it somewhere. A
few additional dependencies must be installed. This can be done through
pip via the requirements.txt file:

::

    $ pip install -r requirements.txt

**NOTE:** There are a few optional dependencies for certain adapter types. These are commented
out in the ``requirements.txt``-file and have to be explicitly enabled. Currently the only optional
dependency is ``pcaspy`` for using devices with an EPICS interface, it requires a working
installation of EPICS base. Please refer to the `installation instructions
<https://pcaspy.readthedocs.io/en/latest/installation.html>`__ of the module.


If you also want to run Lewis' unit tests, you may also install the
development dependencies:

::

    $ pip install -r requirements-dev.txt

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

    $ python lewis.py [lewis args] [-- [adapter args]]

You can then run Lewis as follows (from within the lewis
directory):

::

    $ python lewis.py -p epics chopper

Details about parameters for the various adapters, and differences
between OSes are covered in the "Adapter Specifics" sections.
