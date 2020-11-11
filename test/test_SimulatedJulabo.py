# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2020 European Spallation Source ERIC
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

import unittest

from lewis.devices.julabo.devices.device import SimulatedJulabo

from .utils import assertRaisesNothing


class TestSimulatedJulabo(unittest.TestCase):
    def setUp(self):
        self.julabo_device = SimulatedJulabo()
        self.julabo_device.process()  # Initialise

    def go_forward_one_minute(self):
        """Moves the device forward in time by 60 seconds."""
        self.julabo_device.process(60)

    def check_setting_values_works(self, par_name, value):
        """Helper function for checking that setting a simple value works.

        :param param_name: The name of the parameter to change.
        :param value: The new value.
        """
        setter = getattr(self.julabo_device, "set_%s" % par_name)
        setter(value)
        self.go_forward_one_minute()
        self.assertEqual(value, getattr(self.julabo_device, par_name))

    def test_default_construction(self):
        assertRaisesNothing(self, SimulatedJulabo)

    def test_changing_setpoint_changes_setpoint(self):
        old_sp = self.julabo_device.set_point_temperature

        self.julabo_device.set_set_point(old_sp + 10.0)

        self.assertEqual(old_sp + 10.0, self.julabo_device.set_point_temperature)

    def test_on_initialisation_circulating_is_off(self):
        self.assertEqual(0, self.julabo_device.is_circulating)

    def test_on_stating_circulating_it_starts_circulating(self):
        self.julabo_device.set_circulating(1)
        self.assertEqual(1, self.julabo_device.is_circulating)

    def test_changing_setpoint_does_not_change_temperature_if_not_circulating(self):
        old_sp = self.julabo_device.set_point_temperature
        old_t = self.julabo_device.temperature

        self.julabo_device.set_set_point(old_sp + 10.0)
        self.go_forward_one_minute()

        self.assertEqual(old_t, self.julabo_device.temperature)

    def test_changing_setpoint_does_change_temperature_if_circulating(self):
        self.julabo_device = SimulatedJulabo()
        self.julabo_device.process()  # Initialise
        old_sp = self.julabo_device.set_point_temperature
        old_t = self.julabo_device.temperature

        self.julabo_device.set_set_point(old_sp + 10.0)
        self.julabo_device.set_circulating(1)
        self.go_forward_one_minute()

        self.assertNotEqual(old_t, self.julabo_device.temperature)

    def test_setting_external_p_sets_p(self):
        self.check_setting_values_works("external_p", 10)

    def test_setting_external_i_sets_i(self):
        self.check_setting_values_works("external_i", 10)

    def test_setting_external_d_sets_d(self):
        self.check_setting_values_works("external_d", 10)

    def test_setting_internal_p_sets_p(self):
        self.check_setting_values_works("internal_p", 10)

    def test_setting_internal_i_sets_i(self):
        self.check_setting_values_works("internal_i", 10)

    def test_setting_internal_d_sets_d(self):
        self.check_setting_values_works("internal_d", 10)
