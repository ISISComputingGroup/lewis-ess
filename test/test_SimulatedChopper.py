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

from lewis.devices.chopper.devices.device import SimulatedChopper
from lewis.devices.chopper.devices.states import DefaultIdleState


class TestSimulatedChopper(unittest.TestCase):
    def test_invalid_state_override_fails(self):
        self.assertRaises(
            RuntimeError,
            SimulatedChopper,
            override_states={"invalid": DefaultIdleState()},
        )

    def test_valid_state_override_does_not_fail(self):
        chopper = SimulatedChopper(override_states={"idle": DefaultIdleState()})

        self.assertIsInstance(chopper, SimulatedChopper)

    def test_invalid_transition_override_fails(self):
        self.assertRaises(
            RuntimeError,
            SimulatedChopper,
            override_transitions={("idle", "phase_locking"): lambda: True},
        )

    def test_valid_transition_override_does_not_fail(self):
        chopper = SimulatedChopper(
            override_transitions={("idle", "stopping"): lambda: True}
        )

        self.assertIsInstance(chopper, SimulatedChopper)
