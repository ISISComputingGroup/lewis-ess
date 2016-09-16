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
from time import sleep


def seconds_since(start):
    return (datetime.now() - start).total_seconds()


class SimulationEnvironment(object):
    def __init__(self, adapter, control_server=None):
        self._adapter = adapter
        self._control_server = control_server

        self._processing_time = 0.1

        self._real_cycles = 0
        self._simulation_cycles = 0

        self._real_runtime = 0.0
        self._time_warp_factor = 1.0
        self._simulation_runtime = 0.0

        self._running = False
        self._started = False
        self._stop_commanded = False

    def start(self):
        self._running = True
        self._started = True
        self._stop_commanded = False

        delta = 0.0

        while not self._stop_commanded:  # Could the loop even move out of this class?
            delta = self._process_cycle(delta)

        self._running = False
        self._started = False
        # Should self._stop_commanded be reset here? Not sure...

    def _process_cycle(self, delta):
        start = datetime.now()

        self._process_simulation_cycle(delta)

        if self._control_server:
            self._control_server.process()

        delta = seconds_since(start)

        self._real_cycles += 1
        self._real_runtime += delta

        return delta

    def _process_simulation_cycle(self, delta):
        delta_simulation = delta * self._time_warp_factor

        if self._running:
            self._adapter.process(delta_simulation, self._processing_time)
            self._simulation_cycles += 1
            self._simulation_runtime += delta_simulation
        else:
            sleep(self._processing_time)

    @property
    def processing_time(self):
        return self._processing_time

    @processing_time.setter
    def processing_time(self, new_duration):
        if new_duration <= 0:
            raise ValueError('Cycle time must be greater than 0.')

        self._processing_time = new_duration

    @property
    def cycles(self):
        return self._real_cycles

    @property
    def simulation_cycles(self):
        return self._simulation_cycles

    @property
    def runtime(self):
        return self._real_runtime

    @property
    def time_warp(self):
        return self._time_warp_factor

    @time_warp.setter
    def time_warp(self, new_factor):
        if new_factor <= 0:
            raise ValueError('Time warp factor must be greater than 0.')

        self._time_warp_factor = new_factor

    @property
    def simulation_runtime(self):
        return self._simulation_runtime

    def pause(self):
        if not self._running:
            raise RuntimeError('Can only pause a running simulation.')

        self._running = False

    def resume(self):
        if not self._started or self._running:
            raise RuntimeError('Can only resume a paused simulation.')

        self._running = True

    def stop(self):
        self._stop_commanded = True

    @property
    def is_started(self):
        return self._started

    @property
    def is_paused(self):
        return self._started and not self._running

    @property
    def control_server(self):
        return self._control_server

    @control_server.setter
    def control_server(self, control_server):
        if self.is_started and self._control_server:
            raise RuntimeError('Can not replace control server while simulation is running.')
        self._control_server = control_server
