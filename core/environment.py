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
from core.utils import seconds_since


class SimulationEnvironment(object):
    def __init__(self, adapter, control_server=None):
        self._adapter = adapter
        self._control_server = control_server

        self._speed = 1.0           # Multiplier for delta t
        self._cycle_delay = 0.1     # Target time between cycles

        self._start_time = None     # Real time when the simulation started
        self._cycles = 0            # Number of cycles processed
        self._runtime = 0.0         # Total simulation time processed

        self._running = False
        self._started = False
        self._stop_commanded = False

    def start(self):
        self._running = True
        self._started = True
        self._stop_commanded = False

        self._start_time = datetime.now()

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

        return delta

    def _process_simulation_cycle(self, delta):
        delta_simulation = delta * self._speed

        if self._running:
            self._adapter.process(delta_simulation, self._cycle_delay)
            self._cycles += 1
            self._runtime += delta_simulation
        else:
            sleep(self._cycle_delay)

    @property
    def cycle_delay(self):
        return self._cycle_delay

    @cycle_delay.setter
    def cycle_delay(self, delay):
        if delay < 0.0:
            raise ValueError('Cycle rate must be greater than 0.')

        self._cycle_delay = delay

    @property
    def cycles(self):
        return self._cycles

    @property
    def uptime(self):
        if not self._started:
            return 0.0
        return seconds_since(self._start_time)

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, new_speed):
        if new_speed <= 0:
            raise ValueError('Time warp factor must be greater than 0.')

        self._speed = new_speed

    @property
    def runtime(self):
        return self._runtime

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
