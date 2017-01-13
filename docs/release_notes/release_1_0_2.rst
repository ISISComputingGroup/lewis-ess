:orphan:

Release 1.0.2
=============

This release is work in progress.

New features
------------

 - A simulation for a Julabo FP50 waterbath was kindly contributed by `Matt Clarke`_. It is
   communicating through TCP Stream and offers two different protocol versions. The new device
   can be started like the other available devices:
   
   ::
   
      $ lewis -p julabo-version-1 julabo

 - Exposing devices via TCP Stream has been made easier. It is now possible to define commands
   that expose lambda-functions, named functions and data attributes (with separate read/write
   patterns). See the updated documentation of :mod:`lewis.adapters.stream`.

Bug fixes and other improvements
--------------------------------

 - Virtually disconnecting devices via the control server now actually closes all network
   connections and shuts down any running servers, making it impossible to re-connect to the
   device in that state. Virtually re-connecting the device returns the behavior back to normal.

.. _Matt Clarke: https://github.com/mattclarke
