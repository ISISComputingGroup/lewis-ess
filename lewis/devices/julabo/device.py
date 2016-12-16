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
        self.heating_power = 5.0  # The heating power
        self.set_point_temperature = 24.0  # Set point starts equal to the current temperature
        self.temperature_low_limit = 0.0  # Usually set in the hardware
        self.temperature_high_limit = 100.0  # Usually set in the hardware
        self.is_circulating = 0  # 0 for off, 1 for on
        self.temperature_ramp_rate = 5.0  # Guessed value in C/min

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

    def get_bath_temperature(self):
        """
        Gets the external temperature of the bath.

        :return: The external temperature.
        """
        return self.temperature

    def get_external_temperature(self):
        """
        Gets the temperature of the bath.

        :return: The current bath temperature.
        """
        return self.external_temperature

    def get_power(self):
        """
        Gets the heating power currently being used.

        :return: The heating power.
        """
        return self.heating_power

    def get_set_point(self):
        """
        Gets the set point the user requested.

        :return: The set point temperature.
        """
        return self.set_point_temperature

    def get_high_limit(self):
        """
        Gets the high limit set for the bath.

        These are usually set manually in the hardware.

        :return: The high limit.
        """
        return self.temperature_high_limit

    def get_low_limit(self):
        """
        Gets the low limit set for the bath.

        These are usually set manually in the hardware.

        :return: The low limit.
        """
        return self.temperature_low_limit

    def get_circulating(self):
        """
        Gets whether the bath is circulating.

        This means the heater is on?

        :return: O for off, 1 for on.
        """
        return self.is_circulating

    def get_version(self):
        """
        Gets the Julabo version number.

        :return: Version string.
        """
        return "JULABO FP50_MH Simulator, ISIS"

    def get_status(self):
        """
        Not sure what a real device returns as the manual is a bit vague.
        It will return error codes but it is not clear what it returns if everything is okay.

        :return: String
        """
        return "Hello from the simulated Julabo"

    def set_set_point(self, param):
        """
        Sets the target temperature.

        :param param: The new temperature in C. Must be positive.
        :return: Empty string.
        """
        if self.temperature_low_limit <= param <= self.temperature_high_limit:
            self.set_point_temperature = param
        return ""

    def set_circulating(self, param):
        """
        Sets whether to circulate - in effect whether the heater is on.

        :param param: The mode to set, must be 0 or 1.
        :return: Empty string.
        """
        if param == 0:
            self.is_circulating = param
            self.circulate_commanded = False
        elif param == 1:
            self.is_circulating = param
            self.circulate_commanded = True
        return ""

    def get_internal_p(self):
        """
        Gets the internal proportional.
        Xp in Julabo speak

        :return: The p.
        """
        return self.internal_p

    def get_internal_i(self):
        """
        Gets the internal integral.
        Tn in Julabo speak

        :return: The i.
        """
        return self.internal_i

    def get_internal_d(self):
        """
        Gets the internal derivative.
        Tv in Julabo speak

        :return: The p.
        """
        return self.internal_d

    def get_external_p(self):
        """
        Gets the external proportional.
        Xp in Julabo speak

        :return: The d.
        """
        return self.external_p

    def get_external_i(self):
        """
        Gets the external integral.
        Tn in Julabo speak

        :return: The i.
        """
        return self.external_i

    def get_external_d(self):
        """
        Gets the external derivative.
        Tv in Julabo speak

        :return: The d.
        """
        return self.external_d

    def set_internal_p(self, param):
        """
        Sets the internal proportional.
        Xp in Julabo speak.

        :param param: The value to set, must be between 0.1 and 99.9
        :return: Empty string.
        """
        if 0.1 <= param <= 99.9:
            self.internal_p = param
        return ""

    def set_internal_i(self, param):
        """
        Sets the internal integral.
        Tn in Julabo speak.

        :param param: The value to set, must be an integer between 3 and 9999
        :return: Empty string.
        """
        if 3 <= param <= 9999:
            self.internal_i = param
        return ""

    def set_internal_d(self, param):
        """
        Sets the internal derivative.
        Tv in Julabo speak.

        :param param: The value to set, must be an integer between 0 and 999
        :return: Empty string.
        """
        if 0 <= param <= 999:
            self.internal_d = param
        return ""

    def set_external_p(self, param):
        """
        Sets the external proportional.
        Xp in Julabo speak.

        :param param: The value to set, must be between 0.1 and 99.9
        :return: Empty string.
        """
        if 0.1 <= param <= 99.9:
            self.external_p = param
        return ""

    def set_external_i(self, param):
        """
        Sets the external integral.
        Tn in Julabo speak.

        :param param: The value to set, must be an integer between 3 and 9999
        :return: Empty string.
        """
        if 3 <= param <= 9999:
            self.external_i = param
        return ""

    def set_external_d(self, param):
        """
        Sets the external derivative.
        Tv in Julabo speak.

        :param param: The value to set, must be an integer between 0 and 999
        :return: Empty string.
        """
        if 0 <= param <= 999:
            self.external_d = param
        return ""
