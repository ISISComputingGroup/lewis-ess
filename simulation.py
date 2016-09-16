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
from core.utils import get_available_submodules
from core.control_server import ControlServer, ExposedObject
from core.environment import SimulationEnvironment

from adapters import import_adapter
from setups import import_device, import_bindings

parser = argparse.ArgumentParser(
    description='Run a simulated device and expose it via a specified communication protocol.')
parser.add_argument('-d', '--device', help='Name of the device to simulate.', default='chopper',
                    choices=get_available_submodules('setups'))
parser.add_argument('-r', '--rpc-host', help='HOST:PORT format string for exposing the device via JSON-RPC over ZMQ.')
parser.add_argument('-s', '--setup', help='Name of the setup to load.', default='default')
parser.add_argument('-b', '--bindings', help='Bindings to import from setups.device.bindings. '
                                             'If not specified, this defaults to the value of --protocol.')
parser.add_argument('-p', '--protocol', help='Communication protocol to expose devices.', default='epics',
                    choices=get_available_submodules('adapters'))
parser.add_argument('-a', '--adapter',
                    help='Name of adapter class. If not specified, the loader will choose '
                         'the first adapter it discovers.')
parser.add_argument('adapter_args', nargs='*', help='Arguments for the adapter.')

arguments = parser.parse_args()

CommunicationAdapter = import_adapter(arguments.protocol, arguments.adapter)

bindings = import_bindings(arguments.device, arguments.protocol if arguments.bindings is None else arguments.bindings)
device = import_device(arguments.device, arguments.setup)

control_server = ControlServer({'device': device}, *arguments.rpc_host.split(':')) if arguments.rpc_host else None

environment = SimulationEnvironment(
    adapter=CommunicationAdapter(device, bindings, arguments.adapter_args),
    control_server=control_server)

control_server._rpc_object_collection.add_object(
    obj=ExposedObject(environment, exclude=('start',)), name='environment')

environment.start()
