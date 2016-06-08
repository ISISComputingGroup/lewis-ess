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


class DefaultStandbyState(State):
    def on_entry(self, dt):
        self._context.initialize()


class DefaultPoweredState(State):
    pass


class DefaultAcquireVoltageState(State):
    def on_entry(self, dt):
        self._context.acquire_voltage_commanded = False

    def in_state(self, dt):
        sign = (self._context.target_voltage - self._context.voltage)

        if sign == 0.0:
            return

        sign = sign / abs(sign)
        self._context.voltage += sign * 3.0 * dt

        if sign * self._context.voltage > sign * self._context.target_voltage:
            self._context.voltage = self._context.target_voltage


class DefaultAcquireCurrentState(State):
    def on_entry(self, dt):
        self._context.acquire_current_commanded = False

    def in_state(self, dt):
        sign = (self._context.target_current - self._context.current)

        if sign == 0.0:
            return

        sign = sign / abs(sign)
        self._context.current += sign * 3.0 * dt

        if sign * self._context.current > sign * self._context.target_current:
            self._context.current = self._context.target_current
