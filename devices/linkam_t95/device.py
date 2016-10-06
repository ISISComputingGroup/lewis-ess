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

from __future__ import print_function
from collections import OrderedDict

from core import StateMachine, CanProcessComposite, Context
from core.utils import dict_strict_update

from .states import *


class LinkamT95Context(Context):
    """
    The Context models device memory state.

    All the variables that the device tracks should be defined here, and
    initialized to default values.

    The device context is available as _context in the device class, and
    all associated device State and Transition classes.
    """

    def initialize(self):
        """
        This method is called once on construction. After that, it may be
        manually called again to reset the device to its default state.

        After the first call during construction, the class is frozen.

        This means that attempting to define a new member variable will
        raise an exception. This is to prevent typos from inadvertently
        and silently adding new members instead of accessing existing ones.
        """
        self.serial_command_mode = False
        self.pump_overspeed = False

        self.start_commanded = False
        self.stop_commanded = False
        self.hold_commanded = False

        # Real device remembers values from last run, we use arbitrary defaults
        self.temperature_rate = 5.0  # Rate of change of temperature in C/min
        self.temperature_limit = 0.0  # Target temperature in C

        self.pump_speed = 0  # Pump speed in arbitrary unit, ranging 0 to 30
        self.temperature = 24.0  # Current temperature in C

        self.pump_manual_mode = False
        self.manual_target_speed = 0


