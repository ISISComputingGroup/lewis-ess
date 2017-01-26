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

import asynchat
import asyncore
import inspect
import re
import socket
from argparse import ArgumentParser

from six import b

from lewis.adapters import Adapter
from lewis.core.logging import has_log
from lewis.core.utils import format_doc_text


@has_log
class StreamHandler(asynchat.async_chat):
    def __init__(self, sock, target, stream_server):
        asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator(b(target.in_terminator))
        self.target = target
        self.buffer = []

        self._stream_server = stream_server

        self._set_logging_context(target)
        self.log.info('Client connected from %s:%s', *sock.getpeername())

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        request = b''.join(self.buffer)
        self.buffer = []

        self.log.debug('Got request %s', request)

        try:
            cmd = next((cmd for cmd in self.target.bound_commands if cmd.can_process(request)),
                       None)

            if cmd is None:
                raise RuntimeError('None of the device\'s commands matched.')

            self.log.info('Processing request %s using command %s', request, cmd.raw_pattern)

            reply = cmd.process_request(request)

        except Exception as error:
            reply = self.target.handle_error(request, error)
            self.log.debug('Error while processing request', exc_info=error)

        if reply is not None:
            self.log.debug('Sending reply %s', reply)
            self.push(b(reply + self.target.out_terminator))

    def handle_close(self):
        self.log.info('Closing connection to client %s:%s', *self.socket.getpeername())
        self._stream_server.remove_handler(self)
        asynchat.async_chat.handle_close(self)


@has_log
class StreamServer(asyncore.dispatcher):
    def __init__(self, host, port, target):
        asyncore.dispatcher.__init__(self)
        self.target = target
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

        self._set_logging_context(target)
        self.log.info('Listening on %s:%s', host, port)

        self._accepted_connections = []

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            handler = StreamHandler(sock, self.target, self)

            self._accepted_connections.append(handler)

    def remove_handler(self, handler):
        self._accepted_connections.remove(handler)

    def close(self):
        # As this is an old style class, the base class method must
        # be called directly. This is important to still perform all
        # the teardown-work that asyncore.dispatcher does.
        self.log.info('Shutting down server, closing all remaining client connections.')
        asyncore.dispatcher.close(self)

        # But in addition, close all open sockets and clear the connection list.
        for handler in self._accepted_connections:
            handler.close()

        self._accepted_connections = []


class Func(object):
    """
    Objects of this type connect a callable object to a regular expression. The regular expression
    must define one group (with the use of parentheses) for each argument of the callable.

    In general, Func-objects should not be created directly, instead they are created by one of
    the sub-classes of :class:`CommandBase` using :meth:`~CommandBase.bind`.

    Function arguments are indicated by groups in the regular expression. The number of
    groups has to match the number of arguments of the function. In earlier versions of Lewis it
    was possible to pass flags to ``re.compile``, this has been removed for consistency issues
    in :class:`Var`. It is however still possible to use the exact same flags as part of the
    regular expression. In the documentation of re_, this is outlined, simply add a group to the
    expression that contains the flags, for example ``(?i)`` to make the expression case
    insensitive. This special group does not count towards the matching groups used for argument
    capture.

    The optional argument_mappings can be an iterable of callables with one parameter of the
    same length as the number of arguments of the function. The first parameter will be
    transformed using the first function, the second using the second function and so on.
    This can be useful to automatically transform strings provided by the adapter into a proper
    data type such as ``int`` or ``float`` before they are passed to the function.

    The return_mapping argument is similar, it should map the return value of the function
    to a string. The default map function only does that when the supplied value
    is not None. It can also be set to a numeric value or a string constant so that the
    command always returns the same value. If it is ``None``, the return value is not
    modified at all.

    Finally, documentation can be provided by passing the doc-argument. If it is omitted,
    the docstring of the bound function is used and if that is not present, left empty.

    :param func: Function to be called when pattern matches or member of device/interface.
    :param pattern: Regex to match for function call.
    :param argument_mappings: Iterable with mapping functions from string to some type.
    :param return_mapping: Mapping function for return value of method.
    :param doc: Description of the command. If not supplied, the docstring is used.

    .. _re: https://docs.python.org/2/library/re.html#regular-expression-syntax
    """

    def __init__(self, func, pattern, argument_mappings=None, return_mapping=None, doc=None):
        if not callable(func):
            raise RuntimeError('Can not construct a Func-object from a non callable object.')

        self.func = func
        self.raw_pattern = pattern
        self.pattern = re.compile(b(pattern), 0) if pattern else None

        try:
            inspect.getcallargs(func, *[None] * self.pattern.groups)
        except TypeError:
            raise RuntimeError(
                'The number of arguments for function \'{}\' matched by pattern '
                '\'{}\' is not compatible with number of defined '
                'groups in pattern ({}).'.format(func.__name__, pattern, self.pattern.groups))

        if argument_mappings is not None and (self.pattern.groups != len(argument_mappings)):
            raise RuntimeError(
                'Supplied argument mappings for function matched by pattern \'{}\' specify {} '
                'argument(s), but the function has {} arguments.'.format(
                    self.pattern, len(argument_mappings), self.pattern.groups))

        self.argument_mappings = argument_mappings
        self.return_mapping = return_mapping
        self.doc = doc or (inspect.getdoc(self.func) if callable(self.func) else None)

    def can_process(self, request):
        return self.pattern.match(request) is not None

    def process_request(self, request):
        match = self.pattern.match(request)

        if not match:
            raise RuntimeError('Request can not be processed.')

        args = self.map_arguments(match.groups())

        return self.map_return_value(self.func(*args))

    def map_arguments(self, arguments):
        """
        Returns the mapped function arguments. If no mapping functions are defined, the arguments
        are returned as they were supplied.

        :param arguments: List of arguments for bound function as strings.
        :return: Mapped arguments.
        """
        if self.argument_mappings is None:
            return arguments

        return [f(a) for f, a in zip(self.argument_mappings, arguments)]

    def map_return_value(self, return_value):
        """
        Returns the mapped return_value of a processed request. If no return_mapping has been
        defined, the value is returned as is. If return_mapping is a static value, that value
        is returned, ignoring return_value completely.

        :param return_value: Value to map.
        :return: Mapped return value.
        """
        if callable(self.return_mapping):
            return self.return_mapping(return_value)

        if self.return_mapping is not None:
            return self.return_mapping

        return return_value


