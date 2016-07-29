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

from core import State


class DefaultInitState(State):
    def on_entry(self, dt):
        self._context.initialize()


class DefaultStoppedState(State):
    def on_entry(self, dt):
        self._context.stop_commanded = False


class DefaultStartedState(State):
    def on_entry(self, dt):
        self._context.start_commanded = False


class DefaultHeatState(State):
    def in_state(self, dt):
        self._context.temperature += self._context.temperature_rate * (dt / 60.0)
        if self._context.temperature > self._context.temperature_limit:
            self._context.temperature = self._context.temperature_limit


class DefaultHoldState(State):
    def on_entry(self, dt):
        self._context.pump_speed = 0


class DefaultCoolState(State):
    def in_state(self, dt):
        if self._context.pump_manual_mode:
            self._context.pump_speed = self._context.manual_target_speed
        else:
            # TODO: Figure out real correlation
            self._context.pump_speed = int(30 * (self._context.temperature_rate / 50.0))

        if self._context.pump_speed > 30:
            self._context.pump_speed = 30
            self._context.pump_overspeed = True
        else:
            self._context.pump_overspeed = False

        # TODO: Should be based on pump speed somehow
        self._context.temperature -= self._context.temperature_rate * (dt / 60.0)
        if self._context.temperature < self._context.temperature_limit:
            self._context.temperature = self._context.temperature_limit

    def on_exit(self, dt):
        self._context.pump_overspeed = False
