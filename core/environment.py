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


class SimulationEnvironment(object):
    def __init__(self, adapter, rpc_server=None):
        self._adapter = adapter
        self._cycle_time = 0.1
        self._cycles_per_second = 0
        self._rpc_server = rpc_server

    def run(self):
        delta = 0.0  # Delta between cycles
        count = 0  # Cycles per second counter
        timer = 0.0  # Second counter

        while True:
            start = datetime.now()

            if self._rpc_server:
                self._rpc_server.process()

            self._adapter.process(delta, self._cycle_time)

            delta = (datetime.now() - start).total_seconds()
            count += 1
            timer += delta
            if timer >= 1.0:
                self._cycles_per_second = count
                count = 0
                timer = 0.0

    @property
    def cycle_time(self):
        return self._cycle_time

    @cycle_time.setter
    def cycle_time(self, new_duration):
        if new_duration <= 0:
            raise ValueError('Cycle time must be larger than 0.')

        self._cycle_time = new_duration

    @property
    def cycles_per_second(self):
        return self._cycles_per_second