class CommandBase(object):
    """
    This is the common base class of :class:`Cmd` and :class:`Var`. The concept of commands for
    the stream adapter is based on connecting a callable object to a pattern that matches an
    inbound request.

    For free function and lambda expressions this is straightforward: the function object can
    simply be stored together with the regular expression. Most often however, the callable
    is a method of the device or interface object - these do not exist when the commands are
    defined.

    This problem is solved by introducing a "bind"-step in :class:`StreamAdapter`. So instead
    of a function object, both :class:`Cmd` and :class:`Var` store the name of a member of device
    or interface. At "bind-time", this is translated into the correct callable.

    So instead of using :class:`Cmd` or :class:`Var` directly, both classes' :meth:`bind`-methods
    return an iterable of :class:`Func`-objects which can be used for processing requests.
    :class:`StreamAdapter` performs this bind-step when it's constructed. For details regarding
    the implementations, please see the corresponding classes.

    .. seealso::

        Please take a look at :class:`Cmd` for exposing callable objects or methods of
        device/interface and :class:`Var` for exposing attributes and properties.

        To see how argument_mappings, return_mapping and doc are applied, please look at
        :class:`Func`.

    :param func: Function to be called when pattern matches or member of device/interface.
    :param pattern: Regex to match for function call.
    :param argument_mappings: Iterable with mapping functions from string to some type.
    :param return_mapping: Mapping function for return value of method.
    :param doc: Description of the command. If not supplied, the docstring is used.
    """

    def __init__(self, func, pattern, argument_mappings=None, return_mapping=None, doc=None):
        super(CommandBase, self).__init__()

        self.func = func
        self.pattern = pattern
        self.argument_mappings = argument_mappings
        self.return_mapping = return_mapping
        self.doc = doc

    def bind(self, target):
        raise NotImplementedError('Binders need to implement the bind method.')


