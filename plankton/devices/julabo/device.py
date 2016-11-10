# -*- coding: utf-8 -*-
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

from plankton.devices import StateMachineDevice

from . import states


class SimulatedJulabo(StateMachineDevice):
    def _initialize_data(self):
        """
        This method is called once on construction. After that, it may be
        manually called again to reset the device to its default state.

        After the first call during construction, the class is frozen.

        This means that attempting to define a new member variable will
        raise an exception. This is to prevent typos from inadvertently
        and silently adding new members instead of accessing existing ones.
        """

        self.circulate_commanded = False

        # Real device remembers values from last run, we use arbitrary defaults
        self.temperature = 24.0  # Current temperature in C
        self.external_temperature = 26.0  # External temperature in C
        self.heating_power = 0.0 # The heating power
        self.set_point_temperature = 24.0 # Start with the set point being equal to the current temperature
        self.temperature_low_limit = 0.0  # Usually set in the hardware
        self.temperature_high_limit = 100.0  # Usually set in the hardware
        self.is_circulating = 1  # 0 for off, 1 for on
        self.temperature_ramp_rate = 5.0 # Guessed value in C/min

        self.internal_p = 0.1 # The proportional
        self.internal_i = 3  # The integral
        self.internal_d = 0  # The derivative
        self.external_p = 0.1  # The proportional
        self.external_i = 3  # The integral
        self.external_d = 0  # The derivative


    def _get_state_handlers(self):
        return {
            'circulate': states.DefaultCirculatingState(),
            'not_circulate': states.DefaultNotCirculatingState(),
        }

    def _get_initial_state(self):
        return 'not_circulate'

    def _get_transition_handlers(self):
        return OrderedDict([
            (('not_circulate', 'circulate'), lambda: self.circulate_commanded),
            (('circulate', 'not_circulate'), lambda: not self.circulate_commanded),
        ])
