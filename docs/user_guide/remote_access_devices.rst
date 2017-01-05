Remote Access to Devices
========================

*Please note that this functionality should only be used on a trusted
network.*

Besides the device specific protocols, the device can be made accessible
from the outside via JSON-RPC over ZMQ. This can be achieved by passing
the ``-r`` option with a ``host:port`` string to the simulation:

::

    $ lewis -r 127.0.0.1:10000 chopper -- -p SIM:

Now the device can be controlled via the ``lewis-control.py``-script
in a different terminal window. The service can be queried to show the
available objects by not supplying an object name:

::

    $ lewis-control -r 127.0.0.1:10000

The ``-r`` (or ``--rpc-host``) option defaults to the value shown here,
so it will be omitted in the following examples. To get information on
the API of an object, supplying an object name without a property or
method will list the object's API:

::

    $ lewis-control device

This will output a list of properties and methods which is available for
remote access. This may not comprise the full interface of the object
depending on the server side configuration. Obtaining the value of a
property is done like this:

::

    $ lewis-control device state

The same syntax is used to call methods without parameters:

::

    $ lewis-control device initialize

To set a property to a new value, the value has to be supplied on the
command line:

::

    $ lewis-control device target_speed 100
    $ lewis-control device start

Value Interpretation and Syntax
-------------------------------

``lewis_control`` interprets values as built-in Python literals or containers using
`ast.literal_eval <https://docs.python.org/3/library/ast.html#ast.literal_eval>`__. This means any
syntax for literal evaluation supported by Python works here as well. The following are all valid
values which are interpreted as you might expect:

::

    $ lewis-control device float_value 12.0
    $ lewis-control device float_value .5
    $ lewis-control device float_value 1.23e10
    $ lewis-control device int_value 123
    $ lewis-control device int_value 0xDEADBEEF
    $ lewis-control device int_value 010  # Value of 8 in base 8 (octal)
    $ lewis-control device str_value hello_world
    $ lewis-control device method_call_with_two_string_args hello world
    $ lewis-control device str_value "hello world"
    $ lewis-control device unicode_value "u'hello_world'"
    $ lewis-control device list_value "[1,2,3]"
    $ lewis-control device list_value "['a', 'b', 'c']"
    $ lewis-control device dict_value "{'a': 1, 'b': 2}"

WARNING: Any value that cannot be successfully evaluated is silently converted into a
string literal instead! The following attempts turn into strings because the letters
are not quoted:

::

    $ lewis-control device str_value_looks_like_dict "{a: 1, b: 2}"
    $ lewis-control device str_value_looks_like_list "[a, b, c]"

This is done for convenience, to avoid having to double quote and/or escape quote trivial string
values to match Python syntax while also taking shell quotation and escapes into account. But it
can lead to unexpected results at times.

Control Client Python API
-------------------------

For use cases that require more flexibility and control, it is advised to write a Python script
using the API provided in ``lewis.core.control_client`` instead of using the command line utility.
This makes it possible to use the remote objects in a fairly transparent fashion.

Here is a brief example using the ``chopper`` device:

.. code:: python

    from time import sleep
    from lewis.core.control_client import ControlClient

    client = ControlClient(host='127.0.0.1', port='10000')
    chopper = client.get_object('device')

    chopper.target_speed = 100
    chopper.initialize()

    while chopper.state != 'stopped':
        sleep(0.1)

    chopper.start()

All calls, reads and assignments are synchronous and blocking in terms of the methods and
attributes they access on the server. However, much like with real devices, the behaviour of the
simulated device is asynchronous from its interface. Consequently, depending on the specific
device, some effects of calling a method may take place long after the method is called (and
returns).

This is why, in the above example, a loop is used to wait for ``chopper.state`` to change in
response to the ``chopper.initialize()`` call.
