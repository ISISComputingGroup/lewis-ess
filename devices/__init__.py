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

    setup_module = 'devices.{}.setups.{}'.format(device_type, setup)

    module = importlib.import_module(setup_module)

    device_object = getattr(module, 'device')

    if isinstance(device_object, CanProcess):
        return device_object

    raise RuntimeError('Device \'{}\'could not be found.'.format(device_type))