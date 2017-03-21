Adapter Specifics
=================

EPICS Adapter Specifics
-----------------------

The EPICS adapter takes only one optional argument:

-  ``prefix``: This string is prefixed to all PV names. Defaults to empty / no prefix.

Arguments meant for the adapter can be specified with the adapter options.
For example:

::

    $ docker run -itd dmscid/lewis chopper -p "epics: {prefix: 'SIM1:'}"
    $ python lewis.py chopper --adapter-options "epics: {prefix: 'SIM2:'}"

When using the EPICS adapter within a docker container, the PV will be
served on the docker0 network (172.17.0.0/16).

On Linux, this means that ``EPICS_CA_ADDR_LIST`` must include this
networks broadcast address:

::

    $ export EPICS_CA_AUTO_ADDR_LIST=NO
    $ export EPICS_CA_ADDR_LIST=172.17.255.255
    $ export EPICS_CAS_INTF_ADDR_LIST=localhost

On Windows and OSX, the docker0 network is inside of a virtual machine.
To communicate with it, an EPICS Gateway to forward EPICS requests and
responses is required. We provide an `EPICS Gateway Docker
image <https://hub.docker.com/r/dmscid/epics-gateway/>`__ that can be
used to do this relatively easily. Detailed instructions can be found on
the linked page.

Stream Adapter Specifics
------------------------

The TCP Stream adapter has the following optional arguments:

-  ``bind_address``: Address of network adapter to listen on.
   Defaults to "0.0.0.0" (all network adapters).
-  ``port``: Port to listen for connections on. Defaults to 9999.
-  ``telnet_mode``: When True, overrides both in and out terminators
   to CRNL for telnet compatibility. Defaults to False.

Arguments meant for the adapter can be specified with the adapter options.
For example:

::

    $ docker run -itd dmscid/lewis linkam_t95 --adapter-options "stream: {port: 1234}"
    $ python lewis.py linkam_t95 -p "stream: {bind_address: localhost, port: 1234}"

When using Lewis via Docker on Windows and OSX, the container will be
running inside a virtual machine, and so the port it is listening on
will be on a network inside the VM. To connect to it from outside of the
VM, an additional argument must be passed to Docker to forward the port:

::

    $ docker run -it -p 1234:4321 dmscid/lewis linkam_t95 -p "stream: {port: 4321}"
    $ telnet 192.168.99.100 1234

This port option links port 4321 on the container to port 1234 on
the VM network adapter. It must appear after ``docker run`` and before
``dmscid/lewis``. This allows us to connect to the container from
outside of the VM, in this case using Telnet. The ``192.168.99.100`` IP
is the IP of the VM on the bridge network between the host and the VM.
VirtualBox will typically use this IP when available, but it may be
different on your system.
