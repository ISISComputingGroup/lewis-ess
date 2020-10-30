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

from lewis.core.approaches import linear


class TestApproachLinear(unittest.TestCase):
    def test_target_equals_current_does_not_change(self):
        pos = 34.0
        self.assertEqual(linear(pos, pos, 15.0, 0.5), pos)

    def test_speed_zero_does_not_change_value(self):
        pos = 34.0
        target = 23.0
        self.assertEqual(linear(pos, target, 0.0, 0.5), pos)

    def test_dt_zero_does_not_change_value(self):
        pos = 34.0
        target = 23.0
        self.assertEqual(linear(pos, target, 1.0, 0.0), pos)

    def test_target_less_than_pos_works(self):
        pos = 34.0
        target = 23.0
        self.assertEqual(linear(pos, target, 2.0, 0.5), 33.0)

    def test_target_greater_than_pos_works(self):
        pos = 34.0
        target = 43.0
        self.assertEqual(linear(pos, target, 2.0, 0.5), 35.0)

    def test_target_negative_speed_inverts_behavior(self):
        pos = 34.0
        self.assertEqual(linear(pos, 23, -2.0, 0.5), 35.0)
        self.assertEqual(linear(pos, 43, -2.0, 0.5), 33.0)

    def test_no_overshoot(self):
        pos = 34.0
        target = 33.0
        self.assertEqual(linear(pos, target, 10.0, 100.0), target)
