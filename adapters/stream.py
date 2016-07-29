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


import asyncore
import asynchat
import socket

from adapters import Adapter
from datetime import datetime


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

        for command, funcname in self.bindings['commands'].iteritems():
            if request.startswith(command):
                func = getattr(self.target, funcname)
                args = request[len(command):]
                reply = func(args) if args else func()

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
            print "Client connect from %s" % repr(addr)
            StreamHandler(sock, self.target, self.bindings)


class StreamAdapter(Adapter):
    def run(self, target, bindings, *args, **kwargs):
        StreamServer("localhost", 9999, target, bindings)

        delta = 0.0  # Delta between cycles
        count = 0  # Cycles per second counter
        timer = 0.0  # Second counter

        while True:
            start = datetime.now()

            asyncore.loop(0.1, count=1)
            target.process(delta)

            delta = (datetime.now() - start).total_seconds()
            count += 1
            timer += delta
            if timer >= 1.0:
                print "Running at %d cycles per second (%.3f ms per cycle)" % (count, 1000.0 / count)
                count = 0
                timer = 0.0
