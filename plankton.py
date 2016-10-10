#!/usr/bin/env python
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

from core.control_server import ControlServer, ExposedObject
from core.simulation import Simulation
from core.utils import get_available_submodules
from devices import import_device
from adapters import import_adapter, get_available_adapters, Adapter

parser = argparse.ArgumentParser(
    description='Run a simulated device and expose it via a specified communication protocol.')

parser.add_argument('-r', '--rpc-host', help='HOST:PORT format string for exposing the device via JSON-RPC over ZMQ.')
parser.add_argument('-s', '--setup', help='Name of the setup to load.', default=None)
parser.add_argument('-l', '--list-protocols', help='List available protocols for selected device.', action='store_true')
parser.add_argument('-p', '--protocol', help='Communication protocol to expose devices.', default=None)
parser.add_argument('-c', '--cycle-delay',
                    help='Approximate time to spend in each cycle of the simulation. Must be greater than 0.',
                    type=float, default=0.1)
parser.add_argument('-e', '--speed', type=float, default=1.0,
                    help='Simulation speed. The actually elapsed time '
                         'between two cycles is multiplied with this speed to determine the simulated time.')
parser.add_argument('device', help='Name of the device to simulate.', default='chopper',
                    choices=get_available_submodules('devices'))
parser.add_argument('adapter_args', nargs='*', help='Arguments for the adapter.')

arguments = parser.parse_args()

# Import the device type and required initialisation parameters.
device_type, parameters = import_device(arguments.device, arguments.setup, device_package='devices')

if arguments.list_protocols:
    adapters = get_available_adapters(arguments.device, device_package='devices')

    protocols = {adapter.protocol for adapter in adapters.values()}

    for p in protocols:
        print(p)
    exit()

device = device_type(**parameters)
adapter = import_adapter(arguments.device, arguments.protocol)(device, arguments.adapter_args)

simulation = Simulation(
    device=device,
    adapter=adapter)

simulation.cycle_delay = arguments.cycle_delay
simulation.speed = arguments.speed

if arguments.rpc_host:
    simulation.control_server = ControlServer(
        {'device': device,
         'simulation': ExposedObject(simulation, exclude=('start', 'control_server'))},
        *arguments.rpc_host.split(':'))

simulation.start()
