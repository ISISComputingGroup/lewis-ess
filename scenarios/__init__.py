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
from simulation.core import CanProcess


def import_device(device_type, scenario):
    module_name = '.{}'.format(scenario)
    scenario_package = 'scenarios.{}'.format(device_type)

    module = importlib.import_module(module_name, scenario_package)

    for module_member in dir(module):
        module_object = getattr(module, module_member)

        if isinstance(module_object, CanProcess):
            return module_object

    raise RuntimeError(
        'Did not find anything that implements CanProcess in module \'{}\'.'.format(scenario_package + module_name))


def import_bindings(device_type, bindings):
    module = importlib.import_module('.bindings', 'scenarios.{}'.format(device_type))

    return getattr(module, bindings)
