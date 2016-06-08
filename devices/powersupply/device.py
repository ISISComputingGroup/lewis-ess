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

from core import StateMachine, CanProcessComposite, Context
from core.utils import dict_strict_update

from defaults import *


class PSUContext(Context):
    def initialize(self):
        self.voltage = 0.0
        self.current = 0.0

        self.target_voltage = 0.0
        self.target_current = 0.0

        self.switch = False  # power switch

        self.resistance = 100000.0
        self.power = 0.0

        self.acquire_voltage_commanded = False
        self.acquire_current_commanded = False


class SimulatedPowerSupply(CanProcessComposite, object):
    def print_status(self):
        pass

    def __init__(self, override_states=None, override_transitions=None):
        super(SimulatedPowerSupply, self).__init__()

        self._context = PSUContext()

        state_handlers = {
            'standby': DefaultStandbyState(),
            'powered': DefaultPoweredState(),
            'acquire_voltage': DefaultAcquireVoltageState(),
            'acquire_current': DefaultAcquireCurrentState(),
        }

        if override_states is not None:
            dict_strict_update(state_handlers, override_states)

        transition_handlers = OrderedDict([
            (('standby', 'powered'), lambda: self._context.switch),

            (('powered', 'standby'), lambda: not self._context.switch),
            (('powered', 'acquire_voltage'), lambda: self._context.acquire_voltage_commanded),
            (('powered', 'acquire_current'), lambda: self._context.acquire_current_commanded),

            (('acquire_voltage', 'standby'), lambda: not self._context.switch),
            (('acquire_voltage', 'powered'), lambda: self._context.voltage == self._context.target_voltage),
            (('acquire_voltage', 'acquire_current'), lambda: self._context.acquire_current_commanded),

            (('acquire_current', 'standby'), lambda: not self._context.switch),
            (('acquire_current', 'powered'), lambda: self._context.current == self._context.target_current),
            (('acquire_current', 'acquire_voltage'), lambda: self._context.acquire_voltage_commanded),
        ])

        if override_transitions is not None:
            dict_strict_update(transition_handlers, override_transitions)

        self._csm = StateMachine({
            'initial': 'standby',
            'states': state_handlers,
            'transitions': transition_handlers,
        }, context=self._context)

        self.addProcessor(self._csm)

    @property
    def state(self):
        return self._csm.state

    @property
    def voltage(self):
        return self._context.voltage

    @property
    def current(self):
        return self._context.current

    @property
    def targetVoltage(self):
        return self._context.target_voltage

    @targetVoltage.setter
    def targetVoltage(self, value):
        self._context.target_voltage = value

    @property
    def targetCurrent(self):
        return self._context.target_current

    @targetCurrent.setter
    def targetCurrent(self, value):
        self._context.target_current = value

    @property
    def powerSwitch(self):
        return self._context.switch

    @powerSwitch.setter
    def powerSwitch(self, value):
        self._context.switch = value

    @property
    def resistance(self):
        return self._context.resistance

    @resistance.setter
    def resistance(self, value):
        self._context.resistance = value

    @property
    def power(self):
        return self._context.power

    @property
    def voltageCommanded(self):
        return self._context.acquire_voltage_commanded

    @voltageCommanded.setter
    def voltageCommanded(self, value):
        self._context.acquire_voltage_commanded = value

    @property
    def currentCommanded(self):
        return self._context.acquire_current_commanded

    @currentCommanded.setter
    def currentCommanded(self, value):
        self._context.acquire_current_commanded = value
