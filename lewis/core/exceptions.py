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

"""
Defines exception types specific to lewis. The main intention of these exception types is
that they can be caught and meaningful messages can be displayed to the user.
"""


class LewisException(Exception):
    """
    This exception type is used to distinguish exceptions that are expected
    from unexpected ones. This enables better error handling and more importantly
    better presentation of errors to the users.
    """


class LimitViolationException(Exception):
    """
    An exception that can be raised in a device to indicate a limit violation. It is for example
    raised by the :class:`~lewis.core.utils.check_limits`.
    """


class AccessViolationException(Exception):
    """
    This exception can be raised in situation where the performed action (accessing a property or
    similar) is not allowed. An example is :class:`~lewis.adapters.epics.BoundPV` for enforcing
    read-only PVs.
    """
