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

from lewis.core.logging import has_log, root_logger_name


class TestHasLog(unittest.TestCase):
    def test_logger_name(self):
        @has_log
        class Foo:
            pass

        a = Foo()

        self.assertEqual(a.log.name, "{}.Foo".format(root_logger_name))

    def test_setting_context_changes_name(self):
        @has_log
        class Foo:
            pass

        a = Foo()
        self.assertEqual(a.log.name, "{}.Foo".format(root_logger_name))

        a._set_logging_context("some_context")
        self.assertEqual(a.log.name, "{}.some_context.Foo".format(root_logger_name))

        a._set_logging_context(None)
        self.assertEqual(a.log.name, "{}.Foo".format(root_logger_name))

    def test_decorate_function(self):
        @has_log
        def foo(bar):
            return bar

        self.assertTrue(hasattr(foo, "log"))
        self.assertEqual(foo.log.name, "{}.foo".format(root_logger_name))
