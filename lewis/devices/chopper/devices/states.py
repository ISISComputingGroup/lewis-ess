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
    def on_entry(self, dt):
        self._context._initialize_data()


class DefaultParkingState(State):
    def __init__(self, parking_speed=5.0):
        super(DefaultParkingState, self).__init__()
        self._parking_speed = parking_speed

    def in_state(self, dt):
        self._context.parking_position = approaches.linear(
            self._context.parking_position,
            self._context.target_parking_position,
            self._parking_speed,
            dt,
        )

    def on_entry(self, dt):
        self._context._park_commanded = False


class DefaultParkedState(State):
    pass


class DefaultStoppingState(State):
    def __init__(self, acceleration=5.0):
        super(DefaultStoppingState, self).__init__()
        self._acceleration = acceleration

    def in_state(self, dt):
        self._context.speed = approaches.linear(
            self._context.speed, 0.0, self._acceleration, dt
        )

    def on_entry(self, dt):
        self._context._stop_commanded = False


class DefaultStoppedState(State):
    def on_entry(self, dt):
        if self._context.auto_park:
            self._context._park_commanded = True


class DefaultIdleState(State):
    def __init__(self, acceleration=0.05):
        super(DefaultIdleState, self).__init__()
        self._acceleration = acceleration

    def in_state(self, dt):
        self._context.speed = approaches.linear(
            self._context.speed, self._context.target_speed, self._acceleration, dt
        )


def on_entry(self, dt):
    self._context._idle_commanded = False


class DefaultAcceleratingState(State):
    def __init__(self, acceleration=5.0):
        super(DefaultAcceleratingState, self).__init__()
        self._acceleration = acceleration

    def in_state(self, dt):
        self._context.speed = approaches.linear(
            self._context.speed, self._context.target_speed, self._acceleration, dt
        )

    def on_entry(self, dt):
        self._context._start_commanded = False


class DefaultPhaseLockingState(State):
    def __init__(self, phase_locking_speed=5.0):
        super(DefaultPhaseLockingState, self).__init__()
        self._phase_locking_speed = phase_locking_speed

    def in_state(self, dt):
        self._context.phase = approaches.linear(
            self._context.phase,
            self._context.target_phase,
            self._phase_locking_speed,
            dt,
        )

    def on_entry(self, dt):
        self._context._phase_commanded = False


class DefaultPhaseLockedState(State):
    pass
