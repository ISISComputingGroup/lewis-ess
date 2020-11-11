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

from lewis.devices.linkam_t95.devices.device import SimulatedLinkamT95
from lewis.devices.linkam_t95.devices.states import DefaultStartedState
from lewis.devices.linkam_t95.interfaces.stream_interface import (
    LinkamT95StreamInterface,
)

from .utils import assertRaisesNothing


class TestSimulatedLinkamT95(unittest.TestCase):
    def test_default_construction(self):
        assertRaisesNothing(self, SimulatedLinkamT95)

    def test_state_override_construction(self):
        assertRaisesNothing(
            self, SimulatedLinkamT95, override_states={"started": DefaultStartedState()}
        )

    def test_transition_override_construction(self):
        assertRaisesNothing(
            self,
            SimulatedLinkamT95,
            override_transitions={("init", "stopped"): lambda: True},
        )

    def test_default_status(self):
        linkam = LinkamT95StreamInterface()
        linkam.device = SimulatedLinkamT95()

        status_bytes = linkam.get_status()

        self.assertEqual(len(status_bytes), 10)  # Byte array should always be 10 bytes
        self.assertFalse("\x00" in status_bytes)  # Byte array may not contain zeroes
        self.assertEqual(status_bytes[0], "\x01")  # Status byte should be 1 on startup
        self.assertEqual(
            status_bytes[1], "\x80"
        )  # No error flags should be set on startup
        self.assertEqual(
            status_bytes[2], "\x80"
        )  # The pump should not be active on startup
        self.assertEqual(status_bytes[6:10], "00f0")  # Starting temperature 24C

    def test_simple_heat(self):
        linkam = LinkamT95StreamInterface()

        linkam_device = SimulatedLinkamT95()
        linkam.device = linkam_device

        linkam_device.process()  # Initialize

        # Issue T command to get into stopped state
        linkam.get_status()
        linkam_device.process()

        # Set up to heat from 24.0 C to 44.0 C at 20.00 C/min
        linkam.set_rate("2000")
        linkam.set_limit("440")
        linkam.start()
        linkam_device.process()

        # Heat for almost a minute but not quite
        linkam_device.process(59.5)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[0], "\x10")  # Heating status set
        self.assertNotEqual(status_bytes[6:10], "01b8")  # Temp != 44.0 C

        # Finish off heating (and overshoot a bit)
        linkam_device.process(5)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[6:10], "01b8")  # Temp == 44.0 C

        # Should hold now, so temperature should not change
        linkam_device.process(10)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[0], "\x30")  # Auto-holding at limit
        self.assertEqual(status_bytes[6:10], "01b8")  # Temp == 44.0 C

    def test_simple_cool(self):
        linkam = LinkamT95StreamInterface()
        linkam_device = SimulatedLinkamT95()
        linkam.device = linkam_device

        linkam_device.process()  # Initialize

        # Issue T command to get into stopped state
        linkam.get_status()
        linkam_device.process()

        # Set up to cool from 24.0 C to 4.0 C at 20.00 C/min
        linkam.set_rate("2000")
        linkam.set_limit("40")
        linkam.start()
        linkam_device.process()

        # Cool for almost a minute but not quite
        linkam_device.process(59.5)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[0], "\x20")  # Cooling status set
        self.assertNotEqual(status_bytes[6:10], "0028")  # Temp != 4.0 C

        # Finish off cooling (and overshoot a bit)
        linkam_device.process(5)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[6:10], "0028")  # Temp == 4.0 C

        # Should hold now, so temperature should not change
        linkam_device.process(10)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[0], "\x30")  # Auto-holding at limit
        self.assertEqual(status_bytes[6:10], "0028")  # Temp == 4.0 C

    def test_error_flag_overcool(self):
        linkam = LinkamT95StreamInterface()
        linkam_device = SimulatedLinkamT95()
        linkam.device = linkam_device

        linkam_device.process()  # Initialize

        # Issue T command to get into stopped state
        linkam.get_status()
        linkam_device.process()

        # Ensure flag is not set
        status_bytes = linkam.get_status()
        self.assertFalse(ord(status_bytes[1]) & 0x01)

        # Set up to cool from 24.0 C to 4.0 C at 51.00 C/min
        linkam.set_rate("5100")
        linkam.set_limit("40")
        linkam.start()
        linkam_device.process()

        # Ensure flag is set after running a bit
        linkam_device.process(0.1)
        status_bytes = linkam.get_status()
        self.assertTrue(ord(status_bytes[1]) & 0x01)

    def test_stop_command(self):
        linkam = LinkamT95StreamInterface()
        linkam_device = SimulatedLinkamT95()
        linkam.device = linkam_device

        linkam_device.process()  # Initialize

        # Issue T command to get into stopped state
        linkam.get_status()
        linkam_device.process()

        # Set up to heat from 24.0 C to 44.0 C at 20.00 C/min
        linkam.set_rate("2000")
        linkam.set_limit("440")
        linkam.start()
        linkam_device.process()

        # Process for some time and then stop
        linkam_device.process(10)
        linkam.stop()
        linkam_device.process()

        # Ensure status byte reports stopped
        status_bytes = linkam.get_status()
        self.assertEqual(ord(status_bytes[0]), 0x01)

    def test_hold_and_resume(self):
        linkam = LinkamT95StreamInterface()
        linkam_device = SimulatedLinkamT95()
        linkam.device = linkam_device

        linkam_device.process()  # Initialize

        # Issue T command to get into stopped state
        linkam.get_status()
        linkam_device.process()

        # Set up to cool from 24.0 C to 4.0 C at 20.00 C/min
        linkam.set_rate("2000")
        linkam.set_limit("40")
        linkam.start()
        linkam_device.process()

        # Cool for a while
        linkam_device.process(30)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[0], "\x20")  # Cooling status set
        self.assertNotEqual(status_bytes[6:10], "0028")  # Temp != 4.0 C

        # Hold for a while
        linkam.hold()
        linkam_device.process(30)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[0], "\x50")  # Manually holding
        self.assertNotEqual(status_bytes[6:10], "0028")  # Temp != 4.0 C

        # Cool some more
        linkam.cool()
        linkam_device.process(15)
        status_bytes = linkam.get_status()
        self.assertNotEqual(status_bytes[6:10], "0028")  # Temp != 4.0 C

        # Hold again
        linkam.hold()
        linkam_device.process(30)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[0], "\x50")  # Manually holding
        self.assertNotEqual(status_bytes[6:10], "0028")  # Temp != 4.0 C

        # Finish cooling via heat command (should also work)
        linkam.heat()
        linkam_device.process(15)
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[6:10], "0028")  # Temp == 4.0 C

        # Make sure transitions to auto-holding
        linkam_device.process()
        status_bytes = linkam.get_status()
        self.assertEqual(status_bytes[0], "\x30")  # Auto-holding at limit

    def test_pump_command(self):
        linkam = LinkamT95StreamInterface()
        linkam_device = SimulatedLinkamT95()
        linkam.device = linkam_device

        linkam_device.process()  # Initialize

        # Issue T command to get into stopped state
        linkam.get_status()
        linkam_device.process()

        # Set up to cool from 24.0 C to 4.0 C at 20.00 C/min
        linkam.set_rate("2000")
        linkam.set_limit("40")
        linkam.start()
        linkam_device.process()

        # Since the pump feature is not fully implemented,
        # we can only make sure all valid input is accepted
        assertRaisesNothing(self, linkam.pump_command, "m0")  # Manual
        linkam_device.process()

        for int_value, char_value in enumerate("0123456789:;<=>?@ABCDEFGHIJKLMN"):
            assertRaisesNothing(
                self, linkam.pump_command, char_value
            )  # Characters mean speeds 0 - 30
            linkam_device.process()
            status_bytes = linkam.get_status()
            self.assertEqual(
                status_bytes[2], chr(0x80 | int_value)
            )  # Verify Pump Status Byte reflects speed

        assertRaisesNothing(self, linkam.pump_command, "a0")  # Auto
        linkam_device.process()
