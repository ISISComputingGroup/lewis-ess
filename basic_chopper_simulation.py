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
from scenarios import import_device, import_bindings


class StoreNameValuePair(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        n, v = values.split('=')

        setattr(namespace, n, v)


parser = argparse.ArgumentParser(
    description='Run a simulated device and expose it via a specified communication protocol.')
parser.add_argument('-d', '--device', help='Name of the device to simulate.', default='chopper', choices=['chopper'])
parser.add_argument('-p', '--protocol', help='Communication protocol to expose simulation.', default='epics',
                    choices=['epics'])
parser.add_argument('--parameters', help='Additional parameters for the protocol.', action=StoreNameValuePair,
                    nargs='*')
parser.add_argument('-s', '--scenario', help='Name of the scenario to run.', default='default')

arguments = parser.parse_args()

CommunicationAdapter = import_adapter(arguments.protocol)
bindings = import_bindings(arguments.device, arguments.protocol)
device = import_device(arguments.device, arguments.scenario)

# Run this in terminal window to monitor device:
#   watch -n 0.1 caget SIM:STATE SIM:LAST_COMMAND SIM:SPEED SIM:SPEED:SP SIM:PHASE SIM:PHASE:SP SIM:PARKPOSITION SIM:PARKPOSITION:SP

adapter = CommunicationAdapter(bindings, 'SIM:')
adapter.run(device)
