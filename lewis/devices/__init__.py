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

"""
This module contains base classes for devices. Inherit from :class:`Device` for simple devices
or from :class:`StateMachineDevice` for devices that are more complex and can be described
using a state machine.
"""

from lewis.core.devices import DeviceBase
from lewis.core.processor import CanProcess, CanProcessComposite
from lewis.core.statemachine import StateMachine
from lewis.core.utils import dict_strict_update


class Device(DeviceBase, CanProcess):
    """
    This class exists mainly for consistency. It is meant to implement very simple devices that
    do not require a state machine for their simulation. For such devices, all that is required
    is subclassing from `Device` and possibly implementing `doProcess`, but this is optional.

    StateMachineDevice offers more functionality and is more likely to be useful for implementing
    simulations of real devices.
    """

    def __init__(self):
        super(Device, self).__init__()


class StateMachineDevice(DeviceBase, CanProcessComposite):
    """
    This class is intended to be sub-classed to implement devices using a finite state machine
    internally.

    Implementing such a device is straightforward, there are three methods
    that *must* be overridden:

        - :meth:`_get_state_handlers`
        - :meth:`_get_initial_state`
        - :meth:`_get_transition_handlers`

    The first method is supposed to return a dictionary with state handlers for each state
    of the state machine, the second method must return the name of the initial state.
    The third method must return a dict-like object (often an OrderedDict from collections)
    that defines the conditions for transitions between the states of the state machine.

    They are implemented as methods and not as plain class member variables, because often
    they use the `self`-variable, which does not exist at the class level.

    From these three methods, a :class:`~lewis.core.statemachine.StateMachine`-instance is
    constructed, it's available as the device's ``_csm``-member. CSM is short for
    "cycle-based state machine".

    Most device implementation will also want to override this method:

        - :meth:`_initialize_data`

    This method should initialise device state variables (such as temperature, speed, etc.).
    Having this in a separate method from ``__init__`` has the advantage that it can be used
    to reset those variables at a later stage, without having to write the same code again.

    Following this scheme, inheriting from StateMachineDevice also provides the possibility
    for users of the class to override the states, the transitions, the initial state and
    even the data. For states, transitions and data, dicts need to be passed to the
    constructor, for the initial state that should be a string.

    All these overrides can be used to define device setups to describe certain scenarios
    more easily.

    :param override_states: Dict with one entry per state. Only states defined in the state
                            machine are allowed.
    :param override_transitions: Dict with (state, state) tuples as keys and
                                 callables as values.
    :param override_initial_state: The initial state.
    :param override_initial_data: A dict that contains data members
                                  that should be overwritten on construction.
    """

    def __init__(
        self,
        override_states=None,
        override_transitions=None,
        override_initial_state=None,
        override_initial_data=None,
    ):
        super(StateMachineDevice, self).__init__()

        self.log.info("Creating device, setting up state machine")

        self._initialize_data()
        self._override_data(override_initial_data)

        state_handlers = self._get_final_state_handlers(override_states)
        initial = override_initial_state or self._get_initial_state()

        if initial not in state_handlers:
            raise RuntimeError(
                "Initial state '{}' is not a valid state.".format(initial)
            )

        self._csm = StateMachine(
            {
                "initial": initial,
                "states": state_handlers,
                "transitions": self._get_final_transition_handlers(
                    override_transitions
                ),
            },
            context=self,
        )

        self.add_processor(self._csm)

    def _get_state_handlers(self):
        """
        Implement this method to return a dict-like object with state handlers
        (see :class:`~lewis.core.statemachine.State`) for each state of the state machine.
        The default implementation raises a ``NotImplementedError``.

        :return: A dict-like object containing named state handlers.
        """
        raise NotImplementedError(
            "_get_state_handlers must be implemented in a StateMachineDevice."
        )

    def _get_initial_state(self):
        """
        Implement this method to return the initial state of the internal state machine.
        The default implementation raises a ``NotImplementedError``.

        :return: The initial state of the state machine.
        """
        raise NotImplementedError(
            "_get_initial_state must be implemented in a StateMachineDevice."
        )

    def _get_transition_handlers(self):
        """
        Implement this method to return transition handlers for the internal state machine.
        The keys should be (state, state)-tuples and the values functions that return true
        if the transition should be triggered. The default implementation raises a
        ``NotImplementedError``.

        :return: A dict-like object containing transition handlers.
        """
        raise NotImplementedError(
            "_get_transition_handlers must be implemented in a StateMachineDevice."
        )

    def _initialize_data(self):
        """
        Implement this method to initialize data members of the device, such as temperature,
        speed and others. It gets called first in the __init__-method. The default implementation
        does nothing.
        """
        pass

    def _get_final_state_handlers(self, overrides):
        states = self._get_state_handlers()

        if overrides is not None:
            dict_strict_update(states, overrides)

        return states

    def _get_final_transition_handlers(self, overrides):
        transitions = self._get_transition_handlers()

        if overrides is not None:
            dict_strict_update(transitions, overrides)

        return transitions

    def _override_data(self, overrides):
        """
        This method overrides data members of the class, but does not allow for adding new members.

        :param overrides: Dict with data overrides.
        """
        if overrides is not None:
            for name, val in overrides.items():
                self.log.debug("Trying to override initial data (%s=%s)", name, val)
                if name not in dir(self):
                    raise AttributeError(
                        "Can not override non-existing attribute"
                        "'{}' of class '{}'.".format(name, type(self).__name__)
                    )

                setattr(self, name, val)
