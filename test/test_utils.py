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

import os
import shutil
import tempfile
import unittest
import sys
from datetime import datetime

from mock import patch
from six import iteritems

from plankton.core.utils import dict_strict_update, extract_module_name, \
    is_module, seconds_since, get_available_submodules, FromOptionalDependency
from plankton.core.exceptions import StubAccessException


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


class TestWithPackageStructure(unittest.TestCase):
    """
    This is an intermediate class that creates a package structure in the
    system's temporary file directory. The structure is as follows:

        tmp_dir (random name)
         |
         +- some_dir
         |   |
         |   +- __init__.py
         +- _invalid
         +- empty_dir
         +- some_file.py
         +- some_other_file.pyc
         +- _some_invalid_file.py
         +- __init__.py

    All files are empty and the entire structure is deleted in the tearDown.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmp_dir = tempfile.mkdtemp()
        cls._tmp_package = tempfile.mkdtemp(dir=cls._tmp_dir)
        cls._tmp_package_name = os.path.basename(cls._tmp_package)

        cls._files = {k: os.path.join(cls._tmp_package, v) for k, v in iteritems(dict(
            valid='some_file.py',
            invalid_ext='some_other_file.pyc',
            invalid_name='_some_invalid_file.py',
        ))}

        for abs_file_name in cls._files.values():
            with open(abs_file_name, mode='w'):
                pass

        cls._dirs = {k: os.path.join(cls._tmp_package, v) for k, v in iteritems(dict(
            valid='some_dir',
            empty='empty_dir',
            invalid='_invalid',
        ))}

        for abs_dir_name in cls._dirs.values():
            os.mkdir(abs_dir_name)

        with open(os.path.join(cls._tmp_package, '__init__.py'), 'w'):
            pass

        with open(os.path.join(cls._tmp_package, 'some_dir', '__init__.py'), 'w'):
            pass

        cls._expected_modules = ['some_dir', 'some_file']

        sys.path.insert(0, cls._tmp_dir)

    @classmethod
    def tearDownClass(cls):
        sys.path.pop(sys.path.index(cls._tmp_dir))
        shutil.rmtree(cls._tmp_dir)


class TestExtractModuleName(TestWithPackageStructure):
    def test_directory_basename_is_returned(self):
        self.assertEqual(extract_module_name(self._dirs['valid']), 'some_dir')

    def test_directory_invalid_name(self):
        self.assertEqual(extract_module_name(self._dirs['invalid']), None)

    def test_file_invalid_name(self):
        self.assertEqual(extract_module_name(self._files['invalid_name']), None)

    def test_file_invalid_extension(self):
        self.assertEqual(extract_module_name(self._files['invalid_ext']), None)

    def test_file_basename_without_extension(self):
        self.assertEqual(extract_module_name(self._files['valid']), 'some_file')


class TestIsModule(TestWithPackageStructure):
    def test_valid_directory(self):
        self.assertTrue(is_module(
            extract_module_name(self._dirs['valid']), [self._tmp_package]), self._tmp_package)

    def test_invalid_directory(self):
        self.assertFalse(is_module(
            extract_module_name(self._dirs['invalid']), [self._tmp_package]))

    def test_invalid_file_name(self):
        self.assertFalse(is_module(
            extract_module_name(self._files['invalid_name']), [self._tmp_package]))

    def test_invalid_file_ext(self):
        self.assertFalse(is_module(
            extract_module_name(self._files['invalid_ext']), [self._tmp_package]))

    def test_valid_file(self):
        self.assertTrue(is_module(
            extract_module_name(self._files['valid']), [self._tmp_package]), self._tmp_package)


class TestGetAvailableSubModules(TestWithPackageStructure):
    def test_correct_modules_are_returned(self):
        self.assertEqual(sorted(get_available_submodules(self._tmp_package_name)),
                         sorted(self._expected_modules))


class TestSecondsSince(unittest.TestCase):
    @patch('plankton.core.utils.datetime')
    def test_seconds_since_past(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2016, 9, 1, 2, 0)

        self.assertEqual(seconds_since(datetime(2016, 9, 1, 1, 0)), 3600.0)

    @patch('plankton.core.utils.datetime')
    def test_seconds_since_future(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2016, 9, 1, 2, 0)

        self.assertEqual(seconds_since(datetime(2016, 9, 1, 3, 0)), -3600.0)

    @patch('plankton.core.utils.datetime')
    def test_seconds_since_none(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2016, 9, 1, 2, 0)

        self.assertRaises(TypeError, seconds_since, None)


class TestFrom(unittest.TestCase):
    def test_existing_module_works(self):
        a, = FromOptionalDependency('time').do_import('sleep')

        from time import sleep as b

        self.assertEqual(a, b)

    def test_non_existing_members_in_module_dont_work(self):
        self.assertRaises(AttributeError, FromOptionalDependency('time').do_import, 'sleep', 'bleep')

    def test_non_existing_module_works(self):
        A, B = FromOptionalDependency('invalid_module').do_import('A', 'B')

        self.assertEqual(A.__name__, 'A')
        self.assertEqual(B.__name__, 'B')

        self.assertRaises(StubAccessException, A, 'argument_one')
        self.assertRaises(StubAccessException, B, 'argument_one', 'argument_two')
