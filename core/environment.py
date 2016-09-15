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
        self._processing_time = 0.1
        self._cycles_per_second = 0
        self._rpc_server = rpc_server

        self._time_warp_factor = 1.0

        self._total_cycles = 0
        self._total_runtime_real = 0.0
        self._total_runtime_simulation = 0.0

    def run(self):
        delta_simulation = 0.0
        count = 0  # Cycles per second counter
        timer = 0.0  # Second counter

        while True:
            start = datetime.now()

            if self._rpc_server:
                self._rpc_server.process()

            self._adapter.process(delta_simulation, self._processing_time)

            delta_real = (datetime.now() - start).total_seconds()
            delta_simulation = delta_real * self._time_warp_factor

            self._total_runtime_real += delta_real
            self._total_runtime_simulation += delta_simulation
            self._total_cycles += 1

            count += 1
            timer += delta_real
            if timer >= 1.0:
                self._cycles_per_second = count
                count = 0
                timer = 0.0

    @property
    def processing_time(self):
        return self._processing_time

    @processing_time.setter
    def processing_time(self, new_duration):
        if new_duration <= 0:
            raise ValueError('Cycle time must be larger than 0.')

        self._processing_time = new_duration

    @property
    def cycles_per_second(self):
        return self._cycles_per_seconds

    @property
    def time_warp(self):
        return self._time_warp_factor

    @time_warp.setter
    def time_warp(self, new_factor):
        self._time_warp_factor = new_factor

    @property
    def runtime(self):
        return self._total_runtime_real

    @property
    def simulation_runtime(self):
        return self._total_runtime_simulation

    @property
    def simulation_cycles(self):
        return self._total_cycles