class Cmd(CommandBase):
    """
    This class is an implementation of :class:`CommandBase` that can expose a callable object
    or a named method of the device/interface controlled by :class:`StreamAdapter`.

    .. sourcecode:: Python

        def random():
            return 6

        SomeInterface(StreamAdapter):
            commands = {
                Cmd(lambda: 4, pattern='^R$', doc='Returns a random number.'),
                Cmd('random', pattern='^RR$', doc='Better random number.'),
                Cmd(random, pattern='^RRR$', doc='The best random number.'),
            }

            def random(self):
                return 5

    The interface defined by the above example has three commands, ``R`` which calls a lambda
    function that always returns 4, ``RR``, which calls ``SomeInterface.random`` and returns 5 and
    lastly ``RRR`` which calls the free function defined above and returns the best random number.

    For a detailed explanation of requirements to the constructor arguments, please refer to the
    documentation of :class:`Func`, to which the arguments are forwarded.

    .. seealso ::

        :class:`Var` exposes attributes and properties of a device object. The documentation
        of :class:`Func` provides more information about the common constructor arguments.

    :param func: Function to be called when pattern matches or member of device/interface.
    :param pattern: Regex to match for function call.
    :param argument_mappings: Iterable with mapping functions from string to some type.
    :param return_mapping: Mapping function for return value of method.
    :param doc: Description of the command. If not supplied, the docstring is used.
    """

    def __init__(self, func, pattern, argument_mappings=None,
                 return_mapping=lambda x: None if x is None else str(x), doc=None):
        super(Cmd, self).__init__(func, pattern, argument_mappings, return_mapping,
                                  doc)

    def bind(self, target):
        method = self.func if callable(self.func) else getattr(target, self.func, None)

        if method is None:
            return None

        return [Func(method, self.pattern, self.argument_mappings, self.return_mapping,
                     self.doc)]


class Var(CommandBase):
    """
    With this implementation of :class:`CommandBase` it's possible to expose plain data attributes
    or properties of device or interface. Getting and setting a value are separate procedures
    which both have their own pattern, read_pattern and write_pattern to match a command each.
    Please note that write_pattern has to have exactly one group defined to match a parameter.

    Due to this separation, parameters can be made read-only, write-only or read-write in the
    interface:

    .. sourcecode:: Python

        class SomeInterface(StreamAdapter):
            commands = {
                Var('foo', read_pattern='^F$', write_pattern=r'^F=(\d+)$',
                    argument_mappings=(int,), doc='An integer attribute.'),
                Var('bar' read_pattern='^B$')
            }

            foo = 10

            @property
            def bar(self):
                return self.foo + 5

            @bar.setter
            def bar(self, new_bar):
                self.foo = new_bar - 5

    In the above example, the foo attribute can be read and written, it's automatically converted
    to an integer, while bar is a property that can only be read via the stream protocol.

    .. seealso::

        For exposing methods and free functions, there's the :class:`Cmd`-class.

    :param target_member: Attribute or property of device/interface to expose.
    :param read_pattern: Regex that matches command for property getter.
    :param write_pattern: Regex that matches command for property setter.
    :param argument_mappings: Iterable with mapping functions from string to some type,
                              only applied to setter.
    :param return_mapping: Mapping function for return value of method,
                           applied to getter and setter.
    :param doc: Description of the command. If not supplied, the docstring is used. For plain data
                attributes the only way to get docs is to supply this argument.
    """

    def __init__(self, target_member, read_pattern=None, write_pattern=None,
                 argument_mappings=None, return_mapping=lambda x: None if x is None else str(x),
                 doc=None):
        super(Var, self).__init__(target_member, None, argument_mappings, return_mapping, doc)

        self.target = None

        self.read_pattern = read_pattern
        self.write_pattern = write_pattern

    def bind(self, target):
        if self.func not in dir(target):
            return None

        funcs = []

        if self.read_pattern is not None:
            def getter():
                return getattr(target, self.func)

            if inspect.isdatadescriptor(getattr(type(target), self.func)):
                getter.__doc__ = 'Getter: ' + inspect.getdoc(getattr(type(target), self.func))

            funcs.append(
                Func(getter, self.read_pattern, return_mapping=self.return_mapping, doc=self.doc))

        if self.write_pattern is not None:
            def setter(new_value):
                setattr(target, self.func, new_value)

            if inspect.isdatadescriptor(getattr(type(target), self.func)):
                setter.__doc__ = 'Setter: ' + inspect.getdoc(getattr(type(target), self.func))

            funcs.append(
                Func(setter, self.write_pattern, argument_mappings=self.argument_mappings,
                     return_mapping=self.return_mapping, doc=self.doc))

        return funcs


