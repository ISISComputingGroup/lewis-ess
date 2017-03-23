:orphan:

Release 1.0.3
=============

This release is currently in progress.

Command line interface change
-----------------------------

The way options are passed to the adapters has changed completely, the functionality has been
merged into the ``-p``-argument, which has a new long version now, ``--adapter-options``.

For the default adapter options, it is still possible to use the ``lewis``-command with ``-p``
in the same way as before:

::

   $ lewis -p stream linkam_t95

To supply options, such as the address and port to bind to, the argument accepts an extended
dictionary syntax now:

::

   $ lewis linkam_t95 -p "stream: {bind_address: localhost, port: 9998}"

The space after each colon is significant, it can not be left out. For strings containing
special characters, such as colons, it is necessary to quote them:

::

   $ lewis chopper -p "epics: {prefix: 'PREF:'}"

New features
------------

 - The device setup (specified in the ``setups``-dict or module inside the device module)
   can be changed at runtime through the control server. It is not possible to switch to
   another device, only setups of the same device can be used. To query available setups:

   ::

      $ lewis-control simulation setups

   Then, to actually activate the new setup, assuming it is called ``new_setup``:

   ::

      $ lewis-control simulation switch_setup new_setup

 - It has been made easier to deposit devices in an external module while maintaining control over
   compatibility with the rest of the Lewis-framework. Lewis now checks for a version specification
   in each device module against the framework version before obtaining devices, adapters and
   setups from it. Please add such a version specification to your devices:

   .. code:: python

      framework_version = '1.0.3'

   This way using devices from different sources becomes more reliable for users with different
   versions of Lewis, or hint them to update. By default, Lewis won't start if a device specifies
   another framework version, but this behavior can be overridden by using the new flag
   ``-R/--relaxed-versions``:
   
   ::
   
      $ lewis some_device -R
      
   In this case the simulation will start, but a warning will still be logged so that this can be
   identified as a potential source of errors later on.
   
   
Bug fixes and other improvements
--------------------------------

 - The functionality for disconnecting and reconnecting a device's communication interfaces that
   used to be accessible via ``lewis-control`` through the ``simulation`` has been moved into a
   separate channel called ``interface``. To disconnect a device use:

   ::

      $ lewis-control interface disconnect

   In general, more fine-grained control over the device's communication is now possible, details
   are described :ref:`here <remote-interface-access>`.

 - Both :class:`~lewis.core.control_server.ControlServer` and
   :class:`~lewis.core.control_client.ControlClient` were subject to some improvements, most
   notably a settable timeout for requests was added so that incomplete requests do not cause the
   client to hang anymore. In ``lewis-control`` script, a new ``-t/--timeout`` argument was added
   to make use of that new functionality.
   
 - Only members defined as part of the device class are listed when using ``lewis-control device``.
   ``lewis-control`` generally no longer lists inherited framework functions such as ``log``, 
   ``add_processor``, etc. 
