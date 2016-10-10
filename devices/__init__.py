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
        super(StateMachineDevice, self).__init__()

        self._initialize_data()
        self._override_data(override_initial_data)

        self._csm = StateMachine({
            'initial': self._get_initial_state() if override_initial_state is None else override_initial_state,
            'states': self._get_final_state_handlers(override_states),
            'transitions': self._get_final_transition_handlers(override_transitions)
        }, context=self)

        self.addProcessor(self._csm)

    def _get_state_handlers(self):
        raise NotImplementedError('_get_state_handlers must be implemented in a StateMachineDevice.')

    def _get_initial_state(self):
        raise NotImplementedError('_get_initial_state must be implemented in a StateMachineDevice.')

    def _get_transition_handlers(self):
        raise NotImplementedError('_get_transition_handlers must be implemented in a StateMachineDevice.')

    def _initialize_data(self):
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
