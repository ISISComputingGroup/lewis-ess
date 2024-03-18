# Writing Device Simulators
The following section describes how to write a new device simulator, what to
consider, and how to get the changes upstream.

## Preparations
The Lewis framework provides all the infrastructure to run device
simulations so that developing a new simulation requires little more
than writing code for the actual device.

The process of writing a new device simulator is best explained using
the example of a stateful device.

All that is required to develop a new device is to install Lewis, preferably
in a fresh virtual environment:
```
$ pip install lewis
```

## Device analysis
The hypothetical device that is to be simulated is a simple controller
that controls one motor and can be communicated with via a
`TCP <https://en.wikipedia.org/wiki/Transmission_Control_Protocol>`__
connection. The user can connect to the device using telnet and submit
commands followed by `\r\n` (automatically added by
`telnet <https://linux.die.net/man/1/telnet>`__). Responses are followed
by `\r\n` as well. The following commands and responses are available:

-  `S?`: Returns the status of the motor connected to the controller.
   Can be either `idle` or `moving`, is initially `idle`.
-  `P?`: Returns the current position of the motor in mm. Is initially 0.
-  `T=10.0`: Sets the target position to `10.0` (accepts any
   floating point number) and starts a movement if the position is
   within the limits [0, 250] and returns `T=10.0`. If the motor is
   not in idle state, it returns `err: not idle`. If the value
   violates the limits, it returns `err: not 0<=T<=250`.
-  `T?` Returns the current target of the motor in mm. Is initially 0.
-  `H`: Stops the movement by setting the target to the current
   position and returns `T=6.555,P=6.555`. If the motor is idle,
   nothing happens, but the values are returned anyway.

In the simplest approach, the parameters that can describe the device
are:

-  position: Read only.
-  target: Can be read and written by the user, but with certain
   restrictions.

Additionally, the device is stateful in the sense that it can be in one
of three states.

-  `idle`: The motor is powered on and ready to receive commands.
-  `moving`: The motor is moving towards the user supplied target.

Between those three states, different transitions exist:

-  `idle` -> `moving`: The target position is different from the
   current position, the motor starts moving.
-  `moving` -> `idle`: The motor has reached the target position or
   the user has supplied a stop command, which sets the target position
   to the current position, causing the motor to stop.

