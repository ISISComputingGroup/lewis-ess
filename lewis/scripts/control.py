#!/usr/bin/env python
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
import ast
import sys

from lewis.core.control_client import ControlClient
from lewis.scripts import get_usage_text


def list_objects(remote):
    for obj in remote.keys():
        print(obj)


def show_api(remote, object_name):
    if object_name not in remote.keys():
        raise RuntimeError(
            'Object \'{}\' is not exposed by remote.'.format(object_name))

    obj = remote[object_name]

    properties = list(obj._properties)
    methods = []

    for member_name in dir(obj):
        if member_name[0] not in ('_', ':') and member_name not in dir(type(obj)):
            methods.append(member_name)

    print('Type: {}'.format(type(obj).__name__))

    print('Properties (current values):')
    maxlen = len(max(properties, key=len))
    for prop in sorted(properties):
        try:
            current_value = getattr(obj, prop)
        except Exception as e:
            current_value = 'Not accessible: {}'.format(e)

        print('    {}    ({})'.format(prop.ljust(maxlen), current_value))

    print('Methods:')
    for method in sorted(methods):
        print('    {}'.format(method))


def convert_type(value):
    try:
        return ast.literal_eval(value)
    except ValueError:
        return value


def call_method(remote, object_name, method, arguments):
    if not method:
        raise RuntimeError('Missing object member, can not make call.')

    attr = getattr(remote[object_name], method)
    args = [convert_type(arg) for arg in arguments]

    if callable(attr):
        return attr(*args)
    else:
        if not arguments:
            return attr
        else:
            setattr(remote[object_name], method, *args)


parser = argparse.ArgumentParser(
    description='A client to manipulate the simulated device remotely through a separate '
                'channel. For this tool to be of any use, lewis must be invoked with the '
                '-r/--rpc-host option.',
    add_help=False, prog='lewis-control')

positional_args = parser.add_argument_group('Positional arguments')
positional_args.add_argument(
    'object', nargs='?', default=None,
    help='Object to control. If left out, all objects are listed.')
positional_args.add_argument(
    'member', nargs='?', default=None,
    help='Object-member to access. If omitted, API of the object is listed.')
positional_args.add_argument(
    'arguments', nargs='*',
    help='Arguments to method call. For setting a property, '
         'supply the property value. ')

optional_args = parser.add_argument_group('Optional arguments')
optional_args.add_argument(
    '-r', '--rpc-host', default='127.0.0.1:10000',
    help='HOST:PORT string specifying control server to connect to.')
optional_args.add_argument(
    '-n', '--print-none', action='store_true',
    help='By default, no output is generated if the remote function returns None. '
         'Specifying this flag will force the client to print those None-values.')
optional_args.add_argument(
    '-h', '--h', action='help',
    help='Shows this help message and exits.')

__doc__ = 'To interact with the control server of a running simulation, use this script. ' \
          'Usage:\n\n.. code-block:: none\n\n{}'.format(get_usage_text(parser, indent=4))


def control_simulation(argument_list=None):
    args = parser.parse_args(argument_list or sys.argv[1:])

    remote = ControlClient(*args.rpc_host.split(':')).get_object_collection()

    if not args.object:
        list_objects(remote)
    else:
        if not args.member:
            show_api(remote, args.object)
        else:
            response = call_method(remote, args.object, args.member, args.arguments)

            if response is not None or args.print_none:
                print(response)
