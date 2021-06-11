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


class VerySimpleDevice(Device):
    param = 10


class VerySimpleInterface(StreamInterface):
    """
    A very simple device with TCP-stream interface

    The device has only one parameter, which can be set to an arbitrary
    value. The interface consists of five commands which can be invoked via telnet.
    To connect:

        $ telnet host port

    After that, typing either of the commands and pressing enter sends them to the server.

    The commands are:

     - ``V``: Returns the parameter as part of a verbose message.
     - ``V=something``: Sets the parameter to ``something``.
     - ``P``: Returns the device parameter unmodified.
     - ``P=something``: Exactly the same as ``V=something``.
     - ``R`` or ``r``: Returns the number 4.

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
    }

    in_terminator = "\r\n"
    out_terminator = "\r\n"

    def get_param(self):
        """Returns the device parameter."""
        return self.device.param

    def set_param(self, new_param):
        """Set the device parameter, does not return anything."""
        self.device.param = new_param

    def handle_error(self, request, error):
        return "An error occurred: " + repr(error)
