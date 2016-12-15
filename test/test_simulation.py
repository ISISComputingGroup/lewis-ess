# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
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

from mock import Mock, patch, call, ANY

from lewis.core.simulation import Simulation
from . import assertRaisesNothing


def set_simulation_running(environment):
    environment._running = True
    environment._started = True


class TestSimulation(unittest.TestCase):
    @patch('lewis.core.simulation.seconds_since')
    def test_process_cycle_returns_elapsed_time(self, elapsed_seconds_mock):
        env = Simulation(device=Mock(), adapter=Mock())

        # It doesn't matter what happens in the simulation cycle, here we
        # only care how long it took.
        with patch.object(env, '_process_simulation_cycle'):
            elapsed_seconds_mock.return_value = 0.5
            delta = env._process_cycle(0.0)

            elapsed_seconds_mock.assert_called_once_with(ANY)
            self.assertEqual(delta, 0.5)

    @patch('lewis.core.simulation.seconds_since')
    def test_process_cycle_changes_runtime_status(self, elapsed_seconds_mock):
        env = Simulation(device=Mock(), adapter=Mock())

        with patch.object(env, '_process_simulation_cycle'):
            self.assertEqual(env.uptime, 0.0)

            set_simulation_running(env)

            elapsed_seconds_mock.return_value = 0.5
            env._process_cycle(0.0)

            self.assertEqual(env.uptime, 0.5)

    def test_pause_resume(self):
        env = Simulation(device=Mock(), adapter=Mock())

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

    def test_process_cycle_calls_sleep_if_paused(self):
        device_mock = Mock()
        env = Simulation(device=device_mock, adapter=Mock())
        set_simulation_running(env)
        env.pause()

        # simulation paused, device should not be called
        env._process_cycle(0.5)
        device_mock.assert_not_called()

        env.resume()
        # simulation is running now, device should be called
        env._process_cycle(0.5)

        device_mock.assert_has_calls([call.process(0.5)])

    def test_process_cycle_calls_process_simulation(self):
        adapter_mock = Mock()
        device_mock = Mock()
        env = Simulation(device=device_mock, adapter=adapter_mock)
        set_simulation_running(env)

        env._process_cycle(0.5)
        adapter_mock.assert_has_calls(
            [call.handle(env.cycle_delay)])
        device_mock.assert_has_calls(
            [call.process(0.5)]
        )

        self.assertEqual(env.cycles, 1)
        self.assertEqual(env.runtime, 0.5)

    def test_process_simulation_cycle_applies_speed(self):
        adapter_mock = Mock()
        device_mock = Mock()

        env = Simulation(device=device_mock, adapter=adapter_mock)
        set_simulation_running(env)

        env.speed = 2.0
        env._process_cycle(0.5)

        adapter_mock.assert_has_calls(
            [call.handle(env.cycle_delay)])
        device_mock.assert_has_calls(
            [call.process(1.0)])

        self.assertEqual(env.cycles, 1)
        self.assertEqual(env.runtime, 1.0)

    def test_process_calls_control_server(self):
        env = Simulation(device=Mock(), adapter=Mock())

        control_mock = Mock()
        env._control_server = control_mock

        set_simulation_running(env)
        env._process_cycle(0.5)

        control_mock.assert_has_calls([call.process()])

    def test_None_control_server_is_None(self):
        env = Simulation(device=Mock(), adapter=Mock(), control_server=None)

        self.assertIsNone(env.control_server)

    def test_invalid_control_server_fails(self):
        self.assertRaises(Exception, Simulation,
                          device=Mock(), adapter=Mock(), control_server=5.0)
        self.assertRaises(Exception, Simulation,
                          device=Mock(), adapter=Mock(), control_server=3434)

        # With an arbitrary object it should also fail
        self.assertRaises(Exception, Simulation,
                          device=Mock(), adapter=Mock(), control_server=Mock())

        # The string must have two components separated by :
        self.assertRaises(Exception, Simulation,
                          device=Mock(), adapter=Mock(), control_server='a:b:c')

    @patch('lewis.core.simulation.ExposedObject')
    @patch('lewis.core.simulation.ControlServer')
    def test_construct_control_server(self, mock_control_server_type, exposed_object_mock):
        device = Mock()
        adapter = Mock()

        exposed_object_mock.return_value = 'test'
        assertRaisesNothing(self, Simulation, device=device, adapter=adapter,
                            control_server='localhost:10000')

        mock_control_server_type.assert_called_once_with(
            {'device': device, 'simulation': 'test'},
            'localhost:10000')

    def test_start_starts_control_server(self):
        env = Simulation(device=Mock(), adapter=Mock())

        control_server_mock = Mock()
        env._control_server = control_server_mock

        def process_cycle_side_effect(delta):
            env.stop()

        env._process_cycle = Mock(side_effect=process_cycle_side_effect)
        env.start()

        control_server_mock.assert_has_calls([call.start_server()])

    def test_speed_range(self):
        env = Simulation(device=Mock(), adapter=Mock())

        assertRaisesNothing(self, setattr, env, 'speed', 3.0)
        self.assertEqual(env.speed, 3.0)

        assertRaisesNothing(self, setattr, env, 'speed', 0.1)
        self.assertEqual(env.speed, 0.1)

        assertRaisesNothing(self, setattr, env, 'speed', 0.0)
        self.assertEqual(env.speed, 0.0)

        self.assertRaises(ValueError, setattr, env, 'speed', -0.5)

    def test_cycle_delay_range(self):
        env = Simulation(device=Mock(), adapter=Mock())

        assertRaisesNothing(self, setattr, env, 'cycle_delay', 0.2)
        self.assertEqual(env.cycle_delay, 0.2)

        assertRaisesNothing(self, setattr, env, 'cycle_delay', 2.0)
        self.assertEqual(env.cycle_delay, 2.0)

        assertRaisesNothing(self, setattr, env, 'cycle_delay', 0.0)
        self.assertEqual(env.cycle_delay, 0.0)

        self.assertRaises(ValueError, setattr, env, 'cycle_delay', -4)

    def test_start_stop(self):
        env = Simulation(device=Mock(), adapter=Mock())

        with patch.object(env, '_process_cycle', side_effect=lambda x: env.stop()) as mock_cycle:
            env.start()

            mock_cycle.assert_has_calls([call(0.0)])

    @patch('lewis.core.simulation.ExposedObject')
    @patch('lewis.core.simulation.ControlServer')
    def test_control_server_setter(self, control_server_mock, exposed_object_mock):
        # The return value (= instance of ControlServer) must be specified
        control_server_mock.return_value = Mock()
        exposed_object_mock.return_value = 'test'
        device_mock = Mock()

        env = Simulation(device=device_mock, adapter=Mock())

        assertRaisesNothing(self, setattr, env, 'control_server', '127.0.0.1:10001')
        control_server_mock.assert_called_once_with(
            {'device': device_mock, 'simulation': 'test'}, '127.0.0.1:10001')

        control_server_mock.reset_mock()

        assertRaisesNothing(self, setattr, env, 'control_server', None)
        self.assertIsNone(env.control_server)

        set_simulation_running(env)

        # Can set new control server even when simulation is running:
        assertRaisesNothing(self, setattr, env, 'control_server', '127.0.0.1:10002')

        # The server is started automatically when the simulation is running
        control_server_mock.assert_called_once_with(
            {'device': device_mock, 'simulation': 'test'}, '127.0.0.1:10002')

        # The instance must have one call to start_server
        control_server_mock.return_value.assert_has_calls([call.start_server()])

        # Can not replace control server when simulation is running
        self.assertRaises(RuntimeError, setattr, env, 'control_server', '127.0.0.1:10003')

    def test_connect_disconnect_exceptions(self):
        env = Simulation(device=Mock(), adapter=Mock())

        self.assertTrue(env.device_connected)

        assertRaisesNothing(self, env.disconnect_device)
        self.assertFalse(env.device_connected)
        self.assertRaises(RuntimeError, env.disconnect_device)

        assertRaisesNothing(self, env.connect_device)
        self.assertTrue(env.device_connected)
        self.assertRaises(RuntimeError, env.connect_device)

    @patch('lewis.core.simulation.sleep')
    def test_disconnect_device(self, sleep_mock):
        adapter_mock = Mock()
        env = Simulation(device=Mock(), adapter=adapter_mock)

        # connected device calls adapter_mock
        env._process_cycle(0.5)
        adapter_mock.assert_has_calls([call.handle(env.cycle_delay)])
        sleep_mock.assert_not_called()

        adapter_mock.reset_mock()
        sleep_mock.reset_mock()

        # disconnected device calls sleep_mock
        env.disconnect_device()
        env._process_cycle(0.5)

        sleep_mock.assert_has_calls([call.handle(env.cycle_delay)])
        adapter_mock.assert_not_called()

        adapter_mock.reset_mock()
        sleep_mock.reset_mock()

        # re-connecting returns to previous behavior
        env.connect_device()
        env._process_cycle(0.5)
        adapter_mock.assert_has_calls([call.handle(env.cycle_delay)])
        sleep_mock.assert_not_called()

    def test_device_documentation_returns_adapter_documentation(self):
        adapter_mock = Mock()
        adapter_mock.documentation = 'test'

        env = Simulation(device=Mock(), adapter=adapter_mock)
        doc = env.device_documentation

        self.assertEqual(doc, 'test')
