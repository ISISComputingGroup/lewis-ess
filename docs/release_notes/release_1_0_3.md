# Release 1.0.3
This version was released on March 24th, 2017. In this release, the `lewis.adapters.epics`-
module has received some updates. Some important groundwork for future improvements has been
laid as well, which resulted in the ability to switch device setups at runtime via the control
server and a new command line syntax for configuring communications. The control server and client
have been improved as well.

## Command line interface change
The way options are passed to the adapters has changed completely, the functionality has been
merged into the ``-p``-argument, which has a new long version now, ``--adapter-options``.

For the default adapter options, it is still possible to use the ``lewis``-command with ``-p``
in the same way as before:

```
$ lewis -p stream linkam_t95
```

To supply options, such as the address and port to bind to, the argument accepts an extended
dictionary syntax now:

```
$ lewis linkam_t95 -p "stream: {bind_address: localhost, port: 9998}"
```

The space after each colon is significant, it can not be left out. For strings containing
special characters, such as colons, it is necessary to quote them:

```
$ lewis chopper -p "epics: {prefix: 'PREF:'}"
```

To see what options can be specified, use the new ``-L/--list-adapter-options`` flag:

```
$ lewis chopper -p epics -L
```

## New features
- Writing devices with an EPICS interface has been made more convenient for cases where the device
   does not have properties, but does have getter and setter methods.
   `lewis.adapters.epics.PV` has been extended to accept a wider range of values for
   ``target_property`` and ``meta_data_property``, for example method names:
```
     class FooDevice(Device):
         _foo = 3

         def get_foo(self):
             return self._foo * 3

     class FooDeviceInterface(EpicsAdapter):
         pvs = {
             'Foo': PV('get_foo')
         }
```

   For read/write cases, a tuple of names can be supplied. Instead of method names it is also
   allowed to specify callables, for example functions or lambda expressions. In that case, the
   signature of the function is checked. See also the new example in
   ``lewis.examples.epics_device``.

- The device setup (specified in the ``setups``-dict or module inside the device module)
   can be changed at runtime through the control server. It is not possible to switch to
   another device, only setups of the same device can be used. To query available setups:

```
   $ lewis-control simulation setups
```
   Then, to actually activate the new setup, assuming it is called ``new_setup``:
```
   $ lewis-control simulation switch_setup new_setup
```

- It has been made easier to deposit devices in an external module while maintaining control over
   compatibility with the rest of the Lewis-framework. Lewis now checks for a version specification
   in each device module against the framework version before obtaining devices, adapters and
   setups from it. Please add such a version specification to your devices.

   This way using devices from different sources becomes more reliable for users with different
   versions of Lewis, or hint them to update. By default, Lewis won't start if a device specifies
   another framework version, but this behavior can be overridden by using the new flag
   ``-R/--relaxed-versions``:

   In this case the simulation will start, but a warning will still be logged so that this can be
   identified as a potential source of errors later on.

- A new flag ``-V/--verify`` has been added to the ``lewis``-script. When activated, it sets
   the output level to ``debug`` and exits before actually starting the simulation. This can
   help diagnose problems with device modules or input parameters.

## Bug fixes and other improvements
- The functionality for disconnecting and reconnecting a device's communication interfaces that
   used to be accessible via ``lewis-control`` through the ``simulation`` has been moved into a
   separate channel called ``interface``. To disconnect a device use:

   In general, more fine-grained control over the device's communication is now possible.

- Both `lewis.core.control_server.ControlServer` and
   `lewis.core.control_client.ControlClient` were subject to some improvements, most
   notably a settable timeout for requests was added so that incomplete requests do not cause the
   client to hang anymore. In ``lewis-control`` script, a new ``-t/--timeout`` argument was added
   to make use of that new functionality.

 - Only members defined as part of the device class are listed when using ``lewis-control device``.
   ``lewis-control`` generally no longer lists inherited framework functions such as ``log``,
   ``add_processor``, etc.

## Upgrade Guide
The following changes have to be made to upgrade code working with Lewis `1.0.2` to work with
Lewis `1.0.3`:

- Any scripts or code starting Lewis with the old style adapter parameters need to be updated to
   the new style adapter options.

   For EPICS adapters:
```
      Old style:
      $ lewis chopper
      $ lewis chopper -p epics
      $ lewis chopper -p epics -- -p SIM:
      $ lewis chopper -- --prefix SIM:
      New style:
      $ lewis chopper
      $ lewis chopper -p epics
      $ lewis chopper -p "epics: {prefix: 'SIM:'}"
```

   For TCP Stream adapters:
```
       Old style:
       $ lewis linkam_t95
       $ lewis linkam_t95 -p stream
       $ lewis linkam_t95 -p stream -- -b 127.0.0.1 -p 9999 -t
       $ lewis linkam_t95 -- --bind_address 127.0.0.1 --port 9999 --telnet_mode
       New style:
       $ lewis linkam_t95
       $ lewis linkam_t95 -p stream
       $ lewis linkam_t95 -p "stream: {bind_address: 127.0.0.1, port: 9999, telnet_mode: True}"
```

   For Modbus adapters:
```
      Old style:
      $ lewis -k lewis.examples modbus_device
      $ lewis -k lewis.examples modbus_device -p modbus
      $ lewis -k lewis.examples modbus_device -p modbus -- -b 127.0.0.1 -p 5020
      $ lewis -k lewis.examples modbus_device -- --bind_address 127.0.0.1 --port 5020
      New style:
      $ lewis -k lewis.examples modbus_device
      $ lewis -k lewis.examples modbus_device -p modbus
      $ lewis -k lewis.examples modbus_device -p "modbus: {bind_address: 127.0.0.1, port: 5020}"
```
 - Devices must now specify a ``framework_version`` in the global namespace of their top-level
   ``__init__.py``, like this:

```
   framework_version = '1.0.3'
```

   This will need to be updated with every release. If this version is missing or does not match
   the current Lewis framework version, attempting to run the device simulation will fail with a
   message informing the user of the mismatch. This can be bypassed by starting Lewis with the
   following parameter:

```
   $ lewis linkam_t95 -R
   $ lewis linkam_t95 --relaxed-versions
```
   Warning: in the next release, specifying ``framework_version`` becomes optional and 
      ``--relaxed-versions`` is renamed to ``--ignore-versions``. 
