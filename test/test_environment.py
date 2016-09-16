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
from . import assertRaisesNothing

from core.environment import SimulationEnvironment

try:
    from unittest.mock import Mock, patch, call, ANY
except ImportError:
    from mock import Mock, patch, call, ANY


def set_simulation_running(environment):
    environment._running = True
    environment._started = True


class TestSimulationEnvironment(unittest.TestCase):
    @patch('core.environment.seconds_since')
    def test_process_cycle_returns_elapsed_time(self, elapsed_seconds_mock):
        env = SimulationEnvironment(Mock())

        # It doesn't matter what happens in the simulation cycle, here we
        # only care how long it took.
        with patch.object(env, '_process_simulation_cycle'):
            elapsed_seconds_mock.return_value = 0.5
            delta = env._process_cycle(0.0)

            elapsed_seconds_mock.assert_called_once_with(ANY)
            self.assertEqual(delta, 0.5)

    @patch('core.environment.seconds_since')
    def test_process_cycle_changes_runtime_status(self, elapsed_seconds_mock):
        env = SimulationEnvironment(Mock())

        with patch.object(env, '_process_simulation_cycle'):
            self.assertEqual(env.runtime, 0.0)
            self.assertEqual(env.cycles, 0)

            elapsed_seconds_mock.return_value = 0.5
            env._process_cycle(0.0)

            self.assertEqual(env.runtime, 0.5)
            self.assertEqual(env.cycles, 1)

    def test_pause_resume(self):
        env = SimulationEnvironment(Mock())

        self.assertFalse(env.is_started)
        self.assertFalse(env.is_paused)

        # env is not running, so it can't be paused
        self.assertRaises(RuntimeError, env.pause)

        # Fake start of simulation, we don't need to care how this happened
        set_simulation_running(env)

        self.assertTrue(env.is_started)
        self.assertFalse(env.is_paused)

        assertRaisesNothing(self, env.pause)

        self.assertTrue(env.is_started)
        self.assertTrue(env.is_paused)

        assertRaisesNothing(self, env.resume)

        # now it's running, so it can't be resumed again
        self.assertRaises(RuntimeError, env.resume)

    @patch('core.environment.sleep')
    def test_process_cycle_calls_sleep_if_paused(self, sleep_mock):
        env = SimulationEnvironment(Mock())
        set_simulation_running(env)

        # simulation is running, should not call sleep_mock
        env._process_cycle(0.5)
        sleep_mock.assert_not_called()

        env.pause()
        env._process_cycle(0.5)
        sleep_mock.assert_called_once_with(env.processing_time)

    def test_process_cycle_calls_process_simulation(self):
        adapter_mock = Mock()
        env = SimulationEnvironment(adapter_mock)
        set_simulation_running(env)

        env._process_cycle(0.5)
        adapter_mock.assert_has_calls(
            [call.process(0.5, env.processing_time)])

        self.assertEqual(env.simulation_cycles, 1)
        self.assertEqual(env.simulation_runtime, 0.5)

    def test_process_simulation_cycle_applies_time_warp(self):
        adapter_mock = Mock()
        env = SimulationEnvironment(adapter_mock)
        set_simulation_running(env)

        env.time_warp = 2.0
        env._process_cycle(0.5)

        adapter_mock.assert_has_calls(
            [call.process(1.0, env.processing_time)])

        self.assertEqual(env.simulation_cycles, 1)
        self.assertEqual(env.simulation_runtime, 1.0)

    def test_process_calls_control_server(self):
        control_mock = Mock()
        env = SimulationEnvironment(Mock(), control_mock)

        set_simulation_running(env)
        env._process_cycle(0.5)

        control_mock.assert_has_calls([call.process()])

    def test_time_warp_factor_range(self):
        env = SimulationEnvironment(Mock())

        assertRaisesNothing(self, setattr, env, 'time_warp', 3.0)
        self.assertEqual(env.time_warp, 3.0)

        assertRaisesNothing(self, setattr, env, 'time_warp', 0.1)
        self.assertEqual(env.time_warp, 0.1)

        self.assertRaises(ValueError, setattr, env, 'time_warp', -0.5)
        self.assertRaises(ValueError, setattr, env, 'time_warp', 0.0)

    def test_processing_time_range(self):
        env = SimulationEnvironment(Mock())

        assertRaisesNothing(self, setattr, env, 'processing_time', 0.2)
        self.assertEqual(env.processing_time, 0.2)

        assertRaisesNothing(self, setattr, env, 'processing_time', 0.15)
        self.assertEqual(env.processing_time, 0.15)

        self.assertRaises(ValueError, setattr, env, 'processing_time', -0.5)
        self.assertRaises(ValueError, setattr, env, 'processing_time', 0.0)

    def test_start_stop(self):
        env = SimulationEnvironment(Mock())

        with patch.object(env, '_process_cycle', side_effect=lambda x: env.stop()) as mock_cycle:
            env.start()

            mock_cycle.assert_has_calls([call(0.0)])

    def test_control_server_setter(self):
        env = SimulationEnvironment(Mock())

        control_mock = Mock()
        assertRaisesNothing(self, setattr, env, 'control_server', control_mock)
        self.assertEqual(env.control_server, control_mock)
        
        assertRaisesNothing(self, setattr, env, 'control_server', None)

        set_simulation_running(env)

        # Can set new control server even when simulation is running
        assertRaisesNothing(self, setattr, env, 'control_server', Mock())

        # Can not replace control server when simulation is running
        self.assertRaises(RuntimeError, setattr, env, 'control_server', Mock())
