#  -*- coding: utf-8 -*-
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

import unittest
from devices.linkam_t95 import SimulatedLinkamT95, DefaultStartedState


class TestSimulatedLinkamT95(unittest.TestCase):
    def test_default_construction(self):
        try:
            linkam = SimulatedLinkamT95()
        except:
            self.fail("Default construction of SimulatedLinkamT95 threw an exception.")

    def test_state_override_construction(self):
        try:
            linkam = SimulatedLinkamT95(override_states={'started': DefaultStartedState()})
        except:
            self.fail("Failed to override a state on construction.")

    def test_transition_override_construction(self):
        try:
            linkam = SimulatedLinkamT95(override_transitions={('init', 'stopped'): lambda: True})
        except:
            self.fail("Failed to override a transition on construction.")

    def test_default_status(self):
        linkam = SimulatedLinkamT95()
        status_bytes = linkam.getStatus()

        self.assertEqual(len(status_bytes), 10)
        self.assertFalse('\x00' in status_bytes)
        self.assertEqual(status_bytes[0], '\x01')
        self.assertEqual(status_bytes[1], '\x80')
        self.assertEqual(status_bytes[2], '\x80')

    def test_simple_heat(self):
        pass

    def test_simple_cool(self):
        pass

    def test_stop_command(self):
        pass

    def test_hold_and_resume(self):
        pass

    def test_pump_command(self):
        pass
