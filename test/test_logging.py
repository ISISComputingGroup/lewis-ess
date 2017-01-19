# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
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

from lewis.core.logging import HasLog, root_logger_name


class TestHasLog(unittest.TestCase):
    def test_logger_name(self):
        class Foo(HasLog):
            pass

        a = Foo()

        self.assertEquals(a.log.name, '{}.Foo'.format(root_logger_name))

    def test_name_with_context(self):
        class Foo(HasLog):
            def __init__(self, context):
                super(Foo, self).__init__(context)

        str_context = 'string_context'

        a = Foo(str_context)
        self.assertEquals(a.log.name, '{}.string_context.Foo'.format(root_logger_name))

        class Bar(object):
            pass

        obj_context = Bar()

        b = Foo(obj_context)
        self.assertEquals(b.log.name, '{}.Bar.Foo'.format(root_logger_name))

    def test_setting_context_changes_name(self):
        class Foo(HasLog):
            pass

        a = Foo()
        self.assertEquals(a.log.name, '{}.Foo'.format(root_logger_name))

        a._set_logging_context('some_context')
        self.assertEquals(a.log.name, '{}.some_context.Foo'.format(root_logger_name))

        a._set_logging_context(None)
        self.assertEquals(a.log.name, '{}.Foo'.format(root_logger_name))
