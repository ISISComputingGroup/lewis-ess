:orphan:

Release 1.1.0
=============

This release is currently in progress.

New features
------------

 - It is now possible to have devices with more than one communication interface. The `-p`-option
   can be supplied multiple times:

   ::

      $ lewis some_device -p protocol1 -p protocol2

   When no ``-p`` option is specified, the script behaves as before (use default protocol if
   possible or produce an error message). To start a simulation without any device communication,
   use the new ``-n``/``--no-interface`` option:

   ::

      $ lewis some_device -n

   It is not possible to use both ``-p`` and ``-n`` at the same time, this results in an error
   message.

   The ``epics_device`` example has been renamed to ``dual_device`` and extended to include a
   second interface definition, so it exposes the device state via two different protocols:

   ::

      $ lewis -k lewis.examples dual_device -p epics -p stream

 - The control client, lewis-control, now provides a version argument via ``--version`` or ``-v``.

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

 - Adapters now run in a different thread than the simulation itself. The consequence of this is
   that slow network communication or expensive computations in the device do not influence
   one another anymore. Otherwise, communication still works exactly like in previous versions.

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