class StreamAdapter(Adapter):
    """
    This class is used to provide a TCP-stream based interface to a device.

    Many hardware devices use a protocol that is based on exchanging text with a client via
    a TCP stream. Sometimes RS232-based devices are also exposed this way via an adapter-box.
    This adapter makes it easy to mimic such a protocol, in a subclass only three members must
    be overridden:

     - in_terminator, out_terminator: These define how lines are terminated when transferred
       to and from the device respectively. They are stripped/added automatically.
       The default is ``\\r``.
     - commands: A list of :class:`~CommandBase`-objects that define mappings between protocol
       and device/interface methods/attributes.

    Commands are expressed as regular expressions, a simple example may look like this:

    .. sourcecode:: Python

        class SimpleDeviceStreamInterface(StreamAdapter):
            commands = [
                Cmd('set_speed', r'^S=([0-9]+)$', argument_mappings=[int]),
                Cmd('get_speed', r'^S\\?$')
                Var('speed', read_pattern=r'^V\\?$', write_pattern=r'^V=([0-9]+)$')
            ]

            def set_speed(self, new_speed):
                self._device.speed = new_speed

            def get_speed(self):
                return self._device.speed

    The interface has two commands, ``S?`` to return the speed and ``S=10`` to set the speed
    to an integer value.

    As in the :class:`lewis.adapters.epics.EpicsAdapter`, it does not matter whether the
    wrapped method is a part of the device or of the interface, this is handled automatically.

    In addition, the :meth:`handle_error`-method can be overridden. It is called when an exception
    is raised while handling commands.

    :param device: The exposed device.
    :param arguments: Command line arguments.
    """
    protocol = 'stream'

    in_terminator = '\r'
    out_terminator = '\r'

    commands = None

    def __init__(self, device, arguments=None):
        super(StreamAdapter, self).__init__(device, arguments)

        self._options = self._parse_arguments(arguments or [])

        if self._options.telnet_mode:
            self.in_terminator = '\r\n'
            self.out_terminator = '\r\n'

        self._server = None

        self.bound_commands = self._bind_commands(self.commands)

    @property
    def documentation(self):

        commands = ['{}:\n{}'.format(
            cmd.raw_pattern,
            format_doc_text(cmd.doc or inspect.getdoc(cmd.func) or ''))
                    for cmd in sorted(self.bound_commands, key=lambda x: x.raw_pattern)]

        options = format_doc_text(
            'Listening on: {}\nPort: {}\nRequest terminator: {}\nReply terminator: {}'.format(
                self._options.bind_address, self._options.port,
                repr(self.in_terminator), repr(self.out_terminator)))

        return '\n\n'.join(
            [inspect.getdoc(self) or '',
             'Parameters\n==========', options, 'Commands\n========'] + commands)

    def start_server(self):
        """
        Starts the TCP stream server, binding to the configured host and port.
        Host and port are configured via the command line arguments.

        .. note:: The server does not process requests unless
                  :meth:`handle` is called in regular intervals.

        """
        if self._server is None:
            self._server = StreamServer(self._options.bind_address, self._options.port, self)

    def stop_server(self):
        if self._server is not None:
            self._server.close()
            self._server = None

    @property
    def is_running(self):
        return self._server is not None

    def _parse_arguments(self, arguments):
        parser = ArgumentParser(description='Adapter to expose a device via TCP Stream')
        parser.add_argument('-b', '--bind-address', default='0.0.0.0',
                            help='IP Address to bind and listen for connections on')
        parser.add_argument('-p', '--port', type=int, default=9999,
                            help='Port to listen for connections on')
        parser.add_argument('-t', '--telnet-mode', action='store_true',
                            help='Override terminators to be telnet compatible')
        return parser.parse_args(arguments)

    def _bind_commands(self, cmds):
        patterns = set()

        bound_commands = []

        for cmd in cmds:
            bound = cmd.bind(self) or cmd.bind(self._device) or None

            if bound is None:
                raise RuntimeError(
                    'Unable to produce callable object for non-existing member \'{}\' '
                    'of device or interface.'.format(cmd.member))

            for bound_cmd in bound:
                if bound_cmd.pattern in patterns:
                    raise RuntimeError(
                        'The regular expression {} is '
                        'associated with multiple commands.'.format(bound_cmd.pattern.pattern))

                patterns.add(bound_cmd.pattern)

                bound_commands.append(bound_cmd)

        return bound_commands

    def handle_error(self, request, error):
        """
        Override this method to handle exceptions that are raised during command processing.
        The default implementation does nothing, so that any errors are silently ignored.

        :param request: The request that resulted in the error.
        :param error: The exception that was raised.
        """
        pass

    def handle(self, cycle_delay=0.1):
        """
        Spend approximately ``cycle_delay`` seconds to process requests to the server.

        :param cycle_delay: S
        """
        asyncore.loop(cycle_delay, count=1)
