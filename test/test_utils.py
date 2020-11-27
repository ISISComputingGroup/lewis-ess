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

import importlib
import unittest
from datetime import datetime

from mock import patch

from lewis.core.exceptions import LewisException, LimitViolationException
from lewis.core.utils import (
    FromOptionalDependency,
    check_limits,
    dict_strict_update,
    extract_module_name,
    format_doc_text,
    get_members,
    get_submodules,
    seconds_since,
)

from .utils import TestWithPackageStructure, assertRaisesNothing


class TestDictStrictUpdate(unittest.TestCase):
    def test_update_all(self):
        base_dict = {1: 2, 2: 45, 4: 4}
        update_dict = {1: 3, 2: 43, 4: 3}

        dict_strict_update(base_dict, update_dict)

        self.assertEqual(base_dict, update_dict)

    def test_update_subset(self):
        base_dict = {1: 2, 2: 45, 4: 4}
        update_dict = {1: 3, 2: 43}

        dict_strict_update(base_dict, update_dict)

        self.assertEqual(base_dict, {1: 3, 2: 43, 4: 4})

    def test_update_superset_exception(self):
        base_dict = {1: 2, 2: 45, 4: 4}
        update_dict = {51: 3, 2: 43}

        self.assertRaises(RuntimeError, dict_strict_update, base_dict, update_dict)


class TestExtractModuleName(TestWithPackageStructure):
    def test_directory_basename_is_returned(self):
        self.assertEqual(extract_module_name(self._dirs["valid"]), "some_dir")

    def test_directory_invalid_name(self):
        self.assertEqual(extract_module_name(self._dirs["invalid_underscore"]), None)
        self.assertEqual(extract_module_name(self._dirs["invalid_dot"]), None)

    def test_file_invalid_name(self):
        self.assertEqual(extract_module_name(self._files["invalid_name"]), None)

    def test_file_invalid_extension(self):
        self.assertEqual(extract_module_name(self._files["invalid_ext"]), None)

    def test_file_basename_without_extension(self):
        self.assertEqual(extract_module_name(self._files["valid"]), "some_file")


class TestGetSubmodules(TestWithPackageStructure):
    def test_non_module_raises_runtimeerror(self):
        self.assertRaises(RuntimeError, get_submodules, self._tmp_package_name)

    def test_correct_modules_are_returned(self):
        submodules = get_submodules(importlib.import_module(self._tmp_package_name))

        self.assertEqual(sorted(submodules.keys()), sorted(self._expected_modules))


class TestGetMembers(unittest.TestCase):
    def test_returns_all_members_if_predicate_is_missing(self):
        class Foo:
            bar = 3.0
            baz = "test"

        members = get_members(Foo())

        self.assertEqual(len(members), 2)
        self.assertIn("bar", members)
        self.assertIn("baz", members)

    def test_predicate(self):
        class Foo:
            bar = 3.0
            baz = "test"

        members = get_members(Foo(), lambda x: isinstance(x, str))

        self.assertEqual(len(members), 1)
        self.assertIn("baz", members)


class TestSecondsSince(unittest.TestCase):
    @patch("lewis.core.utils.datetime")
    def test_seconds_since_past(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2016, 9, 1, 2, 0)

        self.assertEqual(seconds_since(datetime(2016, 9, 1, 1, 0)), 3600.0)

    @patch("lewis.core.utils.datetime")
    def test_seconds_since_future(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2016, 9, 1, 2, 0)

        self.assertEqual(seconds_since(datetime(2016, 9, 1, 3, 0)), -3600.0)

    @patch("lewis.core.utils.datetime")
    def test_seconds_since_none(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2016, 9, 1, 2, 0)

        self.assertRaises(TypeError, seconds_since, None)


class TestFromOptionalDependency(unittest.TestCase):
    def test_existing_module_works(self):
        a = FromOptionalDependency("time").do_import("sleep")

        from time import sleep as b

        self.assertEqual(a, b)

    def test_non_existing_members_in_module_dont_work(self):
        self.assertRaises(
            AttributeError, FromOptionalDependency("time").do_import, "sleep", "bleep"
        )

    def test_non_existing_module_works(self):
        A, B = FromOptionalDependency("invalid_module").do_import("A", "B")

        self.assertEqual(A.__name__, "A")
        self.assertEqual(B.__name__, "B")

        self.assertRaises(LewisException, A, "argument_one")
        self.assertRaises(LewisException, B, "argument_one", "argument_two")

    def test_string_exception_is_raised(self):
        A = FromOptionalDependency("invalid_module", "test").do_import("A")

        self.assertRaises(LewisException, A)

    def test_custom_exception_is_raised(self):
        A = FromOptionalDependency("invalid_module", ValueError("test")).do_import("A")

        self.assertRaises(ValueError, A)

    def test_exception_does_not_accept_arbitrary_type(self):
        self.assertRaises(RuntimeError, FromOptionalDependency, "invalid_module", 6.0)


