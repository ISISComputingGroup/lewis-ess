# -*- coding: utf-8 -*-
# *********************************************************************
# plankton - a library for creating hardware device simulators
# Copyright (C) 2016 European Spallation Source ERIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *********************************************************************

"""
This module contains :class:`DeviceBase` as a base class for other device classes and
infrastructure that can import devices from a module (:class:`DeviceRegistry`). The latter also
produces factory-like objects that create device instances and interface types based on setups
(:class:`DeviceBuilder`).
"""

import importlib

from plankton.adapters import Adapter
from plankton.core.exceptions import PlanktonException
from plankton.core.utils import get_submodules, get_members


class DeviceBase(object):
    """
    This class is a common base for :class:`~plankton.devices.Device` and
    :class:`~plankton.devices.StateMachineDevice`. It is mainly used in the device
    discovery process.
    """


def is_device(obj):
    """
    Returns True if obj is a device type (derived from DeviceBase), but not defined in
    :mod:`plankton.core.devices` or :mod:`plankton.devices`.

    :param obj: Object to test.
    :return: True if obj is a device type.
    """
    return isinstance(obj, type) and issubclass(
        obj, DeviceBase) and obj.__module__ not in ('plankton.devices', 'plankton.core.devices')


def is_adapter(obj):
    """
    Returns True if obj is an interface (derived from Adapter), but not defined in
    :mod:`plankton.adapters`.

    :param obj: Object to test.
    :return: True if obj is an interface type.
    """
    return isinstance(obj, type) and issubclass(
        obj, Adapter) and not obj.__module__.startswith('plankton.adapters')


class DeviceBuilder(object):
    """
    This class takes a module object (for example imported via importlib.import_module or via the
    :class:`DeviceRegistry`) and inspects it so that it's possible to construct devices and
    interfaces.

    In order for the class to work properly, the device module has to adhere to a few rules.
    Device types, which means classes inheriting from :class:`DeviceBase`, are imported directly
    from the device module, equivalent to the following:

    .. sourcecode :: Python

        from device_name import SimulatedDeviceType

    If ``SimulatedDeviceType`` is defined in the ``__init__.py``, there's nothing else to do. If
    the device class is defined elsewhere, it must be imported in the ``__init__.py`` file as
    written above. If there is only one device type (which is probably the most common case), it is
    assumed to be default device type.

    Setups are discovered in two locations, the first one is a dict called ``setups`` in the device
    module, which must contain setup names as keys and as values again a dict. This inner dict has
    one mandatory key called ``device_type`` and one optional key ``parameters`` containing the
    constructor arguments for the specified device type:

    .. sourcecode:: Python

        setups = dict(
            broken=dict(
                device_type=SimulatedDeviceType,
                parameters=dict(
                    override_initial_state='error',
                    override_initial_data=dict(
                        target=-10, position=-20.0))))

    The other location is a sub-package called `setups`, which should in turn contain modules. Each
    module must contain a variable ``device_type`` and a variable ``parameters`` which are
    analogous to the keys in the dict described above. This allows for more complex setups which
    define additional classes and so on.

    The ``default`` setup is special, it is used when no setup is supplied to
    :meth:`create_device`. If the setup ``default`` is not defined, one is created with the default
    device type. This has two consequences, no setups need to be defined for very simple devices,
    but if multiple device types are defined, a ``default`` setup must be defined.

    A setup can be supplied to the :meth:`create_device`.

    Lastly, the builder tries to discover device interfaces, which are currently classes based on
    :class:`plankton.adapters.Adapter`. These are looked for in the module and in a sub-package
    called ``interfaces`` (which should contain modules with adapters like the ``setups`` package).

    Each interface has a protocol, if a protocol occurs more than once in a device module,
    a RuntimeError is raised.
    """

    def __init__(self, module):
        self._module = module

        self._device_types = list(get_members(self._module, is_device).values())

        submodules = get_submodules(self._module)

        self._setups = self._discover_setups(submodules.get('setups'))
        self._interfaces = self._discover_interfaces(submodules.get('interfaces'))

    def _discover_setups(self, setups_module):
        all_setups = {}

        if setups_module is not None:
            for name, setup_module in get_submodules(setups_module).items():
                all_setups[name] = {
                    'device_type': getattr(setup_module, 'device_type', self.default_device_type),
                    'parameters': getattr(setup_module, 'parameters', {})
                }

        setups = getattr(self._module, 'setups', {})

        if isinstance(setups, dict):
            all_setups.update(setups)

        if 'default' not in all_setups:
            all_setups['default'] = {'device_type': self.default_device_type}

        return all_setups

    def _discover_interfaces(self, interfaces_module):
        all_interfaces = []

        if interfaces_module is not None:
            for interface_module in get_submodules(interfaces_module).values():
                all_interfaces += list(get_members(interface_module, is_adapter).values())

        all_interfaces += list(get_members(self._module, is_adapter).values())

        interfaces = {}
        for interface in all_interfaces:
            existing_interface = interfaces.get(interface.protocol)

            if existing_interface is not None:
                raise RuntimeError(
                    'The protocol \'{}\' is defined in two interfaces:\n'
                    '    {} (in {})\n'
                    '    {} (in {})\n'
                    'One of the protocol names needs to be changed.'.format(
                        interface.protocol, existing_interface.__name__,
                        existing_interface.__module__, interface.__name__, interface.__module__))

            interfaces[interface.protocol] = interface

        return interfaces

    @property
    def name(self):
        """
        The name of the device, which is also the name of the device module.
        """
        return self._module.__name__.split('.')[-1]

    @property
    def device_types(self):
        """
        This property contains a dict of all device types in the device module. The keys are
        type names, the values are the types themselves.
        """
        return self._device_types

    @property
    def default_device_type(self):
        """
        If the module only defines one device type, it is the default device type. It is used
        whenever a setup does not provide a ``device_type``.
        """
        if len(self.device_types) == 1:
            return self.device_types[0]

        return None

    @property
    def interfaces(self):
        """
        This property contains a map with protocols as keys and interface types as values.
        The types are imported from the ``interfaces`` sub-module and from the device module
        itself. If two interfaces with the same protocol are discovered, a RuntimeError is raiesed.
        """
        return self._interfaces

    @property
    def protocols(self):
        """All available protocols for this device."""
        return list(self.interfaces.keys())

    @property
    def default_protocol(self):
        """In case only one protocol exists for the device, this is the default protocol."""
        if len(self.protocols) == 1:
            return self.protocols[0]

        return None

    @property
    def setups(self):
        """
        A map with all available setups. Setups are imported from the ``setups`` dictionary
        in a device module and from the ``setups`` sub-module. If no ``default``-setup exists,
        one is created using the default_device_type. If there are several device types in
        the module, the default setup must be provided explicitly.
        """
        return self._setups

    def _create_device_instance(self, device_type, **kwargs):
        if device_type not in self.device_types:
            raise RuntimeError('Can not create instance of non-device type.')

        return device_type(**kwargs)

    def create_device(self, setup=None):
        """
        Creates a device object according to the provided setup. If no setup is provided,
        the default setup is used. If the setup can't be found, a PlanktonException is raised.
        This can also happen if the device type specified in the setup is invalid.

        :param setup: Name of the setup from which to create device.
        :return: Device object initialized according to the provided setup.
        """
        setup_name = setup if setup is not None else 'default'

        if setup_name not in self.setups:
            raise PlanktonException(
                'Failed to find setup \'{}\' for device \'{}\'. '
                'Available setups are:\n    {}'.format(
                    setup, self.name, '\n    '.join(self.setups.keys())))

        setup_data = self.setups[setup_name]
        device_type = setup_data.get('device_type') or self.default_device_type

        try:
            return self._create_device_instance(
                device_type, **setup_data.get('parameters', {}))
        except RuntimeError:
            raise PlanktonException(
                'The setup \'{}\' you tried to load does not specify a valid device type, but the '
                'device module \'{}\' provides multiple device types so that no meaningful '
                'default can be deduced.'.format(setup_name, self.name))

    def create_interface_type(self, protocol=None):
        """
        Returns an interface type that implements the provided protocol. If the protocol is not
        known, a PlanktonException is raised.

        .. note::

            This method returns an interface *type*. The interface must be constructed explicitly.

        :param protocol: Protocol which the interface must implement.
        :return: Interface type.
        """
        protocol = protocol if protocol is not None else self.default_protocol

        try:
            return self.interfaces[protocol]
        except KeyError:
            raise PlanktonException(
                'Failed to find protocol \'{}\' for device \'{}\'. '
                'Available protocols are: \n    {}'.format(
                    protocol, self.name, '\n    {}'.join(self.interfaces.keys())))


