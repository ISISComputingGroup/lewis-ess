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

from collections import OrderedDict

from lewis.adapters.stream import Cmd, StreamInterface, regex, scanf
from lewis.core import approaches
from lewis.core.statemachine import State
from lewis.devices import StateMachineDevice


class DefaultMovingState(State):
    def in_state(self, dt):
        old_position = self._context.position
        self._context.position = approaches.linear(
            old_position, self._context.target, self._context.speed, dt
        )
        self.log.info(
            "Moved position (%s -> %s), target=%s, speed=%s",
            old_position,
            self._context.position,
            self._context.target,
            self._context.speed,
        )


class SimulatedExampleMotor(StateMachineDevice):
    def _initialize_data(self):
        self.position = 0.0
        self._target = 0.0
        self.speed = 2.0

    def _get_state_handlers(self):
        return {"idle": State(), "moving": DefaultMovingState()}

    def _get_initial_state(self):
        return "idle"

    def _get_transition_handlers(self):
        return OrderedDict(
            [
                (("idle", "moving"), lambda: self.position != self.target),
                (("moving", "idle"), lambda: self.position == self.target),
            ]
        )

    @property
    def state(self):
        return self._csm.state

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, new_target):
        if self.state == "moving":
            raise RuntimeError("Can not set new target while moving.")

        if not (0 <= new_target <= 250):
            raise ValueError("Target is out of range [0, 250]")

        self._target = new_target

    def stop(self):
        """Stops the motor and returns the new target and position, which are equal"""

        self._target = self.position

        self.log.info("Stopping movement after user request.")

        return self.target, self.position


class ExampleMotorStreamInterface(StreamInterface):
    """
    TCP-stream based example motor interface

    This motor simulation can be controlled via telnet:

        $ telnet host port

    Where the host and port-parameter are part of the dynamically created documentation for
    a concrete device instance.

    The motor starts moving immediately when a new target position is set. Once it's moving,
    it has to be stopped to receive a new target, otherwise an error is generated.
    """

    commands = {
        Cmd("get_status", regex(r"^S\?$")),  # explicit regex
        Cmd("get_position", r"^P\?$"),  # implicit regex
        Cmd("get_target", r"^T\?$"),
        Cmd("set_target", scanf("T=%f")),  # scanf format specification
        Cmd("stop", r"^H$", return_mapping=lambda x: "T={},P={}".format(x[0], x[1])),
    }

    in_terminator = "\r\n"
    out_terminator = "\r\n"

    def get_status(self):
        """Returns the status of the device, which is one of 'idle' or 'moving'."""
        return self.device.state

    def get_position(self):
        """Returns the current position in mm."""
        return self.device.position

    def get_target(self):
        """Returns the current target in mm."""
        return self.device.target

    def set_target(self, new_target):
        """
        Sets the new target in mm, the movement starts immediately. If the value is outside
        the interval [0, 250] or the motor is already moving, an error is returned, otherwise
        the new target is returned."""
        try:
            self.device.target = new_target
            return "T={}".format(new_target)
        except RuntimeError:
            return "err: not idle"
        except ValueError:
            return "err: not 0<=T<=250"


setups = dict(
    moving=dict(
        device_type=SimulatedExampleMotor,
        parameters=dict(
            override_initial_state="moving",
            override_initial_data=dict(_target=120.0, position=20.0),
        ),
    )
)
