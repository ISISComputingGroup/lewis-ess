:orphan:

Release 1.0.3
=============

This release is currently in progress.

New features
------------

 - It has been made easier to deposit devices in an external module while maintaining control over
   compatibility with the rest of the Lewis-framework. Lewis now checks for a version specification
   in each device module against the framework version before obtaining devices, adapters and
   setups from it. Please add such a version specification to your devices:

   .. code:: python

      framework_version = '1.0.3'

   It is also possible to indicate ranges or multiple conditions (like in requirements
   files for pip):

   .. code:: python

      framework_version = '>=1.0.3,<2.0.0'

   This way using devices from different sources becomes more reliable for users with different
   versions of Lewis, or hint them to update.


Bug fixes and other improvements
--------------------------------

 - Both :class:`~lewis.core.control_server.ControlServer` and
   :class:`~lewis.core.control_client.ControlClient` were subject to some improvements, most
   notably a settable timeout for requests was added so that incomplete requests do not cause the
   client to hang anymore. In ``lewis-control`` script, a new ``-t/--timeout`` argument was added
   to make use of that new functionality.