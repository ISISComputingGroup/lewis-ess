# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2017 European Spallation Source ERIC
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

"""
A :class:`~Simulation` combines a :mod:`Device <lewis.devices>` and its interface (derived from
an :mod:`Adapter <lewis.adapters>`).
"""

from datetime import datetime

from lewis.core.adapters import AdapterCollection
from lewis.core.control_server import ControlServer, ExposedObject
from lewis.core.logging import has_log
from lewis.core.utils import seconds_since


@has_log
class Simulation(object):
    """
    The Simulation class controls certain aspects of a device simulation,
    the most important one being time.

    Once :meth:`start` is called, the process-method of the device
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
    computers via a :class:`ControlServer`-instance. The way to expose device and simulation
    is to pass a 'host:port'-string as the control_server argument,
    which will construct the control server. Simulation will try to start the
    control server using the start_server method.

    :param device: The simulated device.
    :param adapter: Adapter which contains the simulated device.
    :param control_server: 'host:port'-string to construct control server or None.
    """

    def __init__(self, device, adapter, device_builder=None, control_server=None):
        super(Simulation, self).__init__()

        self._device_builder = device_builder

        self._device = device
        self._adapters = AdapterCollection(adapter)

        self._speed = 1.0  # Multiplier for delta t
        self._cycle_delay = 0.1  # Target time between cycles

        self._start_time = None  # Real time when the simulation started
        self._cycles = 0  # Number of cycles processed
        self._runtime = 0.0  # Total simulation time processed

        self._running = False
        self._started = False
        self._stop_commanded = False

        # Constructing the control server must be deferred until the end,
        # because the construction is not complete at this point
        self._control_server = None  # Just initialize to None and use property setter afterwards
        self.control_server = control_server

    def _create_control_server(self, control_server):
        if control_server is None:
            return None

        return ControlServer({
            'device': ExposedObject(
                self._device,
                exclude_inherited=True
            ),
            'simulation': ExposedObject(
                self,
                exclude=('start', 'control_server', 'log'),
                exclude_inherited=True
            ),
            'interface': ExposedObject(
                self._adapters,
                exclude=('device', 'add_adapter', 'remove_adapter', 'handle', 'log'),
                exclude_inherited=True
            )},
            control_server)

    @property
    def setups(self):
        """
        A list of setups that are available. Use :meth:`switch_setup` to
        change the setup.
        """
        return list(self._device_builder.setups.keys()) if self._device_builder is not None else []

    def switch_setup(self, new_setup):
        """
        This method switches the setup, which means that it replaces the currently
        simulated device with a new device, as defined by the setup.

        If any error occurs during setup switching it is logged and re-raised.

        :param new_setup: Name of the new setup to load.
        """
        try:
            self._device = self._device_builder.create_device(new_setup)
            self._adapters.device = self._device
            self.log.info('Switched setup to \'%s\'', new_setup)
        except Exception as e:
            self.log.error(
                'Caught an error while trying to switch setups. Setup not switched, '
                'simulation continues: %s', e)
            raise

    def start(self):
        """
        Starts the simulation.
        """
        self.log.info('Starting simulation')

        self._running = True
        self._started = True
        self._stop_commanded = False

        if self._control_server is not None:
            self._control_server.start_server()

        self._adapters.connect()

        self._start_time = datetime.now()

        delta = 0.0

        while not self._stop_commanded:
            delta = self._process_cycle(delta)

        self._running = False
        self._started = False

        self._adapters.disconnect()

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
        self.log.debug('Cycle, dt=%s', delta)

        self._adapters.handle(self._cycle_delay)

        if self._running:
            delta_simulation = delta * self._speed
            self._device.process(delta_simulation)

            self._cycles += 1
            self._runtime += delta_simulation

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

        self.log.info('Changed cycle delay to %s', self._cycle_delay)

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

        self.log.info('Changed speed to %s', self._speed)

    @property
    def runtime(self):
        """
        The accumulated simulation time. Whenever speed is different from 1, this
        progresses at a different rate than uptime.
        """
        return self._runtime

    def set_device_parameters(self, parameters):
        """
        Set multiple parameters of the simulated device "simultaneously". The passed
        parameter is assumed to be device parameter/value dict.
        The method only allows to set existing attributes. If there are invalid
        attribute names, the attributes are not updated, instead a RuntimeError
        is raised. The same happens if any of the parameters are methods, which
        can not be updated with this mechanisms.

        :param parameters: Dict of device attribute/values to update the device.
        """
        invalid_parameters = set(parameters.keys()) - set(
            x for x in dir(self._device) if not callable(getattr(self._device, x)))
        if invalid_parameters:
            raise RuntimeError(
                'The following parameters do not exist in the device or are methods: {}.'
                'Parameters not updated.'.format(invalid_parameters))

        for name, value in parameters.items():
            setattr(self._device, name, value)

        self.log.debug('Updated device parameters: %s', parameters)

    def pause(self):
        """
        Pause the simulation. Can only be called after start has been called.
        """
        if not self._running:
            raise RuntimeError('Can only pause a running simulation.')

        self.log.info('Pausing simulation')

        self._running = False

    def resume(self):
        """
        Resume a paused simulation. Can only be called after start
        and pause have been called.
        """
        if not self._started or self._running:
            raise RuntimeError('Can only resume a paused simulation.')

        self.log.info('Resuming simulation')

        self._running = True

    def stop(self):
        """
        Stops the simulation entirely.
        """

        self.log.warn('Stopping simulation')

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
        control server was previously present. If the server is not running, it will be started
        after it has been set.
        """
        return self._control_server

    @control_server.setter
    def control_server(self, control_server):
        if self.is_started and self._control_server:
            raise RuntimeError('Can not replace control server while simulation is running.')

        self._control_server = self._create_control_server(control_server)

        if self.is_started and self._control_server is not None:
            self._control_server.start_server()
