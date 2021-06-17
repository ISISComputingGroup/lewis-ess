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

from collections import OrderedDict

from lewis.adapters.stream import Cmd, StreamInterface, Var
from lewis.core.statemachine import State
from lewis.devices import StateMachineDevice
from datetime import datetime


class VerySimpleStateDeviceWithEvents(StateMachineDevice):
    param = 10

    def _initialize_data(self):
        self.connected = False

        self.send_update_after = 10  # seconds
        self.send_update_time_remainig = self.send_update_after
        self.send_updates_enabled = False

    def do_send_updates_enable(self):
        self.send_updates_enabled = True
        return f"ALIVE messages will start within {self.send_update_after}"

    def do_send_updates_disable(self):
        self.send_updates_enabled = False
        return f"ALIVE messages will stop ------------------------------"

    def do_send_updates_enable_value(self, state):
        self.send_updates_enabled = state
        return None

    def _get_state_handlers(self):
        return {"disconnected": State(), "connected": State()}

    def _get_initial_state(self):
        return "disconnected"

    def _get_transition_handlers(self):
        return OrderedDict(
            [
                (("disconnected", "connected"), lambda: self.connected),
                (("connected", "disconnected"), lambda: not self.connected),
            ]
        )

    def event_handler(self, message):
        """Publishes a message to all listening stream clients

        Args:
            message ([str]): an event
        """
        self.stream_event_message(message)

    def process(self, dt):

        # Simple scheduled event , determine when to send a periodic message
        self.send_update_time_remainig -= dt
        if self.send_update_time_remainig <= 0:
            if self.send_updates_enabled:
                self.event_handler(f"ALIVE:{datetime.now().isoformat()}")
            # reset the periodic timer
            self.send_update_time_remainig = self.send_update_after
        return super().process(dt=dt)


class VerySimpleStateDeviceWithEventsInterface1(StreamInterface):
    """
    A very simple device with TCP-stream interface that events and publishes a welcome message on connect

    The device has only one parameter, which can be set to an arbitrary
    value through this interface, The interface consists of the following commands which can be invoked via telnet.


            to use this simulated device with lewis-control  to manual send unsolicited responses/simulated events

            `lewis -r localhost:10000 -k lewis.examples simple_state_eventing_device\r\n"

            in a seperate terminal

            `lewis-control -r localhost:10000 device event_handler test`


    To connect:

        $ telnet host port

    After that, typing either of the commands and pressing enter sends them to the server.

    The commands are:

     - ``V``: Returns the parameter as part of a verbose message.
     - ``V=something``: Sets the parameter to ``something``.
     - ``P``: Returns the device parameter unmodified.
     - ``P=something``: Exactly the same as ``V=something``.
     - ``R`` or ``r``: Returns the number 4.
     - ``START`` start regularly sending ALIVE messages regularly default 10s
     - ``STOP`` stop sending ALIVE messages

     - ``HELP`` Displays valid commands commands

    """

    commands = {
        Cmd("get_param", pattern="^V$", return_mapping="The value is {}".format),
        Cmd("set_param", pattern="^V=(.+)$", argument_mappings=(int,)),
        Cmd(
            "show_help",
            pattern="^HELP$",
        ),
        Cmd(
            "do_send_updates_enable",
            pattern="^START$",
        ),
        Cmd(
            "do_send_updates_disable",
            pattern="^STOP$",
        ),
        Var(
            "param",
            read_pattern="^P$",
            write_pattern="^P=(.+)$",
            doc="One of the only parameters.",
        ),
        Cmd(lambda: 4, pattern="^R$(?i)", doc='"Random" number (4).'),
    }

    in_terminator = "\r\n"
    out_terminator = "\r\n"

    readtimeout = 60000  # ms  https://lewis.readthedocs.io/en/latest/api/adapters/stream.html?highlight=readtimeout#lewis.adapters.stream.StreamInterface

    # TODO: Timeout handler

    def initial_message(self):
        return (
            "r\n\r\nWelcome to the Simple Eventing Device\r\n\r\n"
            "     use  HELP to display the commands available\r\n"
        )

    def show_help(self):
        """Returns the valid commands and other notes"""
        return self.__doc__.replace("\n", "\r\n")

    def get_param(self):
        """Returns the device parameter."""
        return self.device.param

    def set_param(self, new_param):
        """Set the device parameter, does not return anything."""
        self.device.param = new_param

    def handle_error(self, request, error):
        return "An error occurred: " + repr(error)


setups = dict(
    disconnected=dict(
        device_type=VerySimpleStateDeviceWithEvents,
        parameters=dict(
            # override_initial_state="disconnected",
            override_initial_data=dict(param=20),
        ),
    )
)