class SimulatedLinkamT95(CanProcessComposite, object):
    def __init__(self, override_states=None, override_transitions=None):
        super(SimulatedLinkamT95, self).__init__()

        # Create instance of device context. This is shared with all the states of this device.
        self._context = LinkamT95Context()

        # Define all existing states of the device; the handlers live in states.py
        state_handlers = {
            'init': DefaultInitState(),
            'stopped': DefaultStoppedState(),
            'started': DefaultStartedState(),
            'heat': DefaultHeatState(),
            'hold': DefaultHoldState(),
            'cool': DefaultCoolState(),
        }

        # Allows setup to override state behaviour by passing it to this constructor
        if override_states is not None:
            dict_strict_update(state_handlers, override_states)

        # Define all transitions and the conditions under which they are executed.
        transition_handlers = OrderedDict([
            (('init', 'stopped'), lambda: self._context.serial_command_mode),

            (('stopped', 'started'), lambda: self._context.start_commanded),

            (('started', 'stopped'), lambda: self._context.stop_commanded),
            (('started', 'heat'), lambda: self._context.temperature < self._context.temperature_limit),
            (('started', 'hold'), lambda: self._context.temperature == self._context.temperature_limit),
            (('started', 'cool'), lambda: self._context.temperature > self._context.temperature_limit),

            (('heat', 'hold'),
             lambda: self._context.temperature == self._context.temperature_limit or self._context.hold_commanded),
            (('heat', 'cool'), lambda: self._context.temperature > self._context.temperature_limit),
            (('heat', 'stopped'), lambda: self._context.stop_commanded),

            (('hold', 'heat'),
             lambda: self._context.temperature < self._context.temperature_limit and not self._context.hold_commanded),
            (('hold', 'cool'),
             lambda: self._context.temperature > self._context.temperature_limit and not self._context.hold_commanded),
            (('hold', 'stopped'), lambda: self._context.stop_commanded),

            (('cool', 'heat'), lambda: self._context.temperature < self._context.temperature_limit),
            (('cool', 'hold'),
             lambda: self._context.temperature == self._context.temperature_limit or self._context.hold_commanded),
            (('cool', 'stopped'), lambda: self._context.stop_commanded),
        ])

        # Allows setup to override transition behaviour by passing it to this constructor
        if override_transitions is not None:
            dict_strict_update(transition_handlers, override_transitions)

        self._csm = StateMachine({
            'initial': 'init',
            'states': state_handlers,
            'transitions': transition_handlers,
        }, context=self._context)

        # Ensures the state machine object gets a 'process' heartbeat tick
        self.addProcessor(self._csm)

    def getStatus(self):
        """
        Models "T Command" functionality of device.

        Returns all available status information about the device as single byte array.

        :return: Byte array consisting of 10 status bytes.
        """

        # "The first command sent must be a 'T' command" from T95 manual
        self._context.serial_command_mode = True

        Tarray = [0x80] * 10

        # Status byte (SB1)
        Tarray[0] = {
            'stopped': 0x01,
            'heat': 0x10,
            'cool': 0x20,
            'hold': 0x30,
        }.get(self._csm.state, 0x01)
        if Tarray[0] == 0x30 and self._context.hold_commanded:
            Tarray[0] = 0x50

        # Error status byte (EB1)
        if self._context.pump_overspeed:
            Tarray[1] |= 0x01
        # TODO: Add support for other error conditions?

        # Pump status byte (PB1)
        Tarray[2] = 0x80 + self._context.pump_speed

        # Temperature
        Tarray[6:10] = [ord(x) for x in "%04x" % (int(self._context.temperature * 10) & 0xFFFF)]

        print(self._csm.state)
        print(str(Tarray))

        return ''.join(chr(c) for c in Tarray)

    def setRate(self, param):
        """
        Models "Rate Command" functionality of device.

        Sets the target rate of temperature change.

        :param param: Rate of temperature change in C/min, multiplied by 100, as a string. Must be positive.
        :return: Empty string.
        """
        # TODO: Is not having leading zeroes / 4 digits an error?
        rate = int(param)
        if 1 <= rate <= 15000:
            self._context.temperature_rate = rate / 100.0
        print("New rate: %.2f C/min" % (self._context.temperature_rate,))
        return ""

    def setLimit(self, param):
        """
        Models "Limit Command" functionality of device.

        Sets the target temperate to be reached.

        :param param: Target temperature in C, multiplied by 10, as a string. Can be negative.
        :return: Empty string.
        """
        # TODO: Is not having leading zeroes / 4 digits an error?
        limit = int(param)
        if -2000 <= limit <= 6000:
            self._context.temperature_limit = limit / 10.0
        print("New limit: %.1f C" % (self._context.temperature_limit,))
        return ""

    def start(self):
        """
        Models "Start Command" functionality of device.

        Tells the T95 unit to start heating or cooling at the rate specified by setRate and to a limit set by setLimit.

        :return: Empty string.
        """
        self._context.start_commanded = True
        print("Start commanded")
        return ""

    def stop(self):
        """
        Models "Stop Command" functionality of device.

        Tells the T95 unit to stop heating or cooling.

        :return: Empty string.
        """
        self._context.stop_commanded = True
        print("Stop commanded")
        return ""

    def hold(self):
        """
        Models "Hold Command" functionality of device.

        Device will hold current temperature until a heat or cool command is issued.

        :return: Empty string.
        """
        self._context.hold_commanded = True
        return ""

    def heat(self):
        """
        Models "Heat Command" functionality of device.

        :return: Empty string.
        """
        # TODO: Is this really all it does?
        self._context.hold_commanded = False
        return ""

    def cool(self):
        """
        Models "Cool Command" functionality of device.

        :return: Empty string.
        """
        # TODO: Is this really all it does?
        self._context.hold_commanded = False
        return ""

    def pumpCommand(self, param):
        """
        Models "LNP Pump Commands" functionality of device.

        Switches between automatic or manual pump mode, and adjusts speed when in manual mode.

        :param param: 'a0' for auto, 'm0' for manual, [0-N] for speed.
        :return:
        """
        lookup = [c for c in "0123456789:;<=>?@ABCDEFGHIJKLMN"]

        if param == "a0":
            self._context.pump_manual_mode = False
        elif param == "m0":
            self._context.pump_manual_mode = True
        elif param in lookup:
            self._context.manual_target_speed = lookup.index(param)

        return ""
