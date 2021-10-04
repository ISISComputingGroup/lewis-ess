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

import unittest
from mock import MagicMock, Mock, patch
from lewis.adapters.stream import Func, scanf

"""
Test Func only
Add something to argument mappings as a dict
may need additional mocking for Func class to operate
test additional areas of Func after adding a few tests for invalid regex triggering an error
"""


class TestFunc(unittest.TestCase):

    def test_func_triggers_runtime_error_when_func_not_callable(self):
        with self.assertRaises(RuntimeError):
            Func("invalid_func", "[0-9]{1}")

    def test_func_triggers_exception_when_passed_invalid_regex(self):
        with self.assertRaises(RuntimeError):
            Func(lambda: 0, "[0-9]*{1}")

    def test_func_initialised_correctly_when_passed_valid_regex(self):
        self.assertTrue(Func(lambda: 0, "[0-9]{1,2}"))

    def test_func_for_incorrect_argument_mappings_to_regex_triggers_runtime_error(self):
        with self.assertRaises(RuntimeError):
            Func(lambda: 0, "[0-9]{1}", [1], 1)

    def test_func_passes_for_correct_argument_mappings(self):
        self.assertTrue(Func(lambda x: 0, "([0-8]{1})", [int]))

    def test_func_passes_for_correct_return_argument_mappings(self):
        self.assertTrue(Func(lambda x: 5, "([0-8]{1})", [int], int).process_request(b"7"))

    def test_func_fails_for_incorrect_return_argument_mappings(self):
        with self.assertRaises(ValueError):
            Func(lambda x: "string", "([0-8]{1})", [int], int).process_request(b"7")

    def test_process_request(self):
        Func(lambda x: 7, "([0-8]{1})", [int], int).can_process(b"7")
