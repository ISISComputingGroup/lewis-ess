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

from plankton.adapters.stream import StreamAdapter, Cmd


class JulaboStreamInterface(StreamAdapter):
    commands = {
        Cmd('get_bath_temperature', '^IN_PV_00$'),
        Cmd('get_external_temperature', '^IN_PV_01$'),
        Cmd('get_power', '^IN_PV_02$'),
        Cmd('get_set_point', '^IN_SP_00$'),
        Cmd('get_high_limit', '^IN_SP_01$'),
        Cmd('get_low_limit', '^IN_SP_02$'),
        Cmd('get_circulating', '^IN_MODE_05$'),
        Cmd('get_version', '^VERSION$'),
        Cmd('get_status', '^STATUS$'),
        Cmd('set_set_point', '^OUT_SP_00 ([0-9]*\.?[0-9]+)$'),
        Cmd('set_mode', '^OUT_MODE_05 [0|1]{1}$'),
        Cmd('get_internal_p', '^IN_PAR_06$'),
        Cmd('get_internal_i', '^IN_PAR_07$'),
        Cmd('get_internal_d', '^IN_PAR_08$'),
        Cmd('set_internal_p', '^OUT_PAR_06 ([0-9]*\.?[0-9]+)$'),
        Cmd('set_internal_i', '^OUT_PAR_07 ([0-9]*)$'),
        Cmd('set_internal_d', '^OUT_PAR_08 ([0-9]*)$'),
        Cmd('get_external_p', '^IN_PAR_09$'),
        Cmd('get_external_i', '^IN_PAR_11$'),
        Cmd('get_external_d', '^IN_PAR_12$'),
        Cmd('set_external_p', '^OUT_PAR_09 ([0-9]*\.?[0-9]+)$'),
        Cmd('set_external_i', '^OUT_PAR_11 ([0-9]*)$'),
        Cmd('set_external_d', '^OUT_PAR_12 ([0-9]*)$'),
    }

    in_terminator = '\r'
    out_terminator = '\r\n'

    def get_bath_temperature(self):
        """
        Gets the external temperature of the bath.

        :return: The external temperature.
        """
        return self._device.temperature

    def get_external_temperature(self):
        """
        Gets the temperature of the bath.

        :return: The current bath temperature.
        """
        return self._device.external_temperature

    def get_power(self):
        """
        Gets the heating power currently being used.

        :return: The heating power.
        """
        return self._device.external_temperature

    def get_set_point(self):
        """
        Gets the set point the user requested.

        :return: The set point temperature.
        """
        return self._device.set_point_temperature

    def get_high_limit(self):
        """
        Gets the high limit set for the bath.

        These are usually set manually in the hardware.

        :return: The high limit.
        """
        return self._device.temperature_high_limit

    def get_low_limit(self):
        """
        Gets the low limit set for the bath.

        These are usually set manually in the hardware.

        :return: The low limit.
        """
        return self._device.temperature_low_limit

    def get_circulating(self):
        """
        Gets whether the bath is circulating.

        This means the heater is on?

        :return: O for off, 1 for on.
        """
        return self._device.is_circulating

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
        sp = int(param)
        if self._device.temperature_low_limit <= sp <= self._device.temperature_high_limit:
            self._device.set_point_temperature = sp
        return ""

    def set_mode(self, param):
        """
        Sets whether to circulate - in effect whether the heater is on.

        :param param: The mode to set, must be 0 or 1.
        :return: Empty string.
        """
        sp = int(param)
        if sp == 0:
            self._device.is_circulating = sp
            self._devicecirculate_commanded = False
        elif sp == 1:
            self._device.is_circulating = sp
            self._devicecirculate_commanded = True
        return ""

    def get_internal_p(self):
        """
        Gets the internal proportional.
        Xp in Julabo speak

        :return: The p.
        """
        return self._device.internal_p

    def get_internal_i(self):
        """
        Gets the internal integral.
        Tn in Julabo speak

        :return: The i.
        """
        return self._device.internal_i

    def get_internal_d(self):
        """
        Gets the internal derivative.
        Tv in Julabo speak

        :return: The p.
        """
        return self._device.internal_d

    def get_external_p(self):
        """
        Gets the external proportional.
        Xp in Julabo speak

        :return: The d.
        """
        return self._device.external_p

    def get_external_i(self):
        """
        Gets the external integral.
        Tn in Julabo speak

        :return: The i.
        """
        return self._device.external_i

    def get_external_d(self):
        """
        Gets the external derivative.
        Tv in Julabo speak

        :return: The d.
        """
        return self._device.external_d

    def set_internal_p(self, param):
        """
        Sets the internal proportional.
        Xp in Julabo speak.

        :param param: The value to set, must be between 0.1 and 99.9
        :return: Empty string.
        """
        sp = float(param)
        if 0.1 <= sp <= 99.9:
            self._device.internal_p = sp
        return ""

    def set_internal_i(self, param):
        """
        Sets the internal integral.
        Tn in Julabo speak.

        :param param: The value to set, must be an integer between 3 and 9999
        :return: Empty string.
        """
        sp = int(param)
        if 3 <= sp <= 9999:
            self._device.internal_i = sp
        return ""

    def set_internal_d(self, param):
        """
        Sets the internal derivative.
        Tv in Julabo speak.

        :param param: The value to set, must be an integer between 0 and 999
        :return: Empty string.
        """
        sp = int(param)
        if 0 <= sp <= 999:
            self._device.internal_d = sp
        return ""

    def set_external_p(self, param):
        """
        Sets the external proportional.
        Xp in Julabo speak.

        :param param: The value to set, must be between 0.1 and 99.9
        :return: Empty string.
        """
        sp = float(param)
        if 0.1 <= sp <= 99.9:
            self._device.external_p = sp
        return ""

    def set_external_i(self, param):
        """
        Sets the external integral.
        Tn in Julabo speak.

        :param param: The value to set, must be an integer between 3 and 9999
        :return: Empty string.
        """
        sp = int(param)
        if 3 <= sp <= 9999:
            self._device.external_i = sp
        return ""

    def set_external_d(self, param):
        """
        Sets the external derivative.
        Tv in Julabo speak.

        :param param: The value to set, must be an integer between 0 and 999
        :return: Empty string.
        """
        sp = int(param)
        if 0 <= sp <= 999:
            self._device.external_d = sp
        return ""
