#  -*- coding: utf-8 -*-
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

import unittest

from core.utils import dict_strict_update


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


from core.utils import extract_module_name
import os, shutil
import tempfile


def generate_fake_package_structure():
    _tmp_package = tempfile.mkdtemp()
    _tmp_dir = tempfile.gettempdir()

    files = {k: os.path.join(_tmp_package, v) for k, v in dict(
        valid='some_file.py',
        invalid_ext='some_other_file.pyc',
        invalid_name='_some_invalid_file.py',
    ).iteritems()}

    for abs_file_name in files.values():
        with open(abs_file_name, mode='w'):
            pass

    dirs = {k: os.path.join(_tmp_package, v) for k, v in dict(
        valid='some_dir',
        empty='empty_dir',
        invalid='_invalid',
    ).iteritems()}

    for abs_dir_name in dirs.values():
        os.mkdir(abs_dir_name)

    with open(os.path.join(_tmp_package, 'some_dir', '__init__.py'), 'w'):
        pass

    return _tmp_package, _tmp_dir, files, dirs, ['some_file', 'some_dir']


class TestExtractModuleName(unittest.TestCase):
    def setUp(self):
        self._tmp_package, tmp_dir, self._files, self._dirs, expected = generate_fake_package_structure()

    def tearDown(self):
        shutil.rmtree(self._tmp_package)

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
