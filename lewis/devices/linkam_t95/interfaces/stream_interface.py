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

from lewis.adapters.stream import Cmd, StreamInterface
from lewis.core.logging import has_log


@has_log
class LinkamT95StreamInterface(StreamInterface):
    """
    Linkam T95 TCP stream interface

    This is the interface of a simulated Linkam T95 device. The device listens on a configured
    host:port-combination, one option to connect to it is via telnet:

        $ telnet host port

    Once connected, it's possible to send the specified commands, described in the dynamically
    generated documentation. Information about host, port and line terminators in the concrete
    device instance are also generated dynamically.
    """

    out_terminator = b"\r"

    commands = {
        Cmd("get_status", "^T$", return_mapping=lambda x: x),
        Cmd("set_rate", "^R1([0-9]+)$"),
        Cmd("set_limit", "^L1([0-9]+)$"),
        Cmd("start", "^S$"),
        Cmd("stop", "^E$"),
        Cmd("hold", "^O$"),
        Cmd("heat", "^H$"),
        Cmd("cool", "^C$"),
        Cmd("pump_command", "^P(a0|m0|[0123456789:;<=>?@ABCDEFGHIJKLMN]{1})$"),
    }

    def get_status(self):
        """
        Models "T Command" functionality of device.

        Returns all available status information about the device as single byte array.

        :return: Byte array consisting of 10 status bytes.
        """

        # "The first command sent must be a 'T' command" from T95 manual
        self.device.serial_command_mode = True

        Tarray = [0x80] * 10

        # Status byte (SB1)
        Tarray[0] = {
            "stopped": 0x01,
            "heat": 0x10,
            "cool": 0x20,
            "hold": 0x30,
        }.get(self.device._csm.state, 0x01)

        if Tarray[0] == 0x30 and self.device.hold_commanded:
            Tarray[0] = 0x50

        # Error status byte (EB1)
        if self.device.pump_overspeed:
            Tarray[1] |= 0x01
        # TODO: Add support for other error conditions?

        # Pump status byte (PB1)
        Tarray[2] = 0x80 + self.device.pump_speed

        # Temperature
        Tarray[6:10] = [
            ord(x) for x in "%04x" % (int(self.device.temperature * 10) & 0xFFFF)
        ]

        return bytes(Tarray)

    def set_rate(self, param):
        """
        Models "Rate Command" functionality of device.

        Sets the target rate of temperature change.

        :param param: Rate of temperature change in C/min, multiplied by 100, as a string.
        Must be positive.
        :return: Empty string.
        """
        # TODO: Is not having leading zeroes / 4 digits an error?
        rate = int(param)
        if 1 <= rate <= 15000:
            self.device.temperature_rate = rate / 100.0
        return b""

    def set_limit(self, param):
        """
        Models "Limit Command" functionality of device.

        Sets the target temperate to be reached.

        :param param: Target temperature in C, multiplied by 10, as a string. Can be negative.
        :return: Empty string.
        """
        # TODO: Is not having leading zeroes / 4 digits an error?
        limit = int(param)
        if -2000 <= limit <= 6000:
            self.device.temperature_limit = limit / 10.0
        return b""

    def start(self):
        """
        Models "Start Command" functionality of device.

        Tells the T95 unit to start heating or cooling at the rate specified by setRate and to a
        limit set by setLimit.

        :return: Empty string.
        """
        self.device.start_commanded = True
        return b""

    def stop(self):
        """
        Models "Stop Command" functionality of device.

        Tells the T95 unit to stop heating or cooling.

        :return: Empty string.
        """
        self.device.stop_commanded = True
        return b""

    def hold(self):
        """
        Models "Hold Command" functionality of device.

        Device will hold current temperature until a heat or cool command is issued.

        :return: Empty string.
        """
        self.device.hold_commanded = True
        return b""

    def heat(self):
        """
        Models "Heat Command" functionality of device.

        :return: Empty string.
        """
        # TODO: Is this really all it does?
        self.device.hold_commanded = False
        return b""

    def cool(self):
        """
        Models "Cool Command" functionality of device.

        :return: Empty string.
        """
        # TODO: Is this really all it does?
        self.device.hold_commanded = False
        return b""

    def pump_command(self, param):
        """
        Models "LNP Pump Commands" functionality of device.

        Switches between automatic or manual pump mode, and adjusts speed when in manual mode.

        :param param: 'a0' for auto, 'm0' for manual, [0-N] for speed.
        :return:
        """
        lookup = b"0123456789:;<=>?@ABCDEFGHIJKLMN"

        if param == b"a0":
            self.device.pump_manual_mode = False
        elif param == b"m0":
            self.device.pump_manual_mode = True
        elif param in lookup:
            self.device.manual_target_speed = lookup.index(param)
        return b""

    def handle_error(self, request, error):
        """
        If command is not recognised print and error

        Args:
            request: requested string
            error: problem

        """
        self.log.error(
            "An error occurred at request " + repr(request) + ": " + repr(error)
        )
