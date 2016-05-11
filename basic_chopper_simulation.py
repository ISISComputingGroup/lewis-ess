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

from importlib import import_module
from adapters import Adapter
from simulation.core import CanProcess


def get_adapter_from_module(module_name):
    module = import_module('.{}'.format(module_name), 'adapters')

    for module_member in dir(module):
        module_object = getattr(module, module_member)

        try:
            if issubclass(module_object, Adapter) and module_object != Adapter:
                return module_object
        except TypeError:
            pass

    raise RuntimeError('No suitable Adapter found in module \'{}\''.format(module_name))


def get_bindings_from_module(device_type, bindings):
    module = import_module('.bindings', 'scenarios.{}'.format(device_type))

    return getattr(module, bindings)


def get_scenario_device(device_type, scenario):
    module = import_module('.{}'.format(scenario), 'scenarios.{}'.format(device_type))

    for module_member in dir(module):
        module_object = getattr(module, module_member)

        if isinstance(module_object, CanProcess):
            return module_object

    raise RuntimeError('Did not find anything that implements CanProcess.')


CommunicationAdapter = get_adapter_from_module('epics')
bindings = get_bindings_from_module('chopper', 'epics')
device = get_scenario_device('chopper', 'default')

prefix = 'SIM:'

# Run this in terminal window to monitor device:
#   watch -n 0.1 caget SIM:STATE SIM:LAST_COMMAND SIM:SPEED SIM:SPEED:SP SIM:PHASE SIM:PHASE:SP SIM:PARKPOSITION SIM:PARKPOSITION:SP

adapter = CommunicationAdapter(bindings, prefix)
adapter.run(device)
