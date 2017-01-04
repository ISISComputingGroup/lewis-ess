:orphan:

Release 1.1
===========

This release is work in progress.

New features
------------

 - Exposing devices via TCP Stream has been made easier. It is now possible to define commands
   that expose lambda-functions, named functions and data attributes (with separate read/write
   patterns).

Bug fixes and other improvements
--------------------------------

 - Virtually disconnecting devices via the control server now actually closes all network
   connections and shuts down any running servers, making it impossible to re-connect to the
   device in that state. Virtually re-connecting the device returns the behavior back to normal.
