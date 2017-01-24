:orphan:

Release 1.0.2
=============

This release is work in progress.

New features
------------
 - Logging capabilities have been added to the framework through the standard Python `logging`_
   module. The ``lewis``-script logs messages to stderr, the level can be set using a new flag
   ``-o/--output-level``.

   All devices have a new member ``log``, which can be used like this:

   .. sourcecode:: Python

       class SomeDevice(Device):
           def some_method(self, param):
               self.log.debug('some_method called with param=%s', param)

   This new behavior is also supported by :class:`~lewis.core.statemachine.State`,
   so that changes in device state can be logged as well.

 - A simulation for a Julabo FP50 waterbath was kindly contributed by `Matt Clarke`_. It is
   communicating through TCP Stream and offers two different protocol versions. The new device
   can be started like the other available devices:
   
   ::
   
      $ lewis -p julabo-version-1 julabo

 - Exposing devices via TCP Stream has been made easier. It is now possible to define commands
   that expose lambda-functions, named functions and data attributes (with separate read/write
   patterns). See the updated documentation of :mod:`lewis.adapters.stream`.

 - The :class:`PV`-class has been extended to allow for meta data updates at runtime. A second
   property can now be specified that returns a dictionary to update the PV's meta data such as
   limits or alarm states.

Bug fixes and other improvements
--------------------------------

 - Virtually disconnecting devices via the control server now actually closes all network
   connections and shuts down any running servers, making it impossible to re-connect to the
   device in that state. Virtually re-connecting the device returns the behavior back to normal.
 - If a device contained members that are not JSON serializable, displaying the device's API
   using the lewis-control script failed. This has been fixed, instead a message is now printed
   that informs the user about why fetching the attribute value failed. Thanks to `Adrian Potter`_
   for reporting this issue.

.. _Matt Clarke: https://github.com/mattclarke
.. _Adrian Potter: https://github.com/AdrianPotter
.. _logging: https://docs.python.org/2/library/logging.html