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

from lewis.adapters.stream import Cmd, StreamInterface, Var
from lewis.devices import Device


class SubUnit:
    """
    A sub unit of the VerySimpleDevice. It has a serial number, a friendly name, and a counter.
    There is a method that increments the counter by 1.
    """

    def __init__(self, serial_number=123, name="subunit"):
        self.serial_number = serial_number
        self.name = name
        self.counter = 0

    def increment_counter(self):
        self.counter += 1
        return f"New counter value: {self.counter}"


class VerySimpleDevice(Device):
    """
    The device has a simple parameter, stores a subunit, and has an internal identifier
    (that is not accessible through the interface) stored as bytes. The interface provides
    commands to communicate with the device and its subunit
    """

    param = 10
    internal_id = b"\x0D\x00\x04\x00\x00\x00"
    subunit = SubUnit(name="unit1", serial_number="15092021")


class VerySimpleInterface(StreamInterface):
    """
    A very simple device with TCP-stream interface

    The device has only one parameter of its own, which can be set to an arbitrary
    value. It also has a SubUnit.
    To connect:

        $ telnet host port

    After that, typing either of the commands and pressing enter sends them to the server.

    The commands are:

     - ``V``: Returns the parameter as part of a verbose message.
     - ``V=something``: Sets the parameter to ``something``.
     - ``P``: Returns the device parameter unmodified.
     - ``P=something``: Exactly the same as ``V=something``.
     - ``R`` or ``r``: Returns the number 4.

     To communicate with the SubUnit:

     - ``SU`` : Returns the name and serial number
     - ``SU C?``: Returns the counter value
     - ``SU C X``: Sets the counter value to X (where X is an integer)
     - ``SU I`` : Increment the counter value

    """

    commands = {
        Cmd("get_param", pattern="^V$", return_mapping="The value is {}".format),
        Cmd("set_param", pattern="^V=(.+)$", argument_mappings=(int,)),
        Var(
            "param",
            read_pattern="^P$",
            write_pattern="^P=(.+)$",
            doc="The only parameter.",
        ),
        Cmd(lambda: 4, pattern="^R$(?i)", doc='"Random" number (4).'),
        Cmd(
            "get_subunit",
            pattern="^SU$",
        ),
        Cmd(
            "get_counter",
            pattern="^SU C\?$",
            return_mapping="SubUnit counter = {}".format,
        ),
        Cmd(
            "increment_counter",
            pattern="^SU I$",
        ),
        Cmd("set_counter", pattern="^SU C\s([0-9]*)$", argument_mappings=(int,)),
    }

    in_terminator = "\r\n"
    out_terminator = "\r\n"

    def get_param(self):
        """Returns the device parameter."""
        return self.device.param

    def set_param(self, new_param):
        """Set the device parameter, does not return anything."""
        self.device.param = new_param

    def get_subunit(self):
        s = self.device.subunit
        return f"SubUnit: Name = {s.name}, Serial = {s.serial_number}"

    def get_counter(self):
        return self.device.subunit.counter

    def increment_counter(self):
        self.device.subunit.increment_counter()

    def set_counter(self, value):
        self.device.subunit.counter = value

    def handle_error(self, request, error):
        return "An error occurred: " + repr(error)
