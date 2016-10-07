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

        for regex, funcname in self.target._bindings:
            match = regex.match(request)
            if match:
                groups = match.groups()
                func = getattr(self.target, funcname)
                try:
                    reply = func(*groups)
                except Exception as error:
                    reply = self.target.handle_error(request, error)

                break

        if reply is not None:
            self.push(b(str(reply) + self.target.out_terminator))


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
    def __init__(self, target_method, regex, **re_args):
        self.method = target_method
        self.pattern = regex
        self.re_args = re_args


class StreamAdapter(Adapter):
    protocol = 'stream'

    in_terminator = '\r'
    out_terminator = '\r'

    commands = None

    def __init__(self, device, arguments=None):
        super(StreamAdapter, self).__init__(device, arguments)
        self._options = self._parseArguments(arguments)

        self._server = None
        self._bindings = None

        self._create_bindings(self.commands)

    def start_server(self):
        self._server = StreamServer(self._options.bind_address, self._options.port, self)

    def _parseArguments(self, arguments):
        parser = ArgumentParser(description='Adapter to expose a device via TCP Stream')
        parser.add_argument('-b', '--bind-address', help='IP Address to bind and listen for connections on',
                            default='0.0.0.0')
        parser.add_argument('-p', '--port', help='Port to listen for connections on', type=int, default=9999)
        return parser.parse_args(arguments)

    def _create_bindings(self, cmds):
        self._bindings = []

        for cmd in cmds:
            method = cmd.method

            if not method in dir(self):
                if not method in dir(self._device):
                    raise AttributeError('Can not find method \'' + method + '\' in device or adapter.')

                setattr(self, method, ForwardMethod(self._device, method))

            self._bindings.append(
                (re.compile(b(cmd.pattern), **cmd.re_args), cmd.method))

    def handle_error(self, request, error):
        pass

    def handle(self, cycle_delay=0.1):
        asyncore.loop(cycle_delay, count=1)
