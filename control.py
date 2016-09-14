#!/usr/bin/env python

import argparse
from core.control_client import ControlClient, remote_objects


def list_objects(remote):
    for obj in remote.keys():
        print(obj)


def show_api(remote, object_name):
    if not object_name in remote.keys():
        raise RuntimeError(
            'Object \'{}\' is not exposed by remote. Use -l to get a list of objects.'.format(object_name))

    obj = remote[object_name]

    properties = list(obj._properties)
    methods = []

    for member_name in dir(obj):
        if not member_name[0] in ('_', ':'):
            member = getattr(obj, member_name)

            if callable(member):
                methods.append(member_name)

    print('Type: {}'.format(type(obj).__name__))
    print('Properties:')
    for prop in sorted(properties):
        print('\t{}'.format(prop))
    print('Methods:')
    for method in sorted(methods):
        print('\t{}'.format(method))


def convert_type(value):
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def call_method(remote, object_name, method, arguments):
    if not method:
        raise RuntimeError('Missing object member. Use -a to get a list of members.')

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
    description='A client to manipulate the simulated device remotely through a separate channel. The simulation must be started with the --rpc-host option.')
parser.add_argument('-r', '--rpc-host', default='127.0.0.1:10000',
                    help='HOST:PORT string specifying control server to connect to.')
parser.add_argument('-l', '--list-objects', action='store_true',
                    help='List all objects exposed by the server and exit.')
parser.add_argument('-a', '--show-api', action='store_true',
                    help='List all properties and methods of the controlled object.')
parser.add_argument('object', nargs='?', default='device', help='Object to control.')
parser.add_argument('member', nargs='?', help='Object-member to access.')
parser.add_argument('arguments', nargs='*',
                    help='Arguments to method call. For setting a property, supply the property value. ')

args = parser.parse_args()

remote = remote_objects(ControlClient(*args.rpc_host.split(':')))

if args.list_objects:
    list_objects(remote)
elif args.show_api:
    show_api(remote, args.object)
else:
    print(call_method(remote, args.object, args.member, args.arguments))
