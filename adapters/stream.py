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

from __future__ import print_function

from six import b

import asyncore
import asynchat
import socket

from adapters import Adapter, ForwardMethod
from argparse import ArgumentParser

import re


class StreamHandler(asynchat.async_chat):
    def __init__(self, sock, target):
        asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator(b(target.in_terminator))
        self.target = target
        self.buffer = []

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        request = b''.join(self.buffer)
        reply = None
        self.buffer = []

        try:
            match = None
            for cmd in self.target.commands:
                match = cmd.pattern.match(request)
                if match:
                    groups = match.groups()
                    func = getattr(self.target, cmd.method)

                    args = groups if not cmd.argument_mappings else [f(a) for f, a in
                                                                     zip(cmd.argument_mappings, groups)]
                    reply = cmd.return_mapping(func(*args))
                    break

            if match is None:
                raise RuntimeError('None of the device\'s commands matched.')

        except Exception as error:
            reply = self.target.handle_error(request, error)

        if reply is not None:
            self.push(b(reply + self.target.out_terminator))


class StreamServer(asyncore.dispatcher):
    def __init__(self, host, port, target):
        asyncore.dispatcher.__init__(self)
        self.target = target
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print("Client connect from %s" % repr(addr))
            StreamHandler(sock, self.target)


class Cmd(object):
    def __init__(self, target_method, regex, argument_mappings=None,
                 return_mapping=lambda x: None if x is None else str(x)):
        """
        This is a small helper class that makes it easy to define commands that are parsed
        by StreamAdapter and forwarded to the correct methods on the Adapter.

        Method arguments are indicated by groups in the regular expression. The number of
        groups has to match the number of arguments of the method. The optional argument_mappings
        can be an iterable of callables with one parameter of the same length as the
        number of arguments of the method. The first parameter will be transformed using the
        first function, the second using the second function and so on. This can be useful
        to automatically transform strings provided by the adapter into a proper data type
        such as int or float before they are passed to the method.

        The return_mapping argument is similar, it should map the return value of the method
        to a string. The default map function only does that when the supplied value
        is not None.

        :param target_method: Method to be called when regex matches.
        :param regex: Regex to match for method call.
        :param argument_mappings: Iterable with mapping functions from string to some type.
        :param return_mapping: Mapping function for return value of method.
        """
        self.method = target_method
        self.pattern = re.compile(b(regex))

        if argument_mappings is not None and (self.pattern.groups != len(argument_mappings)):
            raise RuntimeError(
                'Expected {} argument mapping(s), got {}'.format(self.pattern.groups, len(argument_mappings)))

        self.argument_mappings = argument_mappings
        self.return_mapping = return_mapping


class StreamAdapter(Adapter):
    protocol = 'stream'

    in_terminator = '\r'
    out_terminator = '\r'

    commands = None

    def __init__(self, device, arguments=None):
        super(StreamAdapter, self).__init__(device, arguments)

        if arguments is not None:
            self._options = self._parseArguments(arguments)

        self._server = None

        self._create_properties(self.commands)

    def start_server(self):
        self._server = StreamServer(self._options.bind_address, self._options.port, self)

    def _parseArguments(self, arguments):
        parser = ArgumentParser(description='Adapter to expose a device via TCP Stream')
        parser.add_argument('-b', '--bind-address', help='IP Address to bind and listen for connections on',
                            default='0.0.0.0')
        parser.add_argument('-p', '--port', help='Port to listen for connections on', type=int, default=9999)
        return parser.parse_args(arguments)

    def _create_properties(self, cmds):
        patterns = set()
        for cmd in cmds:
            method = cmd.method

            if not method in dir(self):
                if not method in dir(self._device):
                    raise AttributeError('Can not find method \'' + method + '\' in device or adapter.')

                setattr(self, method, ForwardMethod(self._device, method))

            if cmd.pattern.pattern in patterns:
                raise RuntimeError(
                    'The regular expression \'{}\' is associated with multiple methods.'.format(cmd.pattern.pattern))

            patterns.add(cmd.pattern.pattern)

        if len(patterns) < len(cmds):
            raise RuntimeError('Warning')

    def handle_error(self, request, error):
        pass

    def handle(self, cycle_delay=0.1):
        asyncore.loop(cycle_delay, count=1)
