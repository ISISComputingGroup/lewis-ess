Usage with Docker
=================

Docker Engine must be installed in order to run the Lewis Docker
image. Detailed installation instructions for various OSes may be found
`here <https://docs.docker.com/engine/installation/>`__.

On OSX and Windows, we recommend simply installing the `Docker
Toolbox <https://www.docker.com/products/docker-toolbox>`__. It contains
everything you need and is (currently) more stable than the "Docker for
Windows/Mac" beta versions.

On Linux, to avoid manually copy-pasting your way through the rather
detailed instructions linked to above, you can let the Docker
installation script take care of everything for you:

::

    $ curl -fsSL https://get.docker.com/ | sh

Once Docker is installed, Lewis can be run using the following
general format:

::

    $ docker run -it [docker args] dmscid/lewis [device] [arguments]

For example, to simulate a Linkam T95 device and expose it via the
TCP Stream **p**\ rotocol:

::

    $ docker run -it dmscid/lewis linkam_t95 -p stream

To change the rate at which simulation cycles are calculated, increase
or decrease the cycle delay, via the ``-c`` or ``--cycle-delay`` option.
Smaller values mean more cycles per second, 0 means fastest possible
speed.

::

    $ docker run -it dmscid/lewis linkam_t95 -p stream -c 0.05

For long running devices it might be useful to speed up the simulation
using the ``-e`` or ``--speed`` parameter, which is a factor by which
actual time is multiplied to determine the simulated time in each
simulation cycle. To run a simulation 10 times faster:

::

    $ docker run -it dmscid/lewis linkam_t95 -p stream -e 10

Details about parameters for the various adapters, and differences
between OSes are covered in the "Adapter Specifics" sections.

It's possible to use the Docker container to run devices that reside
on the host using a mounted volume. This is particularly useful
for developing and running EPICS-based devices without having to
install any dependencies on the host besides Docker. This way also removes
the need to rebuild the Lewis image continuously whenever a change is made
to the device.

Assuming a package with devices called ``devices`` resides on the host
under the directory ``/some/host/path`` that contains a device named
``epics_device``, it can be started like this:

::

    $ docker run -it -v /some/host/path:/external dmscid/lewis -a /external -k devices epics_device

This makes the ``/some/host/path``-directory available as ``/external`` in
the container. Specifying ``-a /external`` makes the device modules
residing in ``/external/devices`` available so that it can be found by Lewis
when the ``-k``-option is used.
