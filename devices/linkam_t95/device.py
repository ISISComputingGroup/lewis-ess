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


class LinkamT95Context(Context):
    def initialize(self):
        self.serial_command_mode = False

        self.start_commanded = False
        self.stop_commanded = False
        self.hold_commanded = False

        self.pump_speed = 0         # Pump speed in arbitrary unit, ranging 0 to 30
        self.temperature = 24.0     # Current temperature in C

        self.pump_manual_mode = False
        self.manual_target_speed = 0

        self.temperature_rate = 0.0     # Rate of change of temperature in C/min
        self.temperature_limit = 0.0    # Target temperature in C


class SimulatedLinkamT95(CanProcessComposite, object):
    def __init__(self, override_states=None, override_transitions=None):
        super(SimulatedLinkamT95, self).__init__()

        self._context = LinkamT95Context()

        state_handlers = {
            'init': DefaultInitState(),
            'stopped': DefaultStoppedState(),
            'started': DefaultStartedState(),
            'heat': DefaultHeatState(),
            'hold': DefaultHoldState(),
            'cool': DefaultCoolState(),
        }

        if override_states is not None:
            dict_strict_update(state_handlers, override_states)

        transition_handlers = OrderedDict([
            (('init', 'stopped'), lambda: self._context.serial_command_mode),

            (('stopped', 'started'), lambda: self._context.start_commanded),

            (('started', 'stopped'), lambda: self._context.stop_commanded),
            (('started', 'heat'), lambda: self._context.temperature < self._context.temperature_limit),
            (('started', 'hold'), lambda: self._context.temperature == self._context.temperature_limit),
            (('started', 'cool'), lambda: self._context.temperature > self._context.temperature_limit),

            (('heat', 'hold'), lambda: self._context.temperature == self._context.temperature_limit),
            (('heat', 'cool'), lambda: self._context.temperature > self._context.temperature_limit),
            (('heat', 'stopped'), lambda: self._context.stop_commanded),

            (('hold', 'heat'), lambda: self._context.temperature < self._context.temperature_limit),
            (('hold', 'cool'), lambda: self._context.temperature > self._context.temperature_limit),
            (('hold', 'stopped'), lambda: self._context.stop_commanded),

            (('cool', 'heat'), lambda: self._context.temperature < self._context.temperature_limit),
            (('cool', 'hold'), lambda: self._context.temperature == self._context.temperature_limit),
            (('cool', 'stopped'), lambda: self._context.stop_commanded),
        ])

        if override_transitions is not None:
            dict_strict_update(transition_handlers, override_transitions)

        self._csm = StateMachine({
            'initial': 'init',
            'states': state_handlers,
            'transitions': transition_handlers,
        }, context=self._context)

        self.addProcessor(self._csm)

    def getStatus(self):
        self._context.serial_command_mode = True

        Tarray = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "\n"]

        # Status byte (SB1)
        Tarray[0] = {
            'stopped': 0x01,
            'heat': 0x10,
            'cool': 0x20,
            'hold': 0x30,  # TODO: Other hold states
        }.get(self._csm.state, 0x01)

        # Error status byte (EB1)
        Tarray[1] = 0x00

        # Pump status byte (PB1)
        Tarray[2] = 0x80

        # Temperature
        temphex = "%08x" % int(self._context.temperature)
        tempbytes = [int(e, 16) for e in [temphex[n:n+2] for n in xrange(0, len(temphex), 2)]]
        Tarray[6:10] = tempbytes

        print self._csm.state
        return str(Tarray) + "\n"  # TODO: Should be raw bytes

    def setRate(self, param):
        rate = int(param)
        if 1 <= rate <= 9999:
            self._context.temperature_rate = rate / 100.0
        print "New rate: %.2f C/min\n" % (self._context.temperature_rate,)

    def setLimit(self, param):
        limit = int(param)
        if -9999 <= limit <= 9999:
            self._context.temperature_limit = limit / 10.0
        print "New limit: %.1f C\n" % (self._context.temperature_limit,)

    def start(self):
        self._context.start_commanded = True
        print "Start commanded"

    def stop(self):
        self._context.stop_commanded = True
        print "Stop commanded"

    def hold(self):
        pass

    def heat(self):
        pass

    def cool(self):
        pass

    def pumpCommand(self, param):
        pass
