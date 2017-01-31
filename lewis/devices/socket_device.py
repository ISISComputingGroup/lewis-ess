# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2017 European Spallation Source ERIC
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

from lewis.devices import StateMachineDevice
from lewis.core.statemachine import State, HasContext
from lewis.core.processor import CanProcess

import socket


class DisconnectedState(State):
    def on_entry(self, dt):
        self._retries = 0
        self._since_last = 0.0

    def in_state(self, dt):
        self._since_last += dt
        if self._retries == 0 or self._since_last > self._context.retry_wait:
            try:
                self._context.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                host, port = self._context.connection_string.split(':')
                self._context.sock.connect((host, int(port)))
                self._context.sock.settimeout(self._context.timeout)
            except socket.error as err:
                self._context.sock = None
                self._retries += 1
                self._since_last = 0.0

        if self._retries >= self._context.max_retries:
            self._context.error = 'Connection failure.'


class ConnectedState(State):
    def _req_rep(self, request):
        try:
            if self._context.sock is not None:
                self.log.info('Sending request: %r', request)

                self._context.sock.sendall(request + self._context.out_terminator)
                reply = self._context.sock.recv(1024)

                self.log.info('Got reply: %r', reply)

                return reply
        except socket.timeout:
            pass
        except socket.error:
            self._close_connection()

        return None

    def _close_connection(self):
        if self._context.sock is not None:
            self._context.sock.close()
            self._context.sock = None

    def on_entry(self, dt):
        if hasattr(self._context, 'on_connected'):
            self._context.on_connected()

    def in_state(self, dt):
        if self._context._write_queue:
            self.log.info('Processing write queue.')

            while self._context._write_queue:
                self._req_rep(self._context._write_queue.pop())

            self._context.poll()

        if self._context._read_queue:
            for member, query, conversion in self._context._read_queue:
                new_value = self._req_rep(query)

                if new_value:
                    try:
                        setattr(self._context, member, conversion(new_value))
                    except RuntimeError:
                        self._close_connection()

            self._context._read_queue.clear()


class PollTimer(HasContext, CanProcess):
    def __init__(self, context):
        super(PollTimer, self).__init__()
        self.set_context(context)

    def doProcess(self, dt):
        self._context.last_polled += dt

        if self._context.last_polled > self._context.poll_interval:
            self._context.poll()


class SocketDevice(StateMachineDevice):
    """
    SocketDevice is a device that does not contain a simulation, but logic to connect
    to a TCP-stream based device. Nevertheless it is based on
    :class:`~plankton.devices.StateMachineDevice`, its state machine has only three states:

        - ``disconnected``: No connection to the device has been established.
        - ``connected``: A connection to the device has been established, communication with the
          device is performed.
        - ``error``: The connection to the device has been interrupted.

    The device has a few members that are required for it to function correctly:

        - ``connection_string``: A string with the format ``host:port``. The device should be
          reachable at this address.
        - ``retry_wait``: After the connection has been broken, the device tries to reconnect in
          intervals given by this member (in seconds). The default is 10.
        - ``max_retries``: The number of retries before the device goes from the ``disconnected``
          to the ``error`` state.
        - ``poll_interval``: An interval in seconds that determines how often :meth:`~poll` is
          called.

    The device starts in the ``disconnected`` state and tries to connect, transitioning to the
    ``connected``-state if successful. When that state is entered and the device has an
    ``on_connected``-method, it is called.

    In the ``connected`` state, two "queues" are checked in each iteration, one
    for reading and one for writing. These are filled by calling :meth:`update` and :meth:`write`
    respectively, the write queue is processed first. If writes are processed, :meth:`poll` is
    called, which fills the read-queue, to make sure the device state is updated properly
    in case the write had an influence.

    The use case which lead to this device type is writing an ad-hoc EPICS IOC that exposes a
    TCP-stream device.
    """
    sock = None

    connection_string = ''
    poll_interval = 5.0
    last_polled = poll_interval + 0.1
    retry_wait = 10.0
    max_retries = 3
    timeout = 0.1
    error = None

    _write_queue = []
    _read_queue = set()

    poll_map = {}

    in_terminator = '\r\n'
    out_terminator = '\r\n'

    def __init__(self, override_states=None, override_transitions=None,
                 override_initial_state=None, override_initial_data=None):
        super(SocketDevice, self).__init__(override_states, override_transitions,
                                           override_initial_state, override_initial_data)

        self.add_processor(PollTimer(self))

    def _get_state_handlers(self):
        return {
            'disconnected': DisconnectedState(),
            'connected': ConnectedState(),
            'error': State()
        }

    def _get_initial_state(self):
        return 'disconnected'

    def _get_transition_handlers(self):
        return {
            ('disconnected', 'connected'): lambda: self.sock is not None,
            ('connected', 'disconnected'): lambda: self.sock is None,
            ('disconnected', 'error'): lambda: self.error is not None,
            ('error', 'disconnected'): lambda: self.error is None
        }

    @property
    def error_message(self):
        """The current error message or an empty string if no error."""
        return self.error or ''

    def reset(self):
        """Resets the current error."""
        self.error = None

    def write(self, command):
        """
        Queues the command for submission to the device via the connected socket. The specified
        ``out_terminator`` is appended to the command. Typical usage would be in property setters,
        for example:

        .. sourcecode:: Python

            class SomeDevice(SocketDevice):
                @property
                def example(self):
                    return self._example

                @example.setter
                def example(self, new_value):
                    self.write('DEVICE SPECIFIC COMMAND {}'.format(new_value))

        :param command: Command to be submitted to the device.
        """
        self._write_queue.append(command)

    def update(self, member, command, conversion=float):
        """
        This methods updates the specified member using the return value which is obtained
        as a response from submitting ``command`` (including ``out_terminator``) to the device.
        The return value is transformed by a conversion function that is ``float`` by default.

        Normally it's not necessary to call this method directly, since the :meth;`poll`-method
        will take care of updating members according to the ``poll_map``.

        :param member: Device member to update.
        :param command: Command for obtaining the new value from device.
        :param conversion: Conversion function, default is ``float``.
        """
        self._read_queue.add((member, command, conversion))

    def poll(self):
        """
        The poll method takes the ``poll_map`` dict and iterates through it. The keys are expected
        to be members of the object, the values should be tuples containing the device specific
        command required to obtain the new value and optionally a conversion function.
        """
        if len(self._read_queue) == 0:
            for member, query in self.poll_map.items():
                self.update(member, *query)

            self.last_polled = 0.0
