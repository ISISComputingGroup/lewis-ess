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
