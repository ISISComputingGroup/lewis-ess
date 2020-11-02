.. _quickstart_guide:

Quickstart Guide
################

This section aims to get you started with Lewis as quickly as possible. It is meant as a basic starting point for becoming familiar with Lewis, and to give you a broad overview of what it can do. As such, many features are skimmed over or skipped entirely. See the detailed documentation sections for a more complete overview of features.

This guide is presented as a step-by-step tutorial, so skipping sections may mean you will miss steps that are required for the examples to work.


Install Lewis
=============

The recommended way to install Lewis is via PyPI and using a virtual environment. This guide assumes you have Python and Pip installed and in your PATH.

Create a virtual environment (optional):

::

    $ python -m venv myenv
    $ source myenv/bin/activate

On Windows, the activate script will be located elsewhere and can be executed directly, without ``source``.

Lewis can be installed with Pip using a single command:

::

    $ pip install lewis
    $ lewis --version
    $ lewis -h


Run the Motor Example
=====================

Once Lewis is installed, you can use it to start some of the example devices it ships with.

You can see which devices are available by just executing Lewis without parameters:

::

    $ lewis
    Please specify a device to simulate. The following devices are available:
        julabo
        chopper
        linkam_t95

Some additional, simpler examples are located in the ``lewis.examples`` module. You can tell Lewis which module to scan for devices using the ``-k`` parameter:

::

    $ lewis -k lewis.examples
    Please specify a device to simulate. The following devices are available:
        dual_device
        simple_device
        timeout_device
        modbus_device
        example_motor

For this guide, we will launch the example_motor:

::

    $ lewis -k lewis.examples example_motor
    INFO lewis.DeviceBase: Creating device, setting up state machine
    INFO lewis.Simulation: Changed cycle delay to 0.1
    INFO lewis.Simulation: Changed speed to 1.0
    INFO lewis.Simulation: Starting simulation
    INFO lewis.AdapterCollection: Connecting device interface for protocol 'stream'
    INFO lewis.ExampleMotorStreamInterface.StreamServer: Listening on 0.0.0.0:9999

The example motor is a TCP Stream device and listens on port 9999 on all adapters by default.


Connect to Motor via Telnet
===========================

With the last command from the previous section still running, open another terminal window.

Since the example motor conveniently uses CRLF line terminators, we can use telnet to talk to it:

::

    $ telnet localhost 9999
    Trying 127.0.0.1...
    Connected to localhost.
    Escape character is '^]'.

You're now connected to the TCP Stream interface of the example motor device. It understands the following commands:

=======  =============
Command  Meaning
=======  =============
S?       get status
P?       get position
T?       get target
T=%f     set target
H        stop movement
=======  =============

You can get more details, and details on the interface of any device, by using the ``-i`` or ``--show-interface`` argument:

::

    $ lewis -k lewis.examples example_motor -i

Note that the commands are case sensitive. Try entering a few commands in the Telnet session:

::

    S?
    idle
    P?
    0.0
    T=20.0
    T=20.0
    S?
    moving
    P?
    9.106584

See `the source code <https://github.com/ess-dmsc/lewis/blob/master/lewis/examples/example_motor/__init__.py>`_ of the example motor if you want to see what makes it tick.


Connect to Motor via Control Client
===================================

In addition to the simulated TCP Stream interface, Lewis provides a so-called Control Server interface, which allows you to bypass the normal device protocol and access both device and simulation parameters directly while the simulation is running. This can be very useful for debugging and diagnostics, without having to modify the main device interface.

Remote access is disabled by default and enabled only if you provide the ``-r`` argument when starting Lewis. Stop the previously launched instance of Lewis by pressing ``Ctrl-C`` and run Lewis again with the ``-r`` parameter to enable remote access like this:

::

    $ lewis -r localhost:10000 -k lewis.examples example_motor

Lewis ships with a Control Client commandline tool that allows you to connect to it. It also has an ``-r`` argument but for the client it defaults to ``localhost:10000``, which is why it is recommended to use the same value above.

Open another terminal session. If you installed Lewis in a virtual environment, make sure to activate it in the new terminal session so that Lewis is available:

::

    $ . myenv/bin/activate

Running ``lewis-control`` without any parameter displays the objects available to interact with:

::

    $ lewis-control
    device
    interface
    simulation

You can think of these as root nodes in a tree that ``lewis-control`` allows you to traverse. Passing one of them as an argument shows you what is available below that level:

::

    $ lewis-control device
    Type: SimulatedExampleMotor
    Properties (current values):
        position    (20.0)
        speed       (2.0)
        state       (idle)
        target      (20.0)
    Methods:
        stop

Going down one more level retrieves the value of a single property, or calls a method (without passing arguments):

::

    $ lewis-control device target
    0.0

And by specifying additional argument(s) we can set properties (or pass arguments to methods):

::

    $ lewis-control device target 100.0
    $ lewis-control device
    Type: SimulatedExampleMotor
    Properties (current values):
        position    (29.159932)
        speed       (2.0)
        state       (moving)
        target      (100.0)
    Methods:
        stop
    $ lewis-control device stop
    [78.64038600000002, 78.64038600000002]
    $ lewis-control device
    Type: SimulatedExampleMotor
    Properties (current values):
        position    (78.640386)
        speed       (2.0)
        state       (idle)
        target      (78.640386)
    Methods:
        stop

Note that, as you go along, you can also use a Telnet session in another terminal to issue commands or request information, and that the state of the device will be consistent between the two connections.

Aside from the simulated device itself, you can also access and modify parameters of the simulation and network interface(s):

::

    $ lewis-control simulation
    $ lewis-control interface

See the respective sections of documentation for more details.


Control Motor via Control API
=============================

While the command line client is convenient for manual diagnostics and debugging, you may find the Control API more useful for automated testing. It exposes all the same functionality available on the CLI via a Python library (In fact, that is how the CLI client is implemented).

If you installed Lewis in a virtual environment, make sure you activate it:

::

    $ . myenv/bin/activate

Usually, you would use this API to write a Python script, but for demo purposes we will just use the interactive Python client:

::

    $ python
    Python 2.7.12 (default, Nov 19 2016, 06:48:10)
    [GCC 5.4.0 20160609] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from lewis.core.control_client import ControlClient
    >>>
    >>> client = ControlClient(host='localhost', port='10000')
    >>> motor = client.get_object('device')
    >>>
    >>> motor.target
    78.64038600000002
    >>> motor.target = 20.0
    >>> motor.state
    u'moving'
    >>> motor.stop()
    [45.142721999999964, 45.142721999999964]
    >>> motor.state
    u'idle'
    >>> motor.position
    45.142721999999964

As with the previous sections, you can also interact with the motor using any of the other interfaces as you are doing this and the state will always be consistent between them.

