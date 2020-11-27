|Build Status| |Codacy| |Coverage Status| |Documentation|

|Lewis|
=======

LeWIS - Let's Write Intricate Simulators.

Lewis is a Python framework for simulating hardware devices. It is
compatible with Python 3.6 or higher.

Lewis can be installed via pip or ran from source. See relevant usage sections at
`ReadTheDocs <http://lewis.readthedocs.io/>`__ for more details.

Resources:
`GitHub <https://github.com/ess-dmsc/lewis>`__ --
`ReadTheDocs <http://lewis.readthedocs.io/>`__ --
`PyPI <https://pypi.python.org/pypi/lewis>`__

Lewis was previously named "Plankton" but, due to a
package with the same name on PyPI, we decided to rename the project.

Lewis is licensed under GPL v3 or later.

Purpose and Use Cases
---------------------

Lewis is being developed in the context of instrument control at the
`ESS <http://europeanspallationsource.se>`__, but it is general enough
to be used in many other contexts that require detailed, stateful
software simulations of hardware devices.

We consider a detailed device simulation to be one that can communicate
using the same protocol as the real device, and that can very closely
approximate real device behaviour in terms of what is seen through this
protocol. This includes gradual processes, side-effects and error
conditions.

The purpose of Lewis is to provide a common framework to facilitate
the development of such simulators. The framework provides a common set
of tools, including communication protocol services, which helps minimize code
replication and allows the developer of a simulated device to focus on
capturing device behaviour.

Potential use cases for detailed device simulators include:

-  Replacing the physical device when developing and testing software
   that interfaces with the device
-  Testing failure conditions without risking damage to the physical
   device
-  Automated system and unit tests of software that communicates with
   the device
-  Perform "dry runs" against test scripts that are to be run on the
   real device

Using a simulation for the above has the added benefit that, unlike most
real devices, a simulation may be sped up / fast-forwarded past any
lengthy delays or processes that occur in the device.

Features
--------

Brief Terminology
~~~~~~~~~~~~~~~~~

``Device``\ s and ``Interface``\ s are two independent concepts in
Lewis. The ``Device`` is model for the device behaviour and internal
memory. A ``Device`` can be represented using a ``StateMachine``, but it
does not have to be. A ``Device`` does not include anything specific to
the communication protocol with the ``Device``. An ``Interface``
provides bindings from a protocol ``Adapter`` to a ``Device``.
Common ``Adapter``\ s, , such as TCP stream, Modbus and EPICS, are provided
by Lewis. The ``Device`` and ``Interface`` are instantiated as part of a
``Simulation`` that provides a cycle "heart beat" and manages other
environmental aspects and services.

.. image:: https://github.com/ess-dmsc/lewis/raw/master/docs/resources/diagrams/SimulationCycles.png

What Can You Do With Lewis?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Create new ``Device``\ s to closely imitate the internal behaviour
   and memory of something
-  Optionally make a ``Device`` work as a ``StateMachine`` via
   ``StateMachineDevice`` to give rich behaviours
-  Create one or more ``Interface``\ s over your ``Device`` to expose it
   as an EPICS IOC, a TCP listener, or on any other bespoke protocol you
   like
-  Access and control the ``Device`` while it is running via a control server
-  Access and control the ``Simulation`` while it is running via a control server
-  Control server can be accessed via command-line utility, Python bindings, or
   JSON RPC.

Additional Documentation
------------------------

Documentation can be found at `ReadTheDocs <http://lewis.readthedocs.io/>`__.


.. |Build Status| image:: https://travis-ci.org/ess-dmsc/lewis.svg?branch=master
   :target: https://travis-ci.org/ess-dmsc/lewis
.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/77aef653cf5d42f5a9a8a5a2c929a628
   :target: https://www.codacy.com/app/DMSC/lewis?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=DMSC-Instrument-Data/lewis&amp;utm_campaign=Badge_Grade
.. |Coverage Status| image:: https://coveralls.io/repos/github/DMSC-Instrument-Data/lewis/badge.svg?branch=master
   :target: https://coveralls.io/github/DMSC-Instrument-Data/lewis?branch=master
.. |Documentation| image:: https://readthedocs.org/projects/lewis/badge/?version=latest
   :target: http://lewis.readthedocs.io/en/latest/?badge=latest
.. |Lewis| image:: https://github.com/ess-dmsc/lewis/raw/master/docs/resources/logo/lewis-logo.png
