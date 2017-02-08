:orphan:

Release 1.0.3
=============

This release is currently in progress.

New features
------------

Bug fixes and other improvements
--------------------------------

 - Both :class:`~lewis.core.control_server.ControlServer` and
   :class:`~lewis.core.control_client.ControlClient` were subject to some improvements, most
   notably a settable timeout for requests was added so that incomplete requests do not cause the
   client to hang anymore. In ``lewis-control`` script, a new ``-t/--timeout`` argument was added
   to make use of that new functionality.