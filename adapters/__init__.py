#  -*- coding: utf-8 -*-
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


class Adapter(object):
    protocol = None

    def __init__(self, device, arguments):
        self._device = device

    def handle(self, cycle_delay=0.1):
        pass


def get_available_adapters(device_name, device_package):
    """
    This helper function returns a dictionary with name/type pairs. It imports the module
    device_package.device_name.adapters and puts those members of the module that inherit
    from Adapter into the dictionary.

    :param device_name: Device name for which to get the adapters.
    :param device_package: Name of the package where devices are defined.
    :return: Dictionary of name/type pairs for available adapters for that device.
    """
    adapter_module = importlib.import_module('{}.{}.{}'.format(device_package, device_name, 'adapters'))
    module_members = {member: getattr(adapter_module, member) for member in dir(adapter_module)}

    adapters = dict()
    for name, member in module_members.items():
        try:
            if issubclass(member, Adapter):
                adapters[name] = member
        except TypeError:
            pass

    return adapters


def import_adapter(device_name, protocol_name, device_package='devices'):
    """
    This function tries to import an adapter for the given device that implements
    the requested protocol. If no adapter for that protocol exists, an exception
    is raised. If protocol name is None, the function returns an
    unspecified adapter. If no adapters are found at all, an error is raised.

    :param device_name: Name of device for which an adapter is requested.
    :param protocol_name: Requested protocol implemented by adapter.
    :param device_package: Name of the package where devices are defined.
    :return: Adapter class that implements requested protocol for the specified device.
    """
    available_adapters = get_available_adapters(device_name, device_package)

    if not protocol_name:
        return list(available_adapters.values())[0]

    for adapter in available_adapters.values():
        if adapter.protocol == protocol_name:
            return adapter

    raise RuntimeError(
        'No suitable adapter found for device \'{}\' and protocol \'{}\'.'.format(device_name, protocol_name))
