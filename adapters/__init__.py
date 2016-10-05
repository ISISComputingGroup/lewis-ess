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

    def process(self, cycle_delay=0.1):
        pass


def get_available_adapters(device_name, adapter_module, device_package):
    """

    :param device_name:
    :param adapter_module:
    :param device_package:
    :return:
    """
    adapter_module = importlib.import_module(adapter_module, '{}.{}'.format(device_package, device_name))
    module_members = {member: getattr(adapter_module, member) for member in dir(adapter_module)}

    adapters = dict()
    for name, member in module_members.items():
        try:
            if issubclass(member, Adapter):
                adapters[name] = member
        except TypeError:
            pass

    return adapters


def import_adapter(device_name, protocol_name, adapter_module='.adapters', device_package='devices'):
    """


    :param device_name: Submodule of 'adapters' from which to import the Adapter.
    :param protocol_name: Class name of the Adapter.
    :param adapter_module:
    :param device_package:
    :return: Adapter class.
    """
    available_adapters = get_available_adapters(device_name, adapter_module, device_package='devices')

    for adapter in available_adapters.values():
        if adapter.protocol == protocol_name:
            return adapter

    raise RuntimeError(
        'No suitable adapter found for device \'{}\' and protocol \'{}\'.'.format(device_name, protocol_name))
