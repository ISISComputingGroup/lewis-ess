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


def import_device(device_type, setup):
    """
    This function is a helper that imports the first object which is an instance of devices.core.CanProcess
    from the setups package:

        from setups.device_type.setup import can_process_object.

    The object is returned by the function, so to import the default setup for chopper:

        chopper = import_device('chopper', 'default')

    :param device_type: Sub-package from which to import the setup.
    :param setup: Setup module from which to import the device object.
    :return: Device object as specified by device_type and setup
    """
    devices = importlib.import_module('devices')
    device_module = importlib.import_module('.{}'.format(device_type), 'devices')

    device_package = 'devices.{}'.format(device_type)
    setup_module = '.setups.{}'.format(setup)

    module = importlib.import_module(setup_module, device_package)

    device_object = getattr(module, 'device')

    if isinstance(device_object, CanProcess):
        return device_object

    raise RuntimeError(
        'Did not find anything that implements CanProcess in module \'{}\'.'.format(setup_package + module_name))


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
    package_name = 'setups.{}'.format(device_type)
    importlib.import_module(package_name)
    module = importlib.import_module('.bindings', package_name)

    return getattr(module, bindings_type)
