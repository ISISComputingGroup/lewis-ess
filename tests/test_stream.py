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
from parameterized import parameterized

"""
Test Func only
Add something to argument mappings as a dict
may need additional mocking for Func class to operate
test additional areas of Func after adding a few tests for invalid regex triggering an error
"""


class TestFunc(unittest.TestCase):

    @parameterized.expand([
        ("valid_regex", lambda: 0, "[0-9]{1,2}", None),
        ("valid_regex_and_argument_mapping", lambda x: 5, "([0-8]{1})", [int])
    ])
    def test_argument_variations_of_valid_Func_usage_without_return_mapping(self, _, target_member, write_pattern, argument_mapping):
        self.assertTrue(Func(target_member, write_pattern, argument_mapping))

    @parameterized.expand([
        ("invalid_function", "invalid_func", "[0-9]{1,2}", int, None),
        ("invalid_regex", lambda x: 5, "[0-9]*{1}", int, None),
        ("invalid_argument", lambda: 0, "[0-9]{1}", [1], None),
        ("invalid_argument_and_return_mappings", lambda: 0, "[0-9]{1}", [1], 1)
    ])
    def test_argument_variations_of_Func_usage(self, _, target_member, write_pattern, argument_mapping, return_mapping):
        with self.assertRaises(RuntimeError):
            Func(target_member, write_pattern, argument_mapping, return_mapping)

    def test_argument_invalid_return_mapping_type_returns_TypeError(self):
        with self.assertRaises(TypeError):
            Func(lambda: 0,  "[0-9]{1}", int, 1)

    def test_func_passes_for_correct_return_argument_mappings(self):
        self.assertTrue(Func(lambda x: 5, "([0-8]{1})", [int], int).process_request(b"7"))

    def test_func_fails_for_incorrect_return_argument_mappings(self):
        with self.assertRaises(ValueError):
            Func(lambda x: "string", "([0-8]{1})", [int], int).process_request(b"7")

    def test_process_request(self):
        Func(lambda x: 7, "([0-8]{1})", [int], int).can_process(b"7")
