# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2017 European Spallation Source ERIC
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
import yaml

from six import string_types
from lewis import __version__
from lewis.core.exceptions import LewisException
from lewis.core.logging import logging, default_log_format
from lewis.core.simulation import SimulationFactory
from lewis.scripts import get_usage_text

parser = argparse.ArgumentParser(
    description='This script starts a simulated device that is exposed via the specified '
                'communication protocol. Complete documentation of Lewis is available in '
                'the online documentation: '
                'https://lewis.readthedocs.io/en/v{}/'.format(__version__),
    add_help=False, prog='lewis')

positional_args = parser.add_argument_group('Positional arguments')

positional_args.add_argument(
    'device', nargs='?',
    help='Name of the device to simulate, omitting this argument prints out a list '
         'of available devices.')

device_args = parser.add_argument_group(
    'Device related parameters',
    'Parameters that influence the selected device, such as setup or protocol.')

device_args.add_argument(
    '-s', '--setup', default=None,
    help='Name of the setup to load. If not provided, the default setup is selected. If there'
         'is no default, a list of setups is printed.')
device_args.add_argument(
    '-p', '--adapter-options', default=None,
    help='Supply the protocol name and adapter options in the format '
         '"name:{opt1: val, opt2: val}". Use the --l flag to see which protocols '
         'are available for the selected device.')
device_args.add_argument(
    '-l', '--list-protocols', action='store_true',
    help='List available protocols for selected device.')
device_args.add_argument(
    '-i', '--show-interface', action='store_true',
    help='Show command interface of device interface.')
device_args.add_argument(
    '-k', '--device-package', default='lewis.devices',
    help='Name of packages where devices are found.')
device_args.add_argument(
    '-a', '--add-path', default=None,
    help='Path where the device package exists. Is added to the path.')

simulation_args = parser.add_argument_group(
    'Simulation related parameters',
    'Parameters that influence the simulation itself, such as timing and speed.')

simulation_args.add_argument(
    '-c', '--cycle-delay', type=float, default=0.1,
    help='Approximate time to spend in each cycle of the simulation. '
         '0 for maximum simulation rate.')
simulation_args.add_argument(
    '-e', '--speed', type=float, default=1.0,
    help='Simulation speed. The actually elapsed time between two cycles is '
         'multiplied with this speed to determine the simulated time.')
simulation_args.add_argument(
    '-r', '--rpc-host', default=None,
    help='HOST:PORT format string for exposing the device and the simulation via '
         'JSON-RPC over ZMQ. Use lewis-control to access this service from the command line.')

other_args = parser.add_argument_group('Other arguments')

other_args.add_argument(
    '-o', '--output-level', default='info',
    choices=['none', 'critical', 'error', 'warning', 'info', 'debug'],
    help='Level of detail for logging to stderr.')
other_args.add_argument(
    '-V', '--verify', action='store_true',
    help='Sets the output level to \'debug\' and aborts before starting the device simulation. '
         'This is intended to help with diagnosing problems with devices or input arguments.')
other_args.add_argument(
    '-v', '--version', action='store_true',
    help='Prints the version and exits.')
other_args.add_argument(
    '-R', '--relaxed-versions', action='store_true',
    help='Allow devices with different framework version to be used.')
other_args.add_argument(
    '-h', '--h', action='help',
    help='Shows this help message and exits.')

__doc__ = 'This script is the main interaction point of the user with Lewis. The usage ' \
          'is as follows:\n\n.. code-block:: none\n\n{}'.format(get_usage_text(parser, indent=4))


def parse_adapter_options(raw_adapter_options):
    protocol = None
    options = {}

    if raw_adapter_options:
        try:
            adapter_options = yaml.load(raw_adapter_options)
        except yaml.YAMLError:
            raise LewisException(
                'It was not possible to parse this adapter option specification:\n'
                '    %s\n'
                'Correct formats for the -p argument are:\n'
                '    -p protocol\n'
                '    -p "protocol: {option: \'val\', option2: 34}"\n'
                'The spaces after the colons are significant!' % raw_adapter_options)

        if isinstance(adapter_options, string_types):
            protocol = adapter_options
            options = {}
        else:
            protocol = list(adapter_options.keys())[0]
            options = adapter_options.get(protocol, {})

    return protocol, options


def run_simulation(argument_list=None):  # noqa: C901
    """
    This is effectively the main function of a typical simulation run. Arguments passed in are
    parsed and used to construct and run the simulation.

    This function only exits when the program has completed or is interrupted.

    :param argument_list: Argument list to pass to the argument parser declared in this module.
    """
    try:
        arguments = parser.parse_args(argument_list or sys.argv[1:])

        if arguments.version:
            print(__version__)
            return

        loglevel = 'debug' if arguments.verify else arguments.output_level
        if loglevel != 'none':
            logging.basicConfig(
                level=getattr(logging, loglevel.upper()), format=default_log_format)

        if arguments.add_path is not None:
            sys.path.append(os.path.abspath(arguments.add_path))

        simulation_factory = SimulationFactory(arguments.device_package,
                                               arguments.relaxed_versions)

        if not arguments.device:
            devices = ['Please specify a device to simulate. The following devices are available:']

            for dev in simulation_factory.devices:
                devices.append('    ' + dev)

            print('\n'.join(devices))
            return

        if arguments.list_protocols:
            print('\n'.join(simulation_factory.get_protocols(arguments.device)))
            return

        protocol, options = parse_adapter_options(arguments.adapter_options)

        simulation = simulation_factory.create(
            arguments.device, arguments.setup, protocol, options, arguments.rpc_host)

        if arguments.show_interface:
            print(simulation._adapters.documentation())
            return

        simulation.cycle_delay = arguments.cycle_delay
        simulation.speed = arguments.speed

        if not arguments.verify:
            try:
                simulation.start()
            except KeyboardInterrupt:
                print('\nInterrupt received; shutting down. Goodbye, cruel world!')
                simulation.log.critical('Simulation aborted by user interaction')

    except LewisException as e:
        print('\n'.join(('An error occurred:', e.message)))