class TestFormatDocText(unittest.TestCase):
    def test_lines_are_preserved_and_indented(self):
        text = "This is\na test\nwith multiple lines."
        expected = "    This is\n    a test\n    with multiple lines."
        self.assertEqual(format_doc_text(text), expected)

    def test_indented_lines_are_cleaned_up(self):
        text = "  This is\n  a test\n  with multiple lines."
        expected = "    This is\n    a test\n    with multiple lines."
        self.assertEqual(format_doc_text(text), expected)

    def test_long_lines_are_broken(self):
        text = " ".join(["ab"] * 44)
        expected = (
            "    " + " ".join(["ab"] * 32) + "\n" + "    " + " ".join(["ab"] * 12)
        )

        self.assertEqual(format_doc_text(text), expected)

    def test_no_lines_above_99(self):
        text = " ".join(["abc"] * 143)
        converted = format_doc_text(text).split("\n")

        self.assertTrue(all([len(line) <= 99 for line in converted]))


class TestCheckLimits(unittest.TestCase):
    def test_static_limits(self):
        class Foo:
            bar = 0

            @check_limits(0, 15)
            def set_bar(self, new_bar):
                self.bar = new_bar

        f = Foo()

        assertRaisesNothing(self, f.set_bar, 0)
        assertRaisesNothing(self, f.set_bar, 15)
        assertRaisesNothing(self, f.set_bar, 7)

        self.assertRaises(LimitViolationException, f.set_bar, -3)
        self.assertRaises(LimitViolationException, f.set_bar, 16)

    def test_upper_lower_only(self):
        class Foo:
            bar = 0
            baz = 1

            @check_limits(upper=15)
            def set_bar(self, new_bar):
                self.bar = new_bar

            @check_limits(lower=0)
            def set_baz(self, new_baz):
                self.baz = new_baz

        f = Foo()

        assertRaisesNothing(self, f.set_bar, 0)
        assertRaisesNothing(self, f.set_bar, 15)
        assertRaisesNothing(self, f.set_bar, -5)
        self.assertRaises(LimitViolationException, f.set_bar, 16)

        assertRaisesNothing(self, f.set_baz, 0)
        assertRaisesNothing(self, f.set_baz, 15)
        assertRaisesNothing(self, f.set_baz, 16)
        self.assertRaises(LimitViolationException, f.set_baz, -5)

    def test_property_limits(self):
        class Foo:
            bar = 0
            bar_min = 0
            bar_max = 15

            @check_limits("bar_min", "bar_max")
            def set_bar(self, new_bar):
                self.bar = new_bar

        f = Foo()

        assertRaisesNothing(self, f.set_bar, 0)
        assertRaisesNothing(self, f.set_bar, 15)

        self.assertRaises(LimitViolationException, f.set_bar, -3)
        self.assertRaises(LimitViolationException, f.set_bar, 16)

        f.bar_min = -3
        f.bar_max = 16

        assertRaisesNothing(self, f.set_bar, -3)
        assertRaisesNothing(self, f.set_bar, 16)

        f.bar_min = None
        f.bar_max = None

        assertRaisesNothing(self, f.set_bar, 123232224)
        assertRaisesNothing(self, f.set_bar, -352622234)

    def test_silent_mode(self):
        class Foo:
            bar = 0

            @check_limits(0, 15, silent=True)
            def set_bar(self, new_bar):
                self.bar = new_bar

        f = Foo()

        assertRaisesNothing(self, f.set_bar, 0)
        assertRaisesNothing(self, f.set_bar, 15)

        assertRaisesNothing(self, f.set_bar, -3)
        assertRaisesNothing(self, f.set_bar, 16)

        # Updates must have been ignored.
        self.assertEqual(f.bar, 15)
