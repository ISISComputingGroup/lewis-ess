# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
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
import os
import sys

from lewis import __version__

from lewis.core.devices import DeviceRegistry
from lewis.core.simulation import Simulation
from lewis.core.exceptions import lewisException

parser = argparse.ArgumentParser(
    description='Run a simulated device and expose it via a specified communication protocol.')

parser.add_argument('-r', '--rpc-host', default=None,
                    help='HOST:PORT format string for exposing the device via '
                         'JSON-RPC over ZMQ.')
parser.add_argument('-s', '--setup', default=None,
                    help='Name of the setup to load.')
parser.add_argument('-l', '--list-protocols',
                    help='List available protocols for selected device.', action='store_true')
parser.add_argument('-i', '--show-interface', action='store_true',
                    help='Show command interface of device interface.')
parser.add_argument('-p', '--protocol', default=None,
                    help='Communication protocol to expose devices.')
parser.add_argument('-c', '--cycle-delay', type=float, default=0.1,
                    help='Approximate time to spend in each cycle of the simulation. '
                         '0 for maximum simulation rate.')
parser.add_argument('-e', '--speed', type=float, default=1.0,
                    help='Simulation speed. The actually elapsed time between two cycles is '
                         'multiplied with this speed to determine the simulated time.')
parser.add_argument('-k', '--device-package', default='lewis.devices',
                    help='Name of packages where devices are found.')
parser.add_argument('-a', '--add-path', default=None,
                    help='Path where the device package exists. Is added to the path.')
parser.add_argument('-v', '--version', action='store_true',
                    help='Prints the version and exits.')

parser.add_argument('device', nargs='?',
                    help='Name of the device to simulate, '
                         'omitting prints list of available devices.')
parser.add_argument('adapter_args', nargs='*',
                    help='Arguments for the adapter.')


def do_run_simulation(argument_list=None):
    arguments = parser.parse_args(argument_list or sys.argv[1:])

    if arguments.version:
        print(__version__)
        return

    if arguments.add_path is not None:
        sys.path.append(os.path.abspath(arguments.add_path))

    device_registry = DeviceRegistry(arguments.device_package)

    if not arguments.device:
        devices = ['Please specify a device to simulate. The following devices are available:']

        for dev in device_registry.devices:
            devices.append('    ' + dev)

        print('\n'.join(devices))
        return

    device_builder = device_registry.device_builder(arguments.device)

    if arguments.list_protocols:
        print('\n'.join(device_builder.protocols))
        return

    device = device_builder.create_device(arguments.setup)
    interface = device_builder.create_interface(arguments.protocol,
                                                device=device, arguments=arguments.adapter_args)

    if arguments.show_interface:
        print(interface.documentation)
        return

    simulation = Simulation(
        device=device,
        adapter=interface,
        control_server=arguments.rpc_host)

    simulation.cycle_delay = arguments.cycle_delay
    simulation.speed = arguments.speed

    simulation.start()


def run_simulation(argument_list=None):
    """
    This function is just a very thin wrapper around do_run_simulation to catch expected
    exceptions that are derived from lewisException.

    :param argument_list: Argument list to pass to the argument parser declared in this module.
    :return:
    """
    try:
        do_run_simulation(argument_list)
    except lewisException as e:
        print('\n'.join(('An error occurred:', e.message)))
