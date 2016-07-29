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
        self.pump_overspeed = False

        self.start_commanded = False
        self.stop_commanded = False
        self.hold_commanded = False

        # TODO: Actual rate and limit defaults?
        self.temperature_rate = 0.01    # Rate of change of temperature in C/min
        self.temperature_limit = 0.0    # Target temperature in C

        self.pump_speed = 0         # Pump speed in arbitrary unit, ranging 0 to 30
        self.temperature = 24.0     # Current temperature in C

        self.pump_manual_mode = False
        self.manual_target_speed = 0


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

        Tarray = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 13]

        # Status byte (SB1)
        Tarray[0] = {
            'stopped': 0x01,
            'heat': 0x10,
            'cool': 0x20,
            'hold': 0x30,
        }.get(self._csm.state, 0x01)
        if Tarray[0] == 0x30 and self._context.hold_commanded:
            Tarray[0] = 0x40 if self._context.temperature == self._context.temperature_limit else 0x50

        # Error status byte (EB1)
        Tarray[1] = 0x80
        if self._context.pump_overspeed:
            Tarray[1] |= 0x01
        # TODO: Add support for other error conditions?

        # Pump status byte (PB1)
        Tarray[2] = 0x80 + self._context.pump_speed

        # Temperature
        temphex = "%08x" % int(self._context.temperature * 10)
        tempbytes = [int(e, 16) for e in [temphex[n:n+2] for n in xrange(0, len(temphex), 2)]]
        Tarray[6:10] = tempbytes

        print self._csm.state
        print str(Tarray)

        return ''.join(chr(c) for c in Tarray)

    def setRate(self, param):
        # TODO: Is not having leading zeroes / 4 digits an error?
        # TODO: What is the upper limit in the real device?
        rate = int(param)
        if 1 <= rate <= 9999:
            self._context.temperature_rate = rate / 100.0
        print "New rate: %.2f C/min" % (self._context.temperature_rate,)

    def setLimit(self, param):
        # TODO: Is not having leading zeroes / 4 digits an error?
        # TODO: What are the upper and lower limits in the real device?
        limit = int(param)
        if -9999 <= limit <= 9999:
            self._context.temperature_limit = limit / 10.0
        print "New limit: %.1f C" % (self._context.temperature_limit,)

    def start(self):
        self._context.start_commanded = True
        print "Start commanded"

    def stop(self):
        self._context.stop_commanded = True
        print "Stop commanded"

    def hold(self):
        self._context.hold_commanded = True

    def heat(self):
        # TODO: Is this really all it does?
        self._context.hold_commanded = False

    def cool(self):
        # TODO: Is this really all it does?
        self._context.hold_commanded = False

    def pumpCommand(self, param):
        lookup = [c for c in "0123456789:;<=>?@ABCDEFGHIJKLMN"]

        if param == "a0":
            self._context.pump_manual_mode = False
        elif param == "m0":
            self._context.pump_manual_mode = True
        elif param in lookup:
            self._context.manual_target_speed = lookup.index(param)
