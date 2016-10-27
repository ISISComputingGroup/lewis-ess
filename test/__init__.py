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


def assertRaisesNothing(testobj, func, *args, **kwargs):
    """
    unittest does not have an assertRaisesNothing. This function adopted from
    the Mantid testhelpers module provides that functionality.

    :param testobj: A unittest object
    :param func: A callable object
    :param *args: Positional arguments passed to the callable as they are
    :param **kwargs: Keyword arguments, passed on as they are
    """
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        testobj.fail(
            "Assertion error. An exception was caught where none "
            "was expected in %s. Message: %s" % (func.__name__, str(exc)))
