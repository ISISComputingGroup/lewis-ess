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

import time
from functools import wraps

from lewis.core.logging import has_log


def _get_device_from(instance):
    try:
        device = instance.device
    except AttributeError:
        try:
            device = instance._device
        except AttributeError:
            raise AttributeError(
                "Expected device to be accessible as either self.device or self._device"
            )
    return device


def conditional_reply(property_name, reply=None):
    """
    Decorator that executes the command and replies if the device has a member called 'property name' and it is True in
    a boolean context. Example usage:

    .. sourcecode:: Python

        @conditional_reply("connected")
        def acknowledge_pressure(channel):
            return ACK

    :param property_name: The name of the property to look for on the device
    :param reply: Desired output reply string when condition is false

    :return: The function returns as normal if property is true. The command is not executed and there is no reply if
       property is false

    :except AttributeError if the first argument of the decorated function (self) does not contain .device or ._device
    :except AttributeError if the device does not contain a property called property_name
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):

            device = _get_device_from(self)

            try:
                do_reply = getattr(device, property_name)
            except AttributeError:
                raise AttributeError(
                    "Expected device to contain an attribute called '{}' but it wasn't found.".format(
                        property_name
                    )
                )

            return func(self, *args, **kwargs) if do_reply else reply

        return wrapper

    return decorator


class _LastInput:
    last_input_time = 0


@has_log
def timed_reply(action, reply=None, minimum_time_delay=0):
    """
    Decorator that inhibits a command and performs a action if call time is less than than some minimum time delay
    between the the current and last input.  Example usage:

    .. sourcecode:: Python

        @timed_reply(action="crash_pump", reply="WARNING: Input too quick", minimum_time_delay=150)
        def acknowledge_pressure(channel):
            return ACK

    :param action: The name of the method to execute for on the device
    :param reply: Desired output reply string when input time delay is less than the minimum
    :param minimum_time_delay: The minimum time (ms) between commands sent to the device

    :return: The function returns as normal if minimum delay exceeded. The command is not executed and the action method
     is called on the device instead

    :except AttributeError if the first argument of the decorated function (self) does not contain .device or ._device
    :except AttributeError if the device does not contain a property called action
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                new_input_time = int(round(time.time() * 1000))
                time_since_last_request = new_input_time - _LastInput.last_input_time
                valid_input = time_since_last_request > minimum_time_delay
                if valid_input:
                    _LastInput.last_input_time = new_input_time
                    return func(self, *args, **kwargs)
                else:
                    self.log.info(
                        "Violated time tolerance ({}ms) was {}ms. Calling action ({}) on device".format(
                            minimum_time_delay, time_since_last_request, action
                        )
                    )
                    device = _get_device_from(self)
                    action_function = getattr(device, action)
                    action_function()
                    return reply

            except AttributeError:
                raise AttributeError(
                    "Expected device to contain an attribute called '{}' but it wasn't found.".format(
                        self.action
                    )
                )

        return wrapper

    return decorator
