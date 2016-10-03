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

from collections import OrderedDict

from core import StateMachine, CanProcessComposite, CanProcess, Context
from core.utils import dict_strict_update

from .bearings import MagneticBearings
from .defaults import *


class SimulatedBearings(CanProcess, MagneticBearings):
    def __init__(self):
        super(SimulatedBearings, self).__init__()

        self._csm = StateMachine({
            'initial': 'resting',

            'transitions': {
                ('resting', 'levitating'): lambda: self._levitate,
                ('levitating', 'levitated'): self.levitationComplete,
                ('levitated', 'delevitating'): lambda: not self._levitate,
                ('delevitating', 'resting'): self.delevitationComplete,
            }
        })

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
        return self._csm.state == 'levitated' and self._levitate

    @property
    def idle(self):
        return self._csm.state == 'resting' and not self._levitate


class SimulatedChopper(CanProcessComposite, object):
    speed = 0.0
    target_speed = 0.0

    phase = 0.0
    target_phase = 0.0

    parking_position = 0.0
    target_parking_position = 0.0
    auto_park = False

    def __init__(self, override_states=None, override_transitions=None):
        super(SimulatedChopper, self).__init__()

        # Initialise internal state
        self._park_commanded = False
        self._stop_commanded = False
        self._start_commanded = False
        self._idle_commanded = False
        self._phase_commanded = False
        self._shutdown_commanded = False
        self._initialized = False

        self._bearings = SimulatedBearings()

        state_handlers = self._get_state_handlers(override_states)
        transition_handlers = self._get_transition_handlers(override_transitions)

        self._csm = StateMachine({
            'initial': 'init',
            'states': state_handlers,
            'transitions': transition_handlers,
        }, context=self)

        self.addProcessor(self._csm)

    def _get_transition_handlers(self, override_transitions):
        transition_handlers = OrderedDict([
            (('init', 'bearings'), lambda: self.initialized),
            (('bearings', 'stopped'), lambda: self._bearings.ready),
            (('bearings', 'init'), lambda: self._bearings.idle),

            (('parking', 'parked'), lambda: self.parking_position == self.target_parking_position),
            (('parking', 'stopping'), lambda: self._stop_commanded),

            (('parked', 'stopping'), lambda: self._stop_commanded),
            (('parked', 'accelerating'), lambda: self._start_commanded),

            (('stopped', 'accelerating'), lambda: self._start_commanded),
            (('stopped', 'parking'), lambda: self._park_commanded),
            (('stopped', 'bearings'), lambda: self._shutdown_commanded),

            (('accelerating', 'stopping'), lambda: self._stop_commanded),
            (('accelerating', 'idle'), lambda: self._idle_commanded),
            (('accelerating', 'phase_locking'), lambda: self.speed == self.target_speed),

            (('idle', 'accelerating'), lambda: self._start_commanded),
            (('idle', 'stopping'), lambda: self._stop_commanded),

            (('phase_locking', 'stopping'), lambda: self._stop_commanded),
            (('phase_locking', 'phase_locked'), lambda: self.phase == self.target_phase),
            (('phase_locking', 'idle'), lambda: self._idle_commanded),

            (('phase_locked', 'accelerating'), lambda: self._start_commanded),
            (('phase_locked', 'phase_locking'), lambda: self._phase_commanded),
            (('phase_locked', 'stopping'), lambda: self._stop_commanded),
            (('phase_locked', 'idle'), lambda: self._idle_commanded),

            (('stopping', 'accelerating'), lambda: self._start_commanded),
            (('stopping', 'stopped'), lambda: self.speed == 0.0),
            (('stopping', 'idle'), lambda: self._idle_commanded),
        ])

        if override_transitions is not None:
            dict_strict_update(transition_handlers, override_transitions)

        return transition_handlers

    def _get_state_handlers(self, override_states):
        state_handlers = {
            'init': DefaultInitState(),
            'bearings': {'in_state': self._bearings},
            'stopped': DefaultStoppedState(),
            'stopping': DefaultStoppingState(),
            'accelerating': DefaultAcceleratingState(),
            'phase_locking': DefaultPhaseLockingState(),
            'phase_locked': DefaultPhaseLockedState(),
            'idle': DefaultIdleState(),
            'parking': DefaultParkingState(),
            'parked': DefaultParkedState(),
        }

        if override_states is not None:
            dict_strict_update(state_handlers, override_states)

        return state_handlers

    @property
    def state(self):
        return self._csm.state

    @property
    def initialized(self):
        return self._initialized

    def initialize(self):
        if self._csm.can('bearings') and not self.initialized:
            self._initialized = True
            self._bearings.engage()

    def deinitialize(self):
        if self._csm.can('bearings') and self.initialized:
            self._shutdown_commanded = True
            self._bearings.disengage()

    def park(self):
        if self._csm.can('parking'):
            self._park_commanded = True

    @property
    def parked(self):
        return self._csm.state == 'parked'

    def stop(self):
        if self._csm.can('stopping'):
            self._stop_commanded = True

    @property
    def stopped(self):
        return self._csm.state == 'stopped'

    def start(self):
        if self._csm.can('accelerating') and self.target_speed > 0.0:
            self._start_commanded = True
        else:
            self.stop()

    @property
    def started(self):
        return self._csm.state == 'accelerating'

    def unlock(self):
        if self._csm.can('idle'):
            self._idle_commanded = True

    @property
    def idle(self):
        return self._csm.state == 'idle'

    def lock_phase(self):
        if self._csm.can('phase_locking'):
            self._phase_commanded = True

    @property
    def phase_locked(self):
        return self._csm.state == 'phase_locked'
