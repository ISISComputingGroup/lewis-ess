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

import argparse
from adapters import import_adapter
from setups import import_device, import_bindings


class StoreNameValuePairs(argparse.Action):
    """
    This class is a slightly modified version of the solution presented in a stackoverflow answer:
        http://stackoverflow.com/a/11762020
    """

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(StoreNameValuePairs, self).__init__(option_strings, dest, nargs=nargs, **kwargs)

        self._param_name = dest

    def __call__(self, parser, namespace, values, option_string=None):
        option_dict = {}
        for option in values.split(','):
            n, v = option.split('=')
            option_dict[n] = v

        setattr(namespace, self._param_name, option_dict)


parser = argparse.ArgumentParser(
    description='Run a simulated device and expose it via a specified communication protocol.')
parser.add_argument('-d', '--device', help='Name of the device to simulate.', default='chopper', choices=['chopper'])
parser.add_argument('-s', '--setup', help='Name of the scenario to run.', default='default')
parser.add_argument('-b', '--bindings', help='Bindings to import from setups.device.bindings. '
                                             'If not specified, this defaults to the value of --protocol.')
parser.add_argument('-p', '--protocol', help='Communication protocol to expose devices.', default='epics',
                    choices=['epics'])
parser.add_argument('-a', '--adapter',
                    help='Name of adapter class. If not specified, the loader will choose '
                         'the first adapter it discovers.')
parser.add_argument('--parameters', help='Additional parameters for the protocol.', action=StoreNameValuePairs)

arguments = parser.parse_args()

CommunicationAdapter = import_adapter(arguments.protocol, arguments.adapter)

bindings = import_bindings(arguments.device, arguments.protocol if arguments.bindings is None else arguments.bindings)
device = import_device(arguments.device, arguments.scenario)

adapter = CommunicationAdapter()
adapter.run(device, bindings, **arguments.parameters)
