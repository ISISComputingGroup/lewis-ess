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
from six import iteritems

import asyncore
import asynchat
import socket

from adapters import Adapter
from argparse import ArgumentParser


class StreamHandler(asynchat.async_chat):
    def __init__(self, sock, target, bindings):
        asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator(bindings['meta']['in_terminator'])
        self.target = target
        self.bindings = bindings
        self.buffer = []

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        request = ''.join(self.buffer)
        reply = None
        self.buffer = []

        for command, funcname in iteritems(self.bindings['commands']):
            if request.startswith(command):
                func = getattr(self.target, funcname)
                args = request[len(command):]
                try:
                    reply = func(args) if args else func()
                except Exception:
                    # We're ignoring this temporarily as per Linkam T95 spec
                    # In the long term, we need to come up with a way for the device to decide how errors are handled.
                    pass

        if reply is not None:
            self.push(str(reply) + self.bindings['meta']['out_terminator'])


class StreamServer(asyncore.dispatcher):
    def __init__(self, host, port, target, bindings):
        asyncore.dispatcher.__init__(self)
        self.target = target
        self.bindings = bindings
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print("Client connect from %s" % repr(addr))
            StreamHandler(sock, self.target, self.bindings)


class StreamAdapter(Adapter):
    def __init__(self, target, bindings, arguments):
        super(StreamAdapter, self).__init__(target, bindings, arguments)
        self._options = self._parseArguments(arguments)

        self._server = StreamServer(self._options.bind_address, self._options.port, target, bindings)

    def _parseArguments(self, arguments):
        parser = ArgumentParser(description='Adapter to expose a device via TCP Stream')
        parser.add_argument('-b', '--bind-address', help='IP Address to bind and listen for connections on',
                            default='0.0.0.0')
        parser.add_argument('-p', '--port', help='Port to listen for connections on', type=int, default=9999)
        return parser.parse_args(arguments)

    def process(self, cycle_delay=0.1):
        asyncore.loop(cycle_delay, count=1)
