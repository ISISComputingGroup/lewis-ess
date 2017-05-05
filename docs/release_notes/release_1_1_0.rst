:orphan:

Release 1.1.0
=============

This release is currently in progress.

New features
------------

The control client, lewis-control, now provides a version argument via ``--version`` or ``-v``. 

::

   $ lewis-control -v 

Bug fixes and other improvements
--------------------------------

 - Lewis now has a logo. It is based on  a state machine with one state that is entered and
   repeated infinitely - like the simulation cycles in Lewis.

   .. image:: /resources/logo/lewis-logo.png

   For low-resolution images or settings with little space, there is also a simplified version:

   .. image:: /resources/logo/lewis-logo-simple.png

   The logo was made using `inkscape`_, the font in the logo is `Rubik`_. The two PNGs and
   also the SVGs are in the `source repository`_, feel free to include them in presentations,
   posters.

Upgrade guide
-------------

 - Due to a change to how Adapters and Devices work together, device interfaces are not
   inheriting from Adapter-classes anymore. Instead, there are dedicated Interface classes.
   They are located in the same modules as the Adapters, so only small changes are necessary:

   Old:
   .. sourcecode:: Python

       from lewis.adapters.stream import StreamAdapter, Cmd

       class DeviceInterface(StreamAdapter):
           pass

   New:
   .. sourcecode:: Python

       from lewis.adapters.stream import StreamInterface, Cmd

       class DeviceInterface(StreamInterface):
           pass

   The same goes for ``EpicsAdapter`` and ``ModbusAdapter``, which must be modified to
   ``EpicsInterface`` and ``ModbusInterface`` respectively.

.. _source repository: https://github.com/DMSC-Instrument-Data/lewis/docs/resources/logo
.. _Rubik: https://github.com/googlefonts/rubik
.. _inkscape: https://inkscape.org/
