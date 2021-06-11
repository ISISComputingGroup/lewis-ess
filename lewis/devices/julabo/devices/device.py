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

from lewis.core.utils import check_limits
from lewis.devices import StateMachineDevice

from . import states


class SimulatedJulabo(StateMachineDevice):
    internal_p = 0.1  # The proportional
    internal_i = 3  # The integral
    internal_d = 0  # The derivative
    external_p = 0.1  # The proportional
    external_i = 3  # The integral
    external_d = 0  # The derivative
    temperature_low_limit = 0.0  # Usually set in the hardware
    temperature_high_limit = 100.0  # Usually set in the hardware
    set_point_temperature = 24.0  # Set point starts equal to the current temperature
    heating_power = 5.0  # The heating power
    version = "JULABO FP50_MH Simulator, ISIS"
    status = "Hello from the simulated Julabo"
    is_circulating = 0  # 0 for off, 1 for on
    temperature = 24.0  # Current temperature in C
    external_temperature = 26.0  # External temperature in C
    circulate_commanded = False
    temperature_ramp_rate = 5.0  # Guessed value in C/min

    def _initialize_data(self):
        """
        This method is called once on construction. After that, it may be
        manually called again to reset the device to its default state.

        After the first call during construction, the class is frozen.

        This means that attempting to define a new member variable will
        raise an exception. This is to prevent typos from inadvertently
        and silently adding new members instead of accessing existing ones.
        """
        pass

    def _get_state_handlers(self):
        return {
            "circulate": states.DefaultCirculatingState(),
            "not_circulate": states.DefaultNotCirculatingState(),
        }

    def _get_initial_state(self):
        return "not_circulate"

    def _get_transition_handlers(self):
        return OrderedDict(
            [
                (("not_circulate", "circulate"), lambda: self.circulate_commanded),
                (("circulate", "not_circulate"), lambda: not self.circulate_commanded),
            ]
        )

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

    @check_limits(0.1, 99.9)
    def set_internal_p(self, param):
        """
        Sets the internal proportional.
        Xp in Julabo speak.

        :param param: The value to set, must be between 0.1 and 99.9
        :return: Empty string.
        """
        self.internal_p = param
        return ""

    @check_limits(3, 9999)
    def set_internal_i(self, param):
        """
        Sets the internal integral.
        Tn in Julabo speak.

        :param param: The value to set, must be an integer between 3 and 9999
        :return: Empty string.
        """
        self.internal_i = param
        return ""

    @check_limits(0, 999)
    def set_internal_d(self, param):
        """
        Sets the internal derivative.
        Tv in Julabo speak.

        :param param: The value to set, must be an integer between 0 and 999
        :return: Empty string.
        """
        self.internal_d = param
        return ""

    @check_limits(0.1, 99.9)
    def set_external_p(self, param):
        """
        Sets the external proportional.
        Xp in Julabo speak.

        :param param: The value to set, must be between 0.1 and 99.9
        :return: Empty string.
        """
        self.external_p = param
        return ""

    @check_limits(3, 9999)
    def set_external_i(self, param):
        """
        Sets the external integral.
        Tn in Julabo speak.

        :param param: The value to set, must be an integer between 3 and 9999
        :return: Empty string.
        """
        self.external_i = param
        return ""

    @check_limits(0, 999)
    def set_external_d(self, param):
        """
        Sets the external derivative.
        Tv in Julabo speak.

        :param param: The value to set, must be an integer between 0 and 999
        :return: Empty string.
        """
        self.external_d = param
        return ""
