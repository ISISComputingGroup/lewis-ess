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

from core import CanProcess


def import_device(device_type, scenario):
    """
    This function is a helper that imports the first object which is an instance of devices.core.CanProcess
    from the setups package:

        from setups.device_type.scenario import can_process_object.

    The object is returned by the function, so to import the default scenario for chopper:

        chopper = import_device('chopper', 'default')

    :param device_type: Sub-package from which to import the scenario.
    :param scenario: Scenario module from which to import the device object.
    :return: Device object as specified by device_type and scenario
    """
    module_name = '.{}'.format(scenario)
    scenario_package = 'setups.{}'.format(device_type)

    module = importlib.import_module(module_name, scenario_package)

    for module_member in dir(module):
        module_object = getattr(module, module_member)

        if isinstance(module_object, CanProcess):
            return module_object

    raise RuntimeError(
        'Did not find anything that implements CanProcess in module \'{}\'.'.format(scenario_package + module_name))


def import_bindings(device_type, bindings_type):
    """
    This function imports a variable named bindings_type from setups.device_type.bindings.
    This relies on the convention that the name of the bindings-variable has the same name as the
    communication protocol it addresses. For example, importing the EPICS bindings for simulated choppers:

        bindings = import_bindings('chopper', 'epics')

    This is equivalent to:

        from setups.chopper.bindings import epics as bindings

    :param device_type: Device for which the bindings are written
    :param bindings_type: Name of the variable to import as bindings
    :return: Variable that specifies the binding.
    """
    module = importlib.import_module('.bindings', 'setups.{}'.format(device_type))

    return getattr(module, bindings_type)
