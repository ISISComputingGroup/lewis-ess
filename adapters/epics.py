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

from argparse import ArgumentParser

from pcaspy import Driver, SimpleServer

from adapters import Adapter
from core import CanProcess
from core.utils import seconds_since
from datetime import datetime


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
        for pv, parameters in iteritems(self._pv_dict):
            self._timers[pv] += dt
            if self._timers[pv] >= parameters.get('poll_interval', self._default_poll_interval):
                try:
                    self.setParam(pv, getattr(self._target, parameters['property']))
                    self._timers[pv] = 0.0
                except KeyError:
                    pass

        self.updatePVs()


class EpicsAdapter(Adapter):
    def __init__(self, target, bindings, arguments):
        super(EpicsAdapter, self).__init__(target, bindings, arguments)
        self._options = self._parseArguments(arguments)

        self._server = SimpleServer()
        self._server.createPV(prefix=self._options.prefix, pvdb=bindings)
        self._driver = PropertyExposingDriver(target=target, pv_dict=bindings)

        self._last_update = datetime.now()

    def _parseArguments(self, arguments):
        parser = ArgumentParser(description="Adapter to expose a device via EPICS")
        parser.add_argument('-p', '--prefix', help='Prefix to use for all PVs', default='')
        return parser.parse_args(arguments)

    def process(self, cycle_delay=0.1):
        # pcaspy's process() is weird. Docs claim argument is "processing time" in seconds.
        # But this is not at all consistent with the calculated delta.
        # Having "watch caget" running has a huge effect too (runs faster when watching!)
        # Additionally, if you don't call it every ~0.05s or less, PVs stop working. Annoying.
        # Set it to 0.0 for maximum cycle speed.
        self._server.process(cycle_delay)
        self._driver.process(seconds_since(self._last_update))
        self._last_update = datetime.now()
