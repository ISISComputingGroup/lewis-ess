Remote access to devices
========================

*Please note that this functionality should only be used on a trusted
network.*

Besides the device specific protocols, the device can be made accessible
from the outside via JSON-RPC over ZMQ. This can be achieved by passing
the ``-r`` option with a ``host:port`` string to the simulation:

::

    $ python lewis.py -r 127.0.0.1:10000 chopper -- -p SIM:

Now the device can be controlled via the ``lewis-control.py``-script
in a different terminal window. The service can be queried to show the
available objects by not supplying an object name:

::

    $ python lewis-control.py -r 127.0.0.1:10000

The ``-r`` (or ``--rpc-host``) option defaults to the value shown here,
so it will be omitted in the following examples. To get information on
the API of an object, supplying an object name without a property or
method will list the object's API:

::

    $ python lewis-control.py device

This will output a list of properties and methods which is available for
remote access. This may not comprise the full interface of the object
depending on the server side configuration. Obtaining the value of a
property is done like this:

::

    $ python lewis-control.py device state

The same syntax is used to call methods without parameters:

::

    $ python lewis-control.py device initialize

To set a property to a new value, the value has to be supplied on the
command line:

::

    $ python lewis-control.py device target_speed 100
    $ python lewis-control.py device start

Only numeric types and strings can be used as arguments via the
``lewis-control.py``-script. The script always tries to convert
parameters to ``int`` first, then to ``float`` and leaves it as ``str``
if both fail. For other types and more control over types, it's advised
to write a Python script instead using the tools provided in
``lewis.core.control_client`` which makes it possible to use the
remote objects more or less transparently. An example to control the
chopper:

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
