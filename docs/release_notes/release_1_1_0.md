# Release 1.1
In this release, some key changes to the core framework have been implemented. It is now possible
to have more than one communication interface for a device, which enables some interesting use
cases like partial interfaces, or multiple communication protocols accessing the same device. One
prerequisite for this feature was running the network services in different threads than the
device simulation.

Another key change, one that requires some minor changes to existing devices (see upgrade guide),
was that the communication interface definition has been completely separate from the network
services handling the network communication.

Besides these major improvements, there have been a number of smaller improvements and new
features, and Lewis now also has a logo (see below).

## New features
- It is now possible to have devices with more than one communication interface. The `-p`-option
   can be supplied multiple times:
```
   $ lewis some_device -p protocol1 -p protocol2
```

   When no ``-p`` option is specified, the script behaves as before (use default protocol if
   possible or produce an error message). To start a simulation without any device communication,
   use the new ``-n``/``--no-interface`` option:
```
   $ lewis some_device -n
```

   It is not possible to use both ``-p`` and ``-n`` at the same time, this results in an error
   message.

   The ``epics_device`` example has been renamed to ``dual_device`` and extended to include a
   second interface definition, so it exposes the device state via two different protocols:

```
   $ lewis -k lewis.examples dual_device -p epics -p stream
```
- `lewis.adapters.stream` has been extended. Besides regular expressions, it is now
   possible to use `scanf` format specifications to define commands. This makes handling
   of for example floating point numbers much more convenient:

```
   from lewis.adapters import StreamInterface, Cmd, scanf

   class SomeInterface(StreamInterface):
      commands = {
         Cmd(lambda x: x**2, scanf('SQ %f'))
      }
```

   `lewis.adapters.stream.scanf` provides argument mappings for the matched arguments
   automatically, so it is optional to pass them to ``Cmd``. In the case outlined above, the
   argument is automatically converted to ``float``.

   If a string is specified directly (instead of ``scanf(...)``), it is treated as a regular
   expression like in earlier versions.

   Internally, the scanf package is used for handling these patterns, please check the package
   documentation for all available format specifiers. Thanks to @joshburnett for accepting
   a small patch to the package that made the package easier to integrate into Lewis.

- The control client, lewis-control, now provides a version argument via ``--version`` or ``-v``.

```
   $ lewis-control -v
```

## Bug fixes and other improvements
- Lewis now has a logo. It is based on  a state machine with one state that is entered and
   repeated infinitely - like the simulation cycles in Lewis.

   For low-resolution images or settings with little space, there is also a simplified version.

   The logo was made using inkscape, the font used in the logo is Rubik (in the SVG itself,
   the text was converted into a path, so that the font does not need to be installed for the logo
   to render correctly). The two PNGs and also the SVGs are in the source repository, feel
   free to include them in presentations or posters.

- Adapters now run in a different thread than the simulation itself. The consequence of this is
   that slow network communication or expensive computations in the device do not influence
   one another anymore. Otherwise, communication still works exactly like in previous versions.

- The behavior of the ``framework_version``-variable for devices that was introduced in version
   1.0.3 has been modified to make it easier to convert from older versions of Lewis.

   With the default options of the ``lewis``-command, devices that do not specify the variable
   will be loaded after logging a warning. An error message is only displayed when strict
   version checking is enabled through the new ``-S/--strict-versions``-flag.

   The option to ignore version mismatches has been renamed to ``-I/--ignore-versions``. When
   that flag is specified, any device regardless of the contents of ``framework_version`` is
   loaded, but a warning is still logged.

   Specifying the ``framework_version`` variable is still encouraged as it can contribute to
   more certainty on the user side as to whether a device can function with a certain function
   of Lewis.

## Upgrade guide

- Due to a change to how Adapters and Devices work together, device interfaces are not
   inheriting from Adapter-classes anymore. Instead, there are dedicated Interface classes.
   They are located in the same modules as the Adapters, so only small changes are necessary:

   Old:
```
    from lewis.adapters.stream import StreamAdapter, Cmd

    class DeviceInterface(StreamAdapter):
        pass
```

   New:
```
    from lewis.adapters.stream import StreamInterface, Cmd

    class DeviceInterface(StreamInterface):
        pass
```

   The same goes for ``EpicsAdapter`` and ``ModbusAdapter``, which must be modified to
   ``EpicsInterface`` and ``ModbusInterface`` respectively.
