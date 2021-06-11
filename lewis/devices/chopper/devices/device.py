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

from collections import OrderedDict

from lewis.core.processor import CanProcess
from lewis.core.statemachine import StateMachine
from lewis.devices import StateMachineDevice

from . import states
from .bearings import MagneticBearings


class SimulatedBearings(CanProcess, MagneticBearings):
    def __init__(self):
        super(SimulatedBearings, self).__init__()

        self._csm = StateMachine(
            {
                "initial": "resting",
                "transitions": {
                    ("resting", "levitating"): lambda: self._levitate,
                    ("levitating", "levitated"): self.levitationComplete,
                    ("levitated", "delevitating"): lambda: not self._levitate,
                    ("delevitating", "resting"): self.delevitationComplete,
                },
            }
        )

        self._levitate = False

    def engage(self):
        self.levitate()

    def disengage(self):
        self.delevitate()

    def levitate(self):
        self._levitate = True

    def delevitate(self):
        self._levitate = False

    def levitationComplete(self):
        return True

    def delevitationComplete(self):
        return True

    def doProcess(self, dt):
        self._csm.process(dt)

    @property
    def ready(self):
        return self._csm.state == "levitated" and self._levitate

    @property
    def idle(self):
        return self._csm.state == "resting" and not self._levitate


class SimulatedChopper(StateMachineDevice):
    _bearings = None

    def _initialize_data(self):
        self.speed = 0.0
        self.target_speed = 0.0

        self.phase = 0.0
        self.target_phase = 0.0

        self.parking_position = 0.0
        self.target_parking_position = 0.0
        self.auto_park = False

        self._park_commanded = False
        self._stop_commanded = False
        self._start_commanded = False
        self._idle_commanded = False
        self._phase_commanded = False
        self._shutdown_commanded = False
        self._initialized = False

        if self._bearings is None:
            self._bearings = SimulatedBearings()

    def _get_state_handlers(self):
        return {
            "init": states.DefaultInitState(),
            "bearings": {"in_state": self._bearings},
            "stopped": states.DefaultStoppedState(),
            "stopping": states.DefaultStoppingState(),
            "accelerating": states.DefaultAcceleratingState(),
            "phase_locking": states.DefaultPhaseLockingState(),
            "phase_locked": states.DefaultPhaseLockedState(),
            "idle": states.DefaultIdleState(),
            "parking": states.DefaultParkingState(),
            "parked": states.DefaultParkedState(),
        }

    def _get_initial_state(self):
        return "init"

    def _get_transition_handlers(self):
        return OrderedDict(
            [
                (("init", "bearings"), lambda: self.initialized),
                (("bearings", "stopped"), lambda: self._bearings.ready),
                (("bearings", "init"), lambda: self._bearings.idle),
                (
                    ("parking", "parked"),
                    lambda: self.parking_position == self.target_parking_position,
                ),
                (("parking", "stopping"), lambda: self._stop_commanded),
                (("parked", "stopping"), lambda: self._stop_commanded),
                (("parked", "accelerating"), lambda: self._start_commanded),
                (("stopped", "accelerating"), lambda: self._start_commanded),
                (("stopped", "parking"), lambda: self._park_commanded),
                (("stopped", "bearings"), lambda: self._shutdown_commanded),
                (("accelerating", "stopping"), lambda: self._stop_commanded),
                (("accelerating", "idle"), lambda: self._idle_commanded),
                (
                    ("accelerating", "phase_locking"),
                    lambda: self.speed == self.target_speed,
                ),
                (("idle", "accelerating"), lambda: self._start_commanded),
                (("idle", "stopping"), lambda: self._stop_commanded),
                (("phase_locking", "stopping"), lambda: self._stop_commanded),
                (
                    ("phase_locking", "phase_locked"),
                    lambda: self.phase == self.target_phase,
                ),
                (("phase_locking", "idle"), lambda: self._idle_commanded),
                (("phase_locked", "accelerating"), lambda: self._start_commanded),
                (("phase_locked", "phase_locking"), lambda: self._phase_commanded),
                (("phase_locked", "stopping"), lambda: self._stop_commanded),
                (("phase_locked", "idle"), lambda: self._idle_commanded),
                (("stopping", "accelerating"), lambda: self._start_commanded),
                (("stopping", "stopped"), lambda: self.speed == 0.0),
                (("stopping", "idle"), lambda: self._idle_commanded),
            ]
        )

    @property
    def state(self):
        """
        The current state of the chopper. This parameter is read-only, it is
        determined by the internal state machine of the device.
        """
        return self._csm.state

    @property
    def initialized(self):
        return self._initialized

    def initialize(self):
        if self._csm.can("bearings") and not self.initialized:
            self._initialized = True
            self._bearings.engage()

    def deinitialize(self):
        if self._csm.can("bearings") and self.initialized:
            self._shutdown_commanded = True
            self._bearings.disengage()

    def park(self):
        if self._csm.can("parking"):
            self._park_commanded = True

    @property
    def parked(self):
        return self._csm.state == "parked"

    def stop(self):
        if self._csm.can("stopping"):
            self._stop_commanded = True

    @property
    def stopped(self):
        return self._csm.state == "stopped"

    def start(self):
        if self._csm.can("accelerating") and self.target_speed > 0.0:
            self._start_commanded = True
        else:
            self.stop()

    @property
    def started(self):
        return self._csm.state == "accelerating"

    def unlock(self):
        if self._csm.can("idle"):
            self._idle_commanded = True

    @property
    def idle(self):
        return self._csm.state == "idle"

    def lock_phase(self):
        if self._csm.can("phase_locking"):
            self._phase_commanded = True

    @property
    def phase_locked(self):
        return self._csm.state == "phase_locked"
