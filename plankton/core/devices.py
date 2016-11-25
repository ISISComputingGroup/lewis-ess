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


import importlib

from plankton.adapters import Adapter
from plankton.core.exceptions import PlanktonException
from plankton.core.utils import get_submodules, get_members


class DeviceBase(object):
    """
    This class is a common base for :class:`Device` and :class:`StateMachineDevice`. It is
    mainly used in the device discovery process.
    """


def is_device(obj):
    return isinstance(obj, type) and issubclass(obj, DeviceBase) \
           and obj.__module__ != 'plankton.devices'


def is_adapter(obj):
    return isinstance(obj, type) and issubclass(obj, Adapter) \
           and not obj.__module__.startswith('plankton.adapters')


class DeviceBuilder(object):
    def __init__(self, module):
        self._module = module

        self._device_types = list(get_members(self._module, is_device).values())

        submodules = get_submodules(self._module)
        self._setups_module = submodules.get('setups')
        self._interfaces_module = submodules.get('interfaces')

    @property
    def name(self):
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
        all_interfaces = []

        if self._interfaces_module is not None:
            for interface_module in get_submodules(self._interfaces_module).values():
                all_interfaces += list(get_members(interface_module, is_adapter).values())

        all_interfaces += list(get_members(self._module, is_adapter).values())

        return {interface.protocol: interface for interface in all_interfaces}

    @property
    def protocols(self):
        return self.interfaces.keys()

    @property
    def default_protocol(self):
        interfaces = self.interfaces

        if len(interfaces) == 1:
            return interfaces.keys()[0]

        return None

    @property
    def setups(self):
        all_setups = {}

        if self._setups_module is not None:
            for name, setup_module in get_submodules(self._setups_module).items():
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

    def _create_device_instance(self, device_type, **kwargs):
        if device_type not in self.device_types:
            raise RuntimeError('Can not create instance of non-device type.')

        return device_type(**kwargs)

    def create_device(self, setup=None):
        setups = self.setups

        setup_name = setup if setup is not None else 'default'

        if setup_name not in setups:
            raise PlanktonException(
                'Failed to find setup \'{}\' for device \'{}\'. '
                'Available setups are:\n    {}'.format(
                    setup, self.name, '\n    '.join(setups.keys())))

        setup_data = setups[setup_name]
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
        protocol = protocol if protocol is not None else self.default_protocol

        try:
            return self.interfaces[protocol]
        except KeyError:
            raise PlanktonException(
                'Failed to find protocol \'{}\' for device \'{}\'. '
                'Available protocols are: \n    {}'.format(
                    protocol, self.name, '\n    {}'.join(self.interfaces.keys())))


class DeviceRegistry(object):
    def __init__(self, device_module):
        try:
            self._device_module = importlib.import_module(device_module)
        except ImportError:
            raise PlanktonException(
                'Failed to import module \'{}\' for device discovery. '
                'Make sure that it is in the PYTHONPATH.'.format(device_module))

        self._devices = {name: DeviceBuilder(module) for name, module in
                         get_submodules(self._device_module).items()}

    @property
    def devices(self):
        return self._devices.keys()

    def device_builder(self, name):
        try:
            return self._devices[name]
        except KeyError:
            raise PlanktonException(
                'No device with the name \'{}\' could be found. '
                'Possible names are:\n    {}'.format(name, '\n    '.join(self.devices)))
