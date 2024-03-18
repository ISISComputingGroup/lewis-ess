# Release 1.0.2
This version of Lewis was released on January 26th, 2017. A few bugs have been fixed and a lot
of functionality has been added. The most notable changes are preliminary Modbus protocol support
and logging capabilities which make debugging easier.

## New features
- A preliminary Modbus Adapter has been added. The current version is mainly aimed at what is
   currently required by the IBEX team for the ``nanodac``. Since all that is needed is writing
   and reading back from memory via the Modbus protocol, bindings to ``Device`` attributes or
   functions have not been implemented yet. We will add these in a future version.
   
   The current version supports:
   
    - Eight common Function Codes (0x01 through 0x06, 0x0F and 0x10)
    - Overlaid memory segments (using the same databank for ``di`` and ``co`` for example)
    - Modbus Exceptions for invalid Function Codes, bad memory addresses, invalid data, etc
    - Request frames may arrive in arbitrary chunks of multiple or partial frames
    
   For a usage example, see ``examples/modbus_device``.
    
- Logging capabilities have been added to the framework through the standard Python `logging`_
   module. The ``lewis``-script logs messages to stderr, the level can be set using a new flag
   ``-o/--output-level``.

   All devices have a new member ``log``, which can be used like this:
```
    class SomeDevice(Device):
        def some_method(self, param):
            self.log.debug('some_method called with param=%s', param)
```

   This new behavior is also supported by `lewis.core.statemachine.State`,
   so that changes in device state can be logged as well.

- A simulation for a Julabo FP50 waterbath was kindly contributed by Matt Clarke. It is
   communicating through TCP Stream and offers two different protocol versions. The new device
   can be started like the other available devices:
  ``` 
  $ lewis -p julabo-version-1 julabo
  ```

- Exposing devices via TCP Stream has been made easier. It is now possible to define commands
   that expose lambda-functions, named functions and data attributes (with separate read/write
   patterns). See the updated documentation of :mod:`lewis.adapters.stream`.

- TCP Stream based devices are now easier to test with telnet due to a new adapter argument.
   The new ``-t``-flag makes the device interface "telnet compatible":
   
   ```
   $ lewis linkam_t95 -- -t
   ```
   
   Instead of the native in- and out-terminator of the device, the interface now looks for ``\r\n``.

- The `lewis.adapters.epics.PV`-class has been extended to allow for meta data updates
   at runtime. A second property can now be specified that returns a dictionary to update the
   PV's metadata such as limits or alarm states.
- It is now possible to change multiple device parameters through lewis-control:
 ```
 $ lewis-control simulation set_device_parameters "{'target_speed': 1, 'target_phase': 20}"
 ```
 Thanks to the IBEX team for requesting this.

## Bug fixes and other improvements
- Virtually disconnecting devices via the control server now actually closes all network
   connections and shuts down any running servers, making it impossible to re-connect to the
   device in that state. Virtually re-connecting the device returns the behavior back to normal.
- If a device contained members that are not JSON serializable, displaying the device's API
   using the lewis-control script failed. This has been fixed, instead a message is now printed
   that informs the user about why fetching the attribute value failed. Thanks to Adrian Potter
   for reporting this issue.

