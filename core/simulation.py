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


class Simulation(object):
    def __init__(self, adapter, control_server=None):
        """
        The Simulation class controls certain aspects of a device simulation,
        the most important one being time.

        Once the start-method is called, the process-method of the device
        is called in regular intervals. The time between these calls is
        influenced by the cycle_delay property. Because of the way some
        network protocols work, the actual processing time can be
        longer or shorter, so cycle_delay should be seen as a guideline
        rather than a guaranteed parameter.

        In the simplest case, the actual time-delta between two cycles
        is passed to the simulated device so that it can update its internal
        state according to the elapsed time. It is however possible to set
        a simulation speed, which serves as a multiplier for this time.
        If the speed is set to 2 and 0.1 seconds pass between two cycles,
        the simulation is asked to simulate 0.2 seconds, and so on. Speed 0
        effectively stops all time dependent calculations in the
        simulated device.

        Another possibility to pause the simulation is the pause-method. After
        calling it, all processing in the communication adapters (and thus,
        possibly also the device) is suspended. This can be used to simulate
        disconnected devices. The simulation can be continued using
        the resume-method.

        A number of status properties provide information about the simulation.
        The total uptime (in actually elapsed time) can be obtained through the
        uptime-property, whereas the runtime-property contains the simulated time.
        The cycles-property indicates the total number of simulation cycles, which
        does not increase when the simulation is paused.

        Finally, the simulation can be stopped entirely with the stop-method.

        All functionality except for the start-method can be made available to remote
        computers via a ControlServer-instance. This can either be passed to __init__
        or set as a property before the simulation has been started.

        :param adapter: Adapter which contains the simulated device.
        :param control_server: ControlServer instance to expose the simulation remotely.
        """
        self._adapter = adapter
        self._control_server = control_server

        self._speed = 1.0  # Multiplier for delta t
        self._cycle_delay = 0.1  # Target time between cycles

        self._start_time = None  # Real time when the simulation started
        self._cycles = 0  # Number of cycles processed
        self._runtime = 0.0  # Total simulation time processed

        self._running = False
        self._started = False
        self._stop_commanded = False

    def start(self):
        """
        Starts the simulation.
        """
        self._running = True
        self._started = True
        self._stop_commanded = False

        self._start_time = datetime.now()

        delta = 0.0

        while not self._stop_commanded:
            delta = self._process_cycle(delta)

        self._running = False
        self._started = False

    def _process_cycle(self, delta):
        """
        Processes one cycle, which consists of one simulation cycle and processing
        of control server commands. The method measures how long all this takes
        and returns the elapsed time in seconds.

        :param delta: Elapsed time in last cycle, passed to simulation.
        :return: Elapsed time in this cycle.
        """
        start = datetime.now()

        self._process_simulation_cycle(delta)

        if self._control_server:
            self._control_server.process()

        delta = seconds_since(start)

        return delta

    def _process_simulation_cycle(self, delta):
        """
        If the simulation is not paused, the device's process-method is
        called with the supplied delta, multiplied by the simulation speed.

        If the simulation is paused, the process sleeps for the duration
        of one cycle_delay.

        :param delta: Time delta passed to simulation.
        """
        delta_simulation = delta * self._speed

        if self._running:
            self._adapter.process(delta_simulation, self._cycle_delay)
            self._cycles += 1
            self._runtime += delta_simulation
        else:
            sleep(self._cycle_delay)

    @property
    def cycle_delay(self):
        """
        Desired time between simulation cycles, this can not be negative.
        Use 0 for highest possible processing rate.
        """
        return self._cycle_delay

    @cycle_delay.setter
    def cycle_delay(self, delay):
        if delay < 0.0:
            raise ValueError('Cycle delay can not be negative.')

        self._cycle_delay = delay

    @property
    def cycles(self):
        """
        Simulation cycles processed since start has been called.
        """
        return self._cycles

    @property
    def uptime(self):
        """
        Elapsed time in seconds since the simulation has been started.
        """
        if not self._started:
            return 0.0
        return seconds_since(self._start_time)

    @property
    def speed(self):
        """
        Simulation speed. Actual elapsed time is multiplied with this property
        to determine simulated time. Values greater than 1 increase the simulation
        speed, values between 1 and 0 decrease it. A speed of 0 effectively pauses
        the simulation.
        """
        return self._speed

    @speed.setter
    def speed(self, new_speed):
        if new_speed < 0:
            raise ValueError('Speed can not be negative.')

        self._speed = new_speed

    @property
    def runtime(self):
        """
        The accumulated simulation time. Whenever speed is different from 1, this
        progresses at a different rate than uptime.
        """
        return self._runtime

    def pause(self):
        """
        Pause the simulation. Can only be called after start has been called.
        """
        if not self._running:
            raise RuntimeError('Can only pause a running simulation.')

        self._running = False

    def resume(self):
        """
        Resume a paused simulation. Can only be called after start
        and pause have been called.
        """
        if not self._started or self._running:
            raise RuntimeError('Can only resume a paused simulation.')

        self._running = True

    def stop(self):
        """
        Stops the simulation entirely.
        """
        self._stop_commanded = True

    @property
    def is_started(self):
        """
        This property is true if the simulation has been started.
        """
        return self._started

    @property
    def is_paused(self):
        """
        True if the simulation is paused (implies that the simulation has been started).
        """
        return self._started and not self._running

    @property
    def control_server(self):
        """
        ControlServer-instance that exposes the object to remote machines. Can only
        be set before start has been called or on a running simulation if no
        control server was previously present.
        """
        return self._control_server

    @control_server.setter
    def control_server(self, control_server):
        if self.is_started and self._control_server:
            raise RuntimeError('Can not replace control server while simulation is running.')
        self._control_server = control_server
