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
Defines functions that model typical behavior, such as a value approaching a target linearly at
a certain rate.
"""


def linear(current, target, rate, dt):
    """
    This function returns the new value after moving towards
    target at the given speed constantly for the time dt.

    If for example the current position is 10 and the target is -20,
    the returned value will be less than 10 if rate and dt are greater
    than 0:

    .. sourcecode:: Python

        new_pos = linear(10, -20, 10, 0.1)  # new_pos = 9

    The function makes sure that the returned value never overshoots:

    .. sourcecode:: Python

        new_pos = linear(10, -20, 10, 100)  # new_pos = -20

    :param current: The current value of the variable to be changed.
    :param target: The target value to approach.
    :param rate: The rate at which the parameter should move towards target.
    :param dt: The time for which to calculate the change.
    :return: The new variable value.
    """
    sign = (target > current) - (target < current)

    if not sign:
        return current

    new_value = current + sign * rate * dt

    if sign * new_value > sign * target:
        return target

    return new_value
