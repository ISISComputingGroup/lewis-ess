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

import SocketServer
import re

from adapters import Adapter
from datetime import datetime


class StreamHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        request = self.rfile.readline().strip()
        reply = None

        for command, funcname in self.server.bindings.iteritems():
            if request.startswith(command):
                func = getattr(self.server.target, funcname)
                args = request[len(command):]
                reply = func(args) if args else func()

        """
        if request == "STATE?":
            reply = self.server.target.state + "\n"
        if request == "INIT!":
            self.server.target.initialize()
            reply = "Initializing\n"
        if request == "STATS?":
            speed = self.server.target.speed
            phase = self.server.target.phase
            reply = "%.2f rpm @ %.2f deg\n" % (speed, phase)
        if request.startswith("GO!"):
            m = re.match("GO!(\d+(?:\.\d+)?)@(\d+(?:\.\d+)?)", request)
            if m is None:
                reply = "INVALID FORMAT!\n"
            else:
                self.server.target.targetSpeed = float(m.group(1))
                self.server.target.targetPhase = float(m.group(2))
                self.server.target.start()
                reply = "START COMMANDED!\n"
        """

        if reply is not None:
            self.request.sendall(str(reply))


class StreamAdapter(Adapter):
    def run(self, target, bindings, *args, **kwargs):
        server = SocketServer.TCPServer(("localhost", 9999), StreamHandler)
        server.timeout = 0.1
        server.target = target
        server.bindings = bindings

        delta = 0.0  # Delta between cycles
        count = 0  # Cycles per second counter
        timer = 0.0  # Second counter

        while True:
            start = datetime.now()

            server.handle_request()
            target.process(delta)

            delta = (datetime.now() - start).total_seconds()
            count += 1
            timer += delta
            if timer >= 1.0:
                print "Running at %d cycles per second (%.3f ms per cycle)" % (count, 1000.0 / count)
                count = 0
                timer = 0.0
