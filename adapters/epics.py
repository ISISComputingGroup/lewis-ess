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

from datetime import datetime
from argparse import ArgumentParser

from pcaspy import Driver, SimpleServer

from adapters import Adapter
from core import CanProcess


class PropertyExposingDriver(CanProcess, Driver):
    def __init__(self, target, pv_dict, default_poll_interval=1.0):
        super(PropertyExposingDriver, self).__init__()

        self._target = target
        self._pv_dict = pv_dict
        self._timers = {k: 0.0 for k in pv_dict.keys()}

        self._default_poll_interval = default_poll_interval

    def write(self, pv, value):
        commands = self._pv_dict[pv].get('commands', {})
        command = commands.get(value, None)

        if command is not None:
            getattr(self._target, command)()
            self.setParam(pv, '')
            self.setParam(self._pv_dict[pv]['buffer'], value)
            return True

        try:
            setattr(self._target, self._pv_dict[pv]['property'], value)
        except (AttributeError, KeyError):
            return False

        self.setParam(pv, value)
        return True

    def doProcess(self, dt):
        # Updates bound parameters as needed
        for pv, parameters in self._pv_dict.iteritems():
            self._timers[pv] += dt
            if self._timers[pv] >= parameters.get('poll_interval', self._default_poll_interval):
                try:
                    self.setParam(pv, getattr(self._target, parameters['property']))
                    self._timers[pv] = 0.0
                except KeyError:
                    pass

        self.updatePVs()


class EpicsAdapter(Adapter):
    def _parseArguments(self, arguments):
        parser = ArgumentParser(description="Adapter to expose a device via EPICS")
        parser.add_argument('-p', '--prefix', help='Prefix to use for all PVs', default='')
        return parser.parse_args(arguments)

    def run(self, target, bindings, prefix):
        server = SimpleServer()
        server.createPV(prefix=prefix, pvdb=bindings)
        driver = PropertyExposingDriver(target=target, pv_dict=bindings)

        delta = 0.0  # Delta between cycles
        count = 0  # Cycles per second counter
        timer = 0.0  # Second counter
        while True:
            start = datetime.now()

            # pcaspy's process() is weird. Docs claim argument is "processing time" in seconds.
            # But this is not at all consistent with the calculated delta.
            # Having "watch caget" running has a huge effect too (runs faster when watching!)
            # Additionally, if you don't call it every ~0.05s or less, PVs stop working. Annoying.
            # Set it to 0.0 for maximum cycle speed.
            server.process(0.1)
            target.process(delta)
            driver.process(delta)

            delta = (datetime.now() - start).total_seconds()
            count += 1
            timer += delta
            if timer >= 1.0:
                print "Running at %d cycles per second (%.3f ms per cycle)" % (count, 1000.0 / count)
                count = 0
                timer = 0.0
