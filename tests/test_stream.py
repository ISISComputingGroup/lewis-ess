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
from lewis.adapters.stream import Func
from parameterized import parameterized


class TestFunc(unittest.TestCase):
    """Unit tests for lewis.adapters.stream.Func"""
    def setUp(self):
        self.target_member = lambda x: 7
        self.write_pattern = "([0-8]{1})"
        self.argument_mapping = [int]
        self.incorrect_argument_mapping = int
        self.return_mapping = int
        self.process_request_value = b"7"


    @parameterized.expand([
        ("valid_regex", lambda: 0, "[0-9]{1,2}", None),
        ("valid_regex_and_argument_mapping", lambda x: 5, "([0-8]{1})", [int])
    ])
    def test_argument_variations_of_valid_Func_without_return_mapping_is_instance_of_Func(self, _, target_member, write_pattern, argument_mapping):
        self.assertIsInstance(Func(target_member, write_pattern, argument_mapping), Func)

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
        invalid_return_mapping = 1
        with self.assertRaises(TypeError):
            Func(self.target_member, self.write_pattern, self.incorrect_argument_mapping, invalid_return_mapping)

    def test_func_returns_correct_value_for_return_argument_mapping(self):
        self.assertEqual(Func(self.target_member, 
                              self.write_pattern, 
                              self.argument_mapping, 
                              self.return_mapping).process_request(self.process_request_value), 7)

    def test_process_request_is_int(self):
        self.assertIsInstance(Func(self.target_member, 
                                   self.write_pattern, 
                                   self.argument_mapping, 
                                   self.return_mapping).process_request(self.process_request_value), int)

    def test_func_fails_for_incorrect_return_argument_mappings(self):
        string_target_member = lambda x: "string"
        with self.assertRaises(ValueError):
            Func(string_target_member, 
                 self.write_pattern, 
                 self.argument_mapping, 
                 self.return_mapping).process_request(self.process_request_value)

    def test_process_request(self):
        self.assertTrue(Func(self.target_member, 
                             self.write_pattern, 
                             self.argument_mapping, 
                             self.return_mapping).can_process(self.process_request_value))

    def test_incorrect_can_process_request_fails(self):
        self.assertFalse(Func(self.target_member, 
                              self.write_pattern, 
                              self.argument_mapping, 
                              self.return_mapping).can_process(b"9"))