class DeviceRegistry(object):
    """
    This class takes the name of a module and constructs a :class:`DeviceBuilder` from
    each sub-module. The available devices can be queried and a DeviceBuilder can be
    obtained for each device:

    .. sourcecode:: Python

        from plankton.core.devices import DeviceRegistry

        registry = DeviceRegistry('plankton.devices')
        chopper_builder = registry.device_builder('chopper')

        # construct device, interface, ...

    If the module can not be imported, a PlanktonException is raised.

    :param device_module: Name of device module from which devices are loaded.
    """

    def __init__(self, device_module):
        try:
            self._device_module = importlib.import_module(device_module)
        except ImportError:
            raise PlanktonException(
                'Failed to import module \'{}\' for device discovery. '
                'Make sure that it is in the PYTHONPATH.\n'
                'See also the -a option of plankton.'.format(device_module))

        self._devices = {name: DeviceBuilder(module) for name, module in
                         get_submodules(self._device_module).items()}

    @property
    def devices(self):
        """All available device names."""
        return self._devices.keys()

    def device_builder(self, name):
        """
        Returns a :class:`DeviceBuilder` instance that can be used to create device objects
        based on setups, as well as device interfaces. If the device name is not stored
        in the internal map, a PlanktonException is raised.

        :param name: Name of the device.
        :return: :class:`DeviceBuilder`-object for requested device.
        """
        try:
            return self._devices[name]
        except KeyError:
            raise PlanktonException(
                'No device with the name \'{}\' could be found. '
                'Possible names are:\n    {}\n'
                'See also the -k option to add inspect a different module.'.format(
                    name, '\n    '.join(self.devices)))