The states and transitions described above form a finite state machine
with two states and two transitions. This state machine forms the heart
of the simulated device, so it should be implemented using Lewis'
cycle based [finite state
machine](https://en.wikipedia.org/wiki/Finite-state_machine), which
will be explained below.

## Implementing the device simulation
In many cases there may eventually be more than one device simulation, so the directory
structure should be something like this, assuming your directory is `/some/path`:

```
/some/path
    |
    +- my_devices
        |
        +- device_1
        |
        +- device_2
        |
        +- __init__.py (Empty file)
```

Each device resides in the sub-package `my_devices` in the. The first step is to create a
new directory in the `my_devices` directory called `example_motor`,
which should contain a single file, `__init__.py`. For simple devices
like this it's acceptable to put everything into one file, but for more
complex simulators it's recommended to follow the structure of the
devices that are already part of the Lewis distribution.

Conceptually, in Lewis, devices are split in two Parts: a device
model, which contains internal device state, as well as potentially a
state machine, and an interface that exposes the device to the outside
world via a communication protocol that is provided by an "adapter". The
adapter specifies the communication protocol (for example
[EPICS](http://www.aps.anl.gov/epics/) or TCP/IP), whereas the
interface specifies the syntax and semantics of the actual command
language of the device.

For the actual device simulation there are two classes to choose between
for sub-classing. The class `lewis.devices.Device` can be used for very simple
devices that do not require a state machine to represent their
operation. On each simulation cycle, the method `doProcess` is
executed if it is implemented. This can be used to implement
time-dependent behavior. For the majority of cases, such as in the
example, it is more convenient to inherit from `lewis.devices.StateMachineDevice`.
It provides an internal state machine and options to override
characteristics of the state machine on initialization.

`lewis.devices.StateMachineDevice` has three methods that must be implemented by
sub-classes: `lewis.devices.StateMachineDevice._get_state_handlers`,
`lewis.devices.StateMachineDevice._get_initial_state` and
`lewis.devices.StateMachineDevice._get_transition_handlers`. They are used to define
the state machine. A fourth, optional method can be used to initialize internal device
state, it's calld `lewis.devices.StateMachineDevice._initialize_data`. In this case
the device implementation should also go into `__init__.py`:

```
from lewis.devices import StateMachineDevice

from lewis.core.statemachine import State
from lewis.core import approaches

from collections import OrderedDict

class DefaultMovingState(State):
    def in_state(self, dt):
        old_position = self._context.position
        self._context.position = approaches.linear(old_position, self._context.target,
                                                   self._context.speed, dt)
        self.log.info('Moved position (%s -> %s), target=%s, speed=%s', old_position,
                      self._context.position, self._context.target, self._context.speed)

class SimulatedExampleMotor(StateMachineDevice):
    def _initialize_data(self):
        self.position = 0.0
        self._target = 0.0
        self.speed = 2.0

    def _get_state_handlers(self):
        return {
            'idle': State(),
            'moving': DefaultMovingState()
        }

    def _get_initial_state(self):
        return 'idle'

    def _get_transition_handlers(self):
        return OrderedDict([
            (('idle', 'moving'), lambda: self.position != self.target),
            (('moving', 'idle'), lambda: self.position == self.target)])

    @property
    def state(self):
        return self._csm.state

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, new_target):
        if self.state == 'moving':
            raise RuntimeError('Can not set new target while moving.')

        if not (0 <= new_target <= 250):
            raise ValueError('Target is out of range [0, 250]')

        self._target = new_target

    def stop(self):
        self._target = self.position

        self.log.info('Stopping movement after user request.')

        return self.target, self.position
```

This defines the state machine according to the description at the top
of the page and some internal state variables, for example `target`,
which has some limits on when and to what values it can be set.

Both states of the motor are described by a state handler. In case of
the `idle`-state it is enough to use `lewis.core.statemachine.State`,
which simply does nothing. `lewis.core.statemachine.State` has three methods that
can be overridden:

 - `lewis.core.statemachine.State.on_entry`
 - `lewis.core.statemachine.State.in_state`
 - `lewis.core.statemachine.State.on_exit`.

For other ways to specify those state handlers, please consult the documentation of
`lewis.core.statemachine.StateMachine`, where this is described in detail.
The advantage of using the `lewis.core.statemachine.State`-class is that it
has a so called context, which is stored in the `_context`-member. In case of
`lewis.devices.StateMachineDevice`, this context is the device object.
This means that device data can be modified in a state handler.

This is the case for the `moving`-state, where a state handler has
been defined by sub-classing `lewis.core.statemachine.State`.
In its `in_state`-method it modifies the `position` member of the device until it has reached
`target` with a rate that is stored in the `speed`-member. This
linear change behavior is implemented in the `~lewis.core.approaches.linear`-function from
`lewis.core.approaches`. It automatically makes sure that the target is
always obtained even for very coarse `dt`-values.

The transitions between states are defined using lambda-functions in
this case, which simply check whether the current position is identical
with the target or not.

The device also provides a read-only property `state`, which forwards
the state machine's (in the device as member `_csm`) state. The speed
of the motor is not part of the device specification, but it is added as
a member so that it can be changed via the `lewis-control` script to test
how the motor behaves at different speeds. The device is now fully
functional, but it's not possible to interact with it yet, because the
interface is not specified yet.

### Implementing the device interface
Device interfaces are implemented by sub-classing an appropriate
pre-written, protocol specific interface base class from the framework's
`lewis.adapters`-package and overriding a few members. In this case this
base class is called `lewis.adapters.stream.StreamInterface`. The first step
is to specify the available commands in terms of a collection of
`lewis.adapters.stream.Cmd`-objects. These objects effectively bind
commands specified in terms of regular expressions to the interface's methods.
According to the specifications above, the commands are defined like this:

```
from lewis.adapters.stream import StreamInterface, Cmd, scanf

class ExampleMotorStreamInterface(StreamInterface):
    commands = {
        Cmd('get_status', r'^S\?$'),
        Cmd('get_position', r'^P\?$'),
        Cmd('get_target', r'^T\?$'),
        Cmd('set_target', scanf('T=%f'), argument_mappings=(float,)),
        Cmd('stop', r'^H$',
            return_mapping=lambda x: 'T={},P={}'.format(x[0], x[1])),
    }

    in_terminator = '\r\n'
    out_terminator = '\r\n'

    def get_status(self):
        return self.device.state

    def get_position(self):
        return self.device.position

    def get_target(self):
        return self.device.target

    def set_target(self, new_target):
        try:
            self.device.target = new_target
            return 'T={}'.format(new_target)
        except RuntimeError:
            return 'err: not idle'
        except ValueError:
            return 'err: not 0<=T<=250'
```

The first argument to `lewis.adapters.stream.Cmd` specifies the method
name the command is bound to, whereas the second argument is a pattern that a
request coming in over the TCP stream must match. If the pattern is specified as a string,
it is treated as a regular expression. In the above example, `lewis.adapters.stream.scanf`
is used for one of the functions, it allows for `scanf`-like format specifiers. If a method has
arguments (such as `set_target`), these need to be defined as capture
groups in the regular expression. These groups are passed as strings to
the bound method. If any sort of conversion is required for these
arguments, the `argument_mapping`-parameter can be a tuple of
conversion functions with the same lengths as the number of capture
groups in the regular expression. In the case of `set_target` it's
enough to convert the string to float, but `lewis.adapters.stream.scanf` does that
automatically, so it is not strictly required here. Return values (except `None`)
are converted to strings automatically, but this conversion can be
overridden by supplying a callable object to `return_mapping`, as it
is the case for the `stop`-command.

You may have noticed that `stop` is not a method of the interface.
`lewis.adapters.stream.StreamInterface` tries to resolve the supplied method
names in multiple ways. First it checks its own members, then it checks the members of the
device it owns (accessible in the interface via the `device`-member)
and binds to the appropriate method. If the method name can not be
found in either the device or the interface, an error is produced, which
minimizes the likelihood of typos. The definitions in the interface
always have precedence, this is intentionally done so that device
behavior can be overridden later on with minimal changes to the code.

In case of the `stop`-method, which returns two floating point numbers
(target and position), the `return_mapping` is used to format the
device's position and target as specified in the protocol definition at
the top of the page.

Finally, in- and out-terminators need to be specified. These are
stripped from and appended to requests and replies respectively.

This entire device can also be found in the `lewis.examples` module. It can be
started using the `-a` and `-k` parameters of `lewis.py`:

```
$ lewis -a /some/path -k my_devices example_motor -p "stream: {bind_address: 127.0.0.1, port: 9999}"
```

All functionality described in the
`user_guide`, such as accessing the device and the simulation via the
`lewis-control.py`-script are automatically available.

## Logging
Both device and interface support logging, they supply a `log` member which is
a logger configured with the right name. The adapter already logs all important actions
that influence the device, so in the interface it should not be necessary to do too much
logging, but it might be interesting for debugging purposes.

Note that the simulation already produces one debug log message per simulation cycle logging
the elapsed (real-)time, so it is not necessary to log the `dt` parameters in addition.
`lewis.core.statemachine.StateMachine` also logs on each cycle which state it is in and
which transitions are triggered (if any). In the `lewis.core.statemachine.State`-handlers
that are device specific, any logging should focus on the behavior in that concrete state, as
for example demonstrated in the example above.

It is also important to consider the log level. Log messages that occur on each cycle must be
strictly limited to the `debug`-level, because they potentially produce a lot of data.
The `info`-level and above should be used for information that is relevant to anyone running
the simulation, such as failures or other "virtual problems" that might otherwise go unnoticed.
A good example would be a device that ignores faulty commands - a `warning` could be logged
with details about the command and that it was ignored.

## User facing documentation

The `lewis.adapters.stream.StreamAdapter`-class has a property
`documentation`, which generates user facing documentation from the
`lewis.adapters.stream.Cmd`-objects (it can be displayed via the `-i`-flag of
`lewis` from the `interface` object via `lewis-control.py`). The regular expression of
each command is listed, along with a documentation string. If the `doc`-parameter is provided
to Cmd, it is used,otherwise the docstring of the wrapped method is used (it does not matter
whether the method is part of the device or the interface for feature to work). The latter is the
recommended way, because it avoids duplication. But in some cases, the user- and the
developer facing documentation may be so different that it's useful to override the docstring.

This is also combined with the docstring of the interface (in this case
`ExampleMotorStreamInterface`), and some information about the configured host/port,
as well as terminators. The documentation has been left out from the above code samples for
brevity, but in the `examples`-directory, the docs are present.

All adapters offer similar functionality, the purpose is that the devices are documented in
a way that makes them easy to use by non-developers. This is especially important if the
protocol is non-obvious.

## Unit tests
Unit tests should be added to the `test`-directory. While it would be
best to have unit tests for device and interface separately, it is most
important that the tests capture overall device behavior, so that it's
immediately noticed when a change to Lewis' core parts breaks the
simulation. It also makes it easier later on to refactor and change the
device.

## Adding setups
In order to test certain failure scenarios of a device, setups can be
added to a device. The easiest way is to define a dictionary called
`setups` in the `__init__.py` file. A setup consists of a device
type and initialization parameters:

```
setups = dict(
    moving=dict(
        device_type=SimulatedExampleMotor,
        parameters=dict(
            override_initial_state='moving',
            override_initial_data=dict(
                _target=120.0, position=20.0
            )
        )
    )
)
```

In this case a `moving`-scenario is defined where the motor is already
moving to a target when the simulation is started.

## Compatibility with framework versions
To make sure that users have a good experience using the newly added device,
it should specify what version of Lewis it works with. This is achieved by
adding another variable to the top level of the device module which contains
a version specification:
```
framework_version = '1.0.1'
```

This will make sure that older or newer versions of Lewis do not present odd exceptions
or error messages to users trying to start the device. If Lewis detects a mismatch
between the required version and the existing version, an error message is logged
so that users know where the problem comes from. In the ideal case this variable
would be updated with each release of Lewis after it has been made sure that the
device is compatible.

## Further steps
Once a device is developed far enough, it's time to submit a pull
request. As an external contributor, this happens via a fork on github.
Members of the development team will review the code and may make
suggestions for changes. Once the code is acceptable, it will be merged
into Lewis' main branch and become a part of the distribution.

If a second interface is added to a device, either using a different
interface type or the same but with different commands, the interface
definitions should be moved out of the `__init__.py` file. Lewis
will continue to work if the interfaces are moved to a sub-folder of the
device called `interfaces`. This needs to have its own
`__init__.py`, where interface-classes can be imported from other
files in that module. It's best to look at the chopper and linkam\_t95
devices that are already in Lewis.

The same is true for setups. For complex setups, these should be moved
to a sub-module of the device called `setups`, where each setup can
live in its own file. Please see the documentation of
`lewis.devices.import_device` for reference.

## More Examples
More example devices and interfaces are provided in the `lewis.examples` directory.
