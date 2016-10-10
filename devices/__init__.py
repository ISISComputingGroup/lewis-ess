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

from __future__ import absolute_import
import importlib
from core import CanProcess, CanProcessComposite, StateMachine
from core.utils import dict_strict_update


class Device(CanProcess):
    """
    This class exists mainly for consistency. It is meant to implement very simple devices that
    do not require a state machine for their simulation. For such devices, all that is required
    is subclassing from `Device` and possibly implementing `doProcess`, but this is optional.

    StateMachineDevice offers more functionality and is more likely to be useful for implementing
    simulations of real devices.
    """


class StateMachineDevice(CanProcessComposite):
    def __init__(self, override_states=None, override_transitions=None, override_initial_state=None,
                 override_initial_data=None):
        """
        This class is intended to be sub-classed to implement devices using a finite state machine
        internally.

        Implementing such a device is straightforward, there are three methods that *must* be overriden:

            `_get_state_handlers`
            `_get_initial_state`
            `_get_transition_handlers`

        The first method is supposed to return a dictionary with state handlers for each state
        of the state machine, the second method must return the name of the initial state.
        The third method must return a dict-like object (often an OrderedDict from collections)
        that defines the conditions for transitions between the states of the state machine.

        They are implemented as methods and not as plain class member variables, because often
        they use the `self`-variable, which does not exist at the class level.

        From these three methods, a `StateMachine`-instance is constructed, it's available as
        the device's `_csm`-member. CSM is short for "cycle-based state machine".

        Most device implementation will also want to override this method:

            `_initialize_data`

        This method should initialise device state variables (such as temperature, speed, etc.). Having
        this in a separate method from `__init__` has the advantage that it can be used to reset those
        variables at a later stage, without having to write the same code again.

        Following this scheme, inheriting from `StateMachineDevice` also provides the possibility
        for users of the class to override the states, the transitions, the initial state and
        even the data. For states, transitions and data, dicts need to be passed to the constructor,
        for the initial state that should be a string.

        All these overrides can be used to define device setups to describe certain scenarios more easily.

        :param override_states: Dict with one entry per state. Only states defined in the state machine are allowed.
        :param override_transitions: Dict with (state, state) tuples as keys and callables as values.
        :param override_initial_state: The initial state.
        :param override_initial_data: A dict that contains data members that should be overwritten on construction.
        """
        super(StateMachineDevice, self).__init__()

        self._initialize_data()
        self._override_data(override_initial_data)

        state_handlers = self._get_final_state_handlers(override_states)
        initial = self._get_initial_state() if override_initial_state is None else override_initial_state

        if not initial in state_handlers:
            raise RuntimeError('Initial state \'{}\' is not a valid state.'.format(initial))

        self._csm = StateMachine({
            'initial': initial,
            'states': state_handlers,
            'transitions': self._get_final_transition_handlers(override_transitions)
        }, context=self)

        self.addProcessor(self._csm)

    def _get_state_handlers(self):
        """
        Implement this method to return a dict-like object with state handlers (see core.statemachine.State) for each
        state of the state machine. The default implementation raises a NotImplementedError.

        :return: A dict-like object containing named state handlers.
        """
        raise NotImplementedError('_get_state_handlers must be implemented in a StateMachineDevice.')

    def _get_initial_state(self):
        """
        Implement this method to return the initial state of the internal state machine. The default implementation
        raises a NotImplementedError.

        :return: The initial state of the state machine.
        """
        raise NotImplementedError('_get_initial_state must be implemented in a StateMachineDevice.')

    def _get_transition_handlers(self):
        """
        Implement this method to return transition handlers for the internal state machine. The keys should be
        (state, state)-tuples and the values functions that return true if the transition should be triggered.

        :return: A dict-like object containing transition handlers.
        """
        raise NotImplementedError('_get_transition_handlers must be implemented in a StateMachineDevice.')

    def _initialize_data(self):
        """
        Implement this method to initialize data members of the device, such as temperature, speed and others. It gets
        called first in the __init__-method.
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
                if not name in dir(self):
                    raise AttributeError('Can not override non-existing attribute \'{}\' of class \'{}\'.'.format(
                        name, type(self).__name__))

                setattr(self, name, val)


def import_device(device, setup=None, device_package='devices'):
    """
    This function tries to load a given device with a given setup from the package specified
    in the device_package parameter. First it checks if there is a module

        device_package.device.setups.setup

    and tries to import two members from that module `device_type` and `parameters`. The former
    must be the device class and the latter the parameters that are passed to the class' constructor.
    The above mentioned module might look like this:

        from ..device import SomeDeviceClass as device_type

        parameters = dict(device_param1='some_value', device_param2=3.4)

    This allows for a large degree of freedom for specifying setups. If that is not required,
    and the setup does not exist in that sub-module of the device, this function checks for a dictionary
    named `setups` directly in the device module (device_package.device). So the device_package.device.__init__.py
    could contain something like this:

        from .device import SomeDeviceClass

        setups = dict(
                     default=dict(
                         device_type=SomeDeviceClass,
                         parameters=dict(device_param1='some_value', device_param2=3.4)
                     )
                 )

    If that also fails, but no setup was specified in the function's arguments, the function will try to return
    the first sub-class of `CanProcess` that it finds in the device module. That means in the simplest case,
    the __init__.py only needs to declare a class that can be instantiated without parameters.

    If all of that fails, an exception is raised.

    Otherwise, a device type and the parameter-dict for object instantiation are returned.

    :param device: Device to load.
    :param setup: Setup to load, 'default' will be loaded if parameter is None.
    :param device_package: Name of the package where devices are defined.
    :return: Device type and parameter dict.
    """
    setup_name = setup if setup is not None else 'default'

    try:
        setup_module = importlib.import_module('{}.{}.{}.{}'.format(device_package, device, 'setups', setup_name))
        device_type = getattr(setup_module, 'device_type')
        parameters = getattr(setup_module, 'parameters')

        return device_type, parameters
    except (ImportError, AttributeError):
        try:
            device_module = importlib.import_module('{}.{}'.format(device_package, device))

            try:
                setups = getattr(device_module, 'setups')

                device_type = setups[setup_name]['device_type']
                parameters = setups[setup_name].get('parameters', {})

                return device_type, parameters
            except (AttributeError, KeyError):
                if setup_name == 'default':
                    for member_name in dir(device_module):
                        try:
                            member_object = getattr(device_module, member_name)
                            if issubclass(member_object,
                                          CanProcess) and not member_object.__module__ == 'core.processor':
                                return member_object, dict()
                        except TypeError:
                            pass
                raise

        except (ImportError, AttributeError, KeyError):
            raise RuntimeError('Could not find setup \'{}\' for device \'{}\'.'.format(setup_name, device))
