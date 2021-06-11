# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2021 European Spallation Source ERIC
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

from lewis.core import approaches
from lewis.core.statemachine import State


class DefaultInitState(State):
    pass


class DefaultStoppedState(State):
    def on_entry(self, dt):
        # Reset the stop commanded flag once we enter the stopped state
        self._context.stop_commanded = False


class DefaultStartedState(State):
    def on_entry(self, dt):
        # Reset the start commanded flag once we enter the started state
        self._context.start_commanded = False


class DefaultHeatState(State):
    def in_state(self, dt):
        # Approach target temperature at set temperature rate
        self._context.temperature = approaches.linear(
            self._context.temperature,
            self._context.temperature_limit,
            self._context.temperature_rate / 60.0,
            dt,
        )


class DefaultHoldState(State):
    pass


class DefaultCoolState(State):
    def in_state(self, dt):
        # TODO: Does manual control work like this? Or is it perhaps a separate state?
        if self._context.pump_manual_mode:
            self._context.pump_speed = self._context.manual_target_speed
        else:
            # TODO: Figure out real correlation
            self._context.pump_speed = 30 * (self._context.temperature_rate / 50.0)

        # Handle "cooling too fast" error
        if self._context.pump_speed > 30:
            self._context.pump_speed = 30
            self._context.pump_overspeed = True
        else:
            self._context.pump_speed = int(self._context.pump_speed)
            self._context.pump_overspeed = False

        # Approach target temperature at set temperature rate
        # TODO: Should be based on pump speed somehow
        self._context.temperature = approaches.linear(
            self._context.temperature,
            self._context.temperature_limit,
            self._context.temperature_rate / 60.0,
            dt,
        )

    def on_exit(self, dt):
        # If we exit the cooling state, the cooling pump should no longer run
        self._context.pump_overspeed = False
        self._context.pump_speed = 0
