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

from mock import Mock, patch

from lewis.core.statemachine import (
    State,
    StateMachine,
    StateMachineException,
    Transition,
)


class TestStateMachine(unittest.TestCase):
    def test_initial_state_is_required(self):
        with self.assertRaises(StateMachineException) as context:
            StateMachine({})

        self.assertTrue("must include 'initial'" in str(context.exception))

    def test_state_machine_starts_in_None(self):
        sm = StateMachine({"initial": "foobar"})
        self.assertIsNone(sm.state, "StateMachine should start in the 'None' non-state")

    def test_first_cycle_transitions_to_initial(self):
        sm = StateMachine({"initial": "foobar"})
        sm.process(0.1)
        self.assertEqual(
            sm.state,
            "foobar",
            "StateMachine failed to transition into " "initial state on first cycle",
        )

    def test_can_transition_with_lambda(self):
        sm = StateMachine(
            {"initial": "foo", "transitions": {("foo", "bar"): lambda: True}}
        )

        self.assertIsNone(sm.state)
        sm.process(0.1)
        self.assertEqual(sm.state, "foo")
        sm.process(0.2)
        self.assertEqual(sm.state, "bar")

    def test_can_transition_with_callable(self):
        transition = Mock(return_value=True)
        sm = StateMachine(
            {"initial": "foo", "transitions": {("foo", "bar"): transition}}
        )

        transition.assert_not_called()
        self.assertIsNone(sm.state)
        sm.process(0.1)
        transition.assert_not_called()
        self.assertEqual(sm.state, "foo")
        sm.process(0.2)
        self.assertTrue(transition.called)
        self.assertEqual(sm.state, "bar")

    @patch.object(Transition, "__call__", return_value=True)
    def test_can_transition_with_Transition(self, tr_call):
        transition = Transition()
        sm = StateMachine(
            {"initial": "foo", "transitions": {("foo", "bar"): transition}}
        )

        tr_call.assert_not_called()
        self.assertIsNone(sm.state)
        sm.process(0.1)
        tr_call.assert_not_called()
        self.assertEqual(sm.state, "foo")
        sm.process(0.2)
        self.assertTrue(tr_call.called)
        self.assertEqual(sm.state, "bar")

    def test_Transition_receives_Context(self):
        transition = Transition()
        context = object()
        StateMachine(
            {"initial": "foo", "transitions": {("foo", "bar"): transition}},
            context=context,
        )

        self.assertEqual(transition._context, context)

    def test_can_specify_state_handlers_as_dict(self):
        on_entry = Mock()
        in_state = Mock()
        on_exit = Mock()
        sm = StateMachine(
            {
                "initial": "foo",
                "states": {
                    "foo": {
                        "on_entry": on_entry,
                        "in_state": in_state,
                        "on_exit": on_exit,
                    },
                },
                "transitions": {("foo", "bar"): lambda: True},
            }
        )

        # First cycle enters and executes initial state, but forces delta T to zero
        sm.process(1.0)
        on_entry.assert_called_once_with(0)
        in_state.assert_called_once_with(0)

        on_entry.reset_mock()
        in_state.reset_mock()

        # Second cycle transitions due to lambda: True above
        sm.process(2.0)
        on_exit.assert_called_once_with(2.0)

        on_exit.reset_mock()

        # Third cycle only does an in_state in bar, shouldn't affect foo
        sm.process(3.0)
        on_entry.assert_not_called()
        in_state.assert_not_called()
        on_exit.assert_not_called()

    def test_can_specify_state_handlers_as_list(self):
        on_entry = Mock()
        in_state = Mock()
        on_exit = Mock()
        sm = StateMachine(
            {
                "initial": "foo",
                "states": {
                    "foo": [on_entry, in_state, on_exit],
                },
                "transitions": {("foo", "bar"): lambda: True},
            }
        )

        # First cycle enters and executes initial state, but forces delta T to zero
        sm.process(1.0)
        on_entry.assert_called_once_with(0)
        in_state.assert_called_once_with(0)

        on_entry.reset_mock()
        in_state.reset_mock()

        # Second cycle transitions due to lambda: True above
        sm.process(2.0)
        on_exit.assert_called_once_with(2.0)

        on_exit.reset_mock()

        # Third cycle only does an in_state in bar, shouldn't affect foo
        sm.process(3.0)
        on_entry.assert_not_called()
        in_state.assert_not_called()
        on_exit.assert_not_called()

    @patch.object(State, "on_entry")
    @patch.object(State, "in_state")
    @patch.object(State, "on_exit")
    def test_can_specify_state_handlers_as_State(self, *_):
        foo = State()
        bar = State()
        sm = StateMachine(
            {
                "initial": "foo",
                "states": {
                    "foo": foo,
                    "bar": bar,
                },
                "transitions": {("foo", "bar"): lambda: True},
            }
        )

        # First cycle enters and executes initial state, but forces delta T to zero
        sm.process(1.0)
        foo.on_entry.assert_called_once_with(0)
        foo.in_state.assert_called_once_with(0)

        foo.on_entry.reset_mock()
        foo.in_state.reset_mock()

        # Second cycle transitions due to lambda: True above
        sm.process(2.0)
        foo.on_exit.assert_called_once_with(2.0)
        bar.on_entry.assert_called_once_with(2.0)
        bar.in_state.assert_called_once_with(2.0)

        foo.on_exit.reset_mock()
        bar.on_entry.reset_mock()
        bar.in_state.reset_mock()

        # Third cycle only does an in_state in bar
        sm.process(3.0)
        bar.in_state.assert_called_once_with(3.0)
        bar.on_entry.assert_not_called()
        bar.on_exit.assert_not_called()

    def test_State_receives_Context(self):
        state = State()
        context = object()
        StateMachine({"initial": "foo", "states": {"foo": state}}, context=context)

        self.assertEqual(state._context, context)

    def test_bind_handlers_by_name_default_behaviour(self):
        target = Mock()
        sm = StateMachine(
            {"initial": "foo", "transitions": {("foo", "bar"): lambda: True}}
        )
        sm.bind_handlers_by_name(target)

        # First cycle enters and executes initial state, but forces delta T to zero
        sm.process(1.0)
        target._on_entry_foo.assert_called_once_with(0)
        target._in_state_foo.assert_called_once_with(0)

        target._on_entry_foo.reset_mock()
        target._in_state_foo.reset_mock()

        # Second cycle transitions due to lambda: True above
        sm.process(2.0)
        target._on_exit_foo.assert_called_once_with(2.0)
        target._on_entry_bar.assert_called_once_with(2.0)
        target._in_state_bar.assert_called_once_with(2.0)

        target._on_exit_foo.reset_mock()
        target._on_entry_bar.reset_mock()
        target._in_state_bar.reset_mock()

        # Third cycle only does an in_state in bar
        sm.process(3.0)
        target._in_state_bar.assert_called_once_with(3.0)
        target._on_entry_bar.assert_not_called()
        target._on_exit_bar.assert_not_called()

    def test_bind_handlers_by_name_custom_prefix(self):
        target = Mock()
        sm = StateMachine(
            {"initial": "foo", "transitions": {("foo", "bar"): lambda: True}}
        )
        sm.bind_handlers_by_name(
            target,
            prefix={
                "on_entry": "enter_",
                "in_state": "do_",
                "on_exit": "exit_",
            },
        )

        # First cycle enters and executes initial state, but forces delta T to zero
        sm.process(1.0)
        target.enter_foo.assert_called_once_with(0)
        target.do_foo.assert_called_once_with(0)

        target.enter_foo.reset_mock()
        target.do_foo.reset_mock()

        # Second cycle transitions due to lambda: True above
        sm.process(2.0)
        target.exit_foo.assert_called_once_with(2.0)
        target.enter_bar.assert_called_once_with(2.0)
        target.do_bar.assert_called_once_with(2.0)

        target.exit_foo.reset_mock()
        target.enter_bar.reset_mock()
        target.do_bar.reset_mock()

        # Third cycle only does an in_state in bar
        sm.process(3.0)
        target.do_bar.assert_called_once_with(3.0)
        target.enter_bar.assert_not_called()
        target.exit_bar.assert_not_called()

    def test_bind_handlers_by_name_override(self):
        # first target will accept any event call
        first = Mock()

        # second target will 'override' the events for bar
        second = Mock(spec=["_on_entry_bar", "_in_state_bar", "_on_exit_bar"])

        sm = StateMachine(
            {"initial": "foo", "transitions": {("foo", "bar"): lambda: True}}
        )
        sm.bind_handlers_by_name(first)
        sm.bind_handlers_by_name(second, override=True)

        # First cycle enters and executes initial state, but forces delta T to zero
        sm.process(1.0)
        first._on_entry_foo.assert_called_once_with(0)
        first._in_state_foo.assert_called_once_with(0)

        first._on_entry_foo.reset_mock()
        first._in_state_foo.reset_mock()

        # Second cycle transitions due to lambda: True above
        sm.process(2.0)
        first._on_exit_foo.assert_called_once_with(2.0)
        second._on_entry_bar.assert_called_once_with(2.0)
        second._in_state_bar.assert_called_once_with(2.0)

        first._on_exit_foo.reset_mock()
        second._on_entry_bar.reset_mock()
        second._in_state_bar.reset_mock()

        # Third cycle only does an in_state in bar
        sm.process(3.0)
        second._in_state_bar.assert_called_once_with(3.0)
        second._on_entry_bar.assert_not_called()
        second._on_exit_bar.assert_not_called()

        # 'bar' events should not have been called on 'first'
        first._on_entry_bar.assert_not_called()
        first._in_state_bar.assert_not_called()
        first._on_exit_bar.assert_not_called()

    def test_reset(self):
        sm = StateMachine(
            {"initial": "foo", "transitions": {("foo", "bar"): lambda: True}}
        )

        self.assertIsNone(sm.state)
        sm.reset()
        self.assertIsNone(sm.state)

        sm.process(0.1)
        self.assertEqual(sm.state, "foo")
        sm.reset()
        self.assertIsNone(sm.state)

        sm.process(0.2)
        sm.process(0.3)
        self.assertEqual(sm.state, "bar")
        sm.reset()
        self.assertIsNone(sm.state)

    def test_can(self):
        sm = StateMachine(
            {
                "initial": "init",
                "transitions": {
                    ("init", "foo"): lambda: True,
                    ("foo", "bar"): lambda: True,
                    ("bar", "foo"): lambda: True,
                    ("bar", "init"): lambda: True,
                    ("bar", "bar"): lambda: True,
                },
            }
        )

        self.assertEqual(sm.state, None)
        self.assertIs(sm.can("init"), True)
        self.assertIs(sm.can("foo"), False)
        self.assertIs(sm.can("bar"), False)
        self.assertIs(sm.can(None), False)

        sm.process()
        self.assertEqual(sm.state, "init")
        self.assertIs(sm.can("foo"), True)
        self.assertIs(sm.can("bar"), False)
        self.assertIs(sm.can("init"), False)

        sm.process()
        self.assertEqual(sm.state, "foo")
        self.assertIs(sm.can("bar"), True)
        self.assertIs(sm.can("init"), False)
        self.assertIs(sm.can("foo"), False)

        sm.process()
        self.assertEqual(sm.state, "bar")
        self.assertIs(sm.can("foo"), True)
        self.assertIs(sm.can("init"), True)
        self.assertIs(sm.can("bar"), True)
