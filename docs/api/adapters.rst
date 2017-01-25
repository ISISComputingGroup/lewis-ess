Adapter API
===========

The Adapter API consists of a general :mod:`~lewis.adapters`-module that defines a base class
for all specific adapters. These specific adapters in turn define slightly different utilities
for writing device interfaces.

.. toctree::
    :maxdepth: 2

    adapters/adapters
    adapters/epics
    adapters/modbus
    adapters/stream
