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


def import_device(device, setup=None, device_package='devices'):
    setup_name = setup if setup else 'default'

    try:
        setup_module = importlib.import_module('{}.{}.{}.{}'.format(device_package, device, 'setups', setup_name))
        device_type = getattr(setup_module, 'device_type')
        parameters = getattr(setup_module, 'parameters')

        return device_type, parameters
    except (ImportError, AttributeError):
        try:
            device_module = importlib.import_module('{}.{}'.format(device_package, device))

            setups = getattr(device_module, 'setups')

            device_type = setups[setup_name]['device_type']
            parameters = setups[setup_name].get('parameters', {})

            return device_type, parameters
        except (ImportError, AttributeError, KeyError):
            raise RuntimeError('Could not find setup \'{}\' for device \'{}\'.'.format(setup_name, device))
