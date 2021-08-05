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
This module contains classes to expose objects via a JSON-RPC over ZMQ server. Lewis uses
this infrastructure in :class:`~lewis.core.simulation.Simulation`.

.. seealso::

    Client classes for the service defined in this module can be found in
    :mod:`~lewis.core.control_client`.

"""

import inspect
import json
import socket

import zmq
from jsonrpc import JSONRPCResponseManager

from lewis.core.exceptions import LewisException
from lewis.core.logging import has_log


class ExposedObject:
    """
    ExposedObject is a class that makes it easy to expose an object via the
    JSONRPCResponseManager from the json-rpc package, where it can serve as a dispatcher.
    For this purpose it exposes a read-only dict-like interface.

    The basic problem solved by this wrapper is that plain data members of an object are not
    really captured well by the RPC-approach, where a client performs function calls on a
    remote machine and gets the result back.

    The supplied object is inspected using dir(object) and all entries that do not start
    with a _ are exposed in a way that depends on whether the corresponding member
    is a method or a property (either in the Python-sense or the general OO-sense). Methods
    are stored directly, and stored in an internal dict where the method name is the key and
    the callable method object is the value. For properties, a getter- and a setter function
    are generated, which are then stored in the same dict. The names of these methods for
    a property called ``a`` are ``a:get`` and ``a:set``. The separator has been chosen to be
    colon because it can't be part of a valid Python identifier.

    If the second argument is not empty, it is interpreted to be the list of members
    to expose and only those are actually exposed. This can be used to explicitly expose
    members of an object that start with an underscore. If all but one or two members
    should be exposed, it's also possible to use the exclude-argument to explicitly
    exclude a few members. Both parameters can be used in combination, the exclude-list
    takes precedence.

    In certain situations it is desirable to acquire a lock before accessing the exposed object,
    for example when multiple threads are accessing it on the server side. For this purpose,
    the ``lock``-parameter can be used. If it is not ``None``, the exposed methods are wrapped
    in a function that acquires the lock before accessing ``obj``, and releases it afterwards.

    :param obj: The object to expose.
    :param members: This list of methods will be exposed. (defaults to all public members)
    :param exclude: Members in this list will not be exposed.
    :param exclude_inherited: Should inherited members be excluded? (defaults to False)
    :param lock: ``threading.Lock`` that is used when accessing ``obj``.
    """

    def __init__(
        self, obj, members=None, exclude=None, exclude_inherited=False, lock=None
    ):
        super(ExposedObject, self).__init__()

        self._object = obj
        self._function_map = {}
        self._lock = lock

        self._add_function(":api", self.get_api)

        exposed_members = members if members else self._public_members()
        exclude = list(exclude or [])
        if exclude_inherited:
            for base in inspect.getmro(type(obj))[1:]:
                exclude += dir(base)

        for method in exposed_members:
            if method not in exclude:
                self._add_member_wrappers(method)

    def _public_members(self):
        """
        Returns a list of members that do not start with an underscore.
        """
        return [prop for prop in dir(self._object) if not prop.startswith("_")]

    def _add_member_wrappers(self, member):
        """
        This method probes the supplied member of the wrapped object and inserts an appropriate
        entry into the internal method map. Getters and setters for properties get a suffix
        ':get' and ':set' respectively.

        :param member: The member of the wrapped object to expose
        """
        method_object = getattr(type(self._object), member, None) or getattr(
            self._object, member
        )

        if callable(method_object):
            self._add_function(member, getattr(self._object, member))
        else:
            self._add_property(member)

    def get_api(self):
        """
        This method returns the class name and a list of exposed methods.
        It is exposed to RPC-clients by an instance of ExposedObjectCollection.

        :return: A dictionary describing the exposed API (consisting of a class name and methods).
        """
        return {
            "class": type(self._object).__name__,
            "methods": list(self._function_map.keys()),
        }

    def __getitem__(self, item):
        return self._function_map[item]

    def __len__(self):
        return len(self._function_map)

    def __iter__(self):
        return iter(self._function_map)

    def __contains__(self, item):
        return item in self._function_map

    def _add_property(self, name):
        self._add_function("{}:get".format(name), lambda: getattr(self._object, name))
        self._add_function(
            "{}:set".format(name), lambda value: setattr(self._object, name, value)
        )

    def _add_function(self, name, function):
        if not callable(function):
            raise TypeError("Only callable objects can be exposed.")

        if self._lock is not None:

            def create_locking_wrapper(f):
                def locking_wrapper_function(*args, **kwargs):
                    with self._lock:
                        return f(*args, **kwargs)

                return locking_wrapper_function

            function = create_locking_wrapper(function)

        self._function_map[name] = function

    def _remove_function(self, name):
        del self._function_map[name]


class ExposedObjectCollection(ExposedObject):
    """
    This class helps expose a number of objects (plain or RPCObject) by
    exposing the methods of each object as

    .. sourcecode:: Python

        name.method

    Furthermore it exposes each object's API as a method with the following name:

    .. sourcecode:: Python

        name:api

    A list of exposed objects can be obtained by calling the following method from the client:

    .. sourcecode:: Python

        :objects

    :param named_objects: Dictionary of of name: object pairs.
    """

    def __init__(self, named_objects):
        super(ExposedObjectCollection, self).__init__(self, ("get_objects",))
        self._object_map = {}

        if named_objects:
            for name, obj in named_objects.items():
                self.add_object(obj, name)

        self._add_function("get_objects", self.get_objects)

    def add_object(self, obj, name):
        """
        Adds the supplied object to the collection under the supplied name. If the name is already
        in use, a RuntimeError is raised. If the object is not an instance of
        :class:`ExposedObject`, the method automatically constructs one.

        :param obj: Object to add to the collection.
        :param name: Name of the exposed object.
        """
        if name in self._object_map:
            raise RuntimeError("An object is already registered under that name.")

        exposed_object = self._object_map[name] = (
            obj if isinstance(obj, ExposedObject) else ExposedObject(obj)
        )

        for method_name in exposed_object:
            glue = "." if not method_name.startswith(":") else ""
            self._add_function(name + glue + method_name, exposed_object[method_name])

    def remove_object(self, name):
        """
        Remove the object exposed under that name. If no object is registered under the supplied
        name, a RuntimeError is raised.

        :param name: Name of object to be removed.
        """
        if name not in self._object_map:
            raise RuntimeError("No object with name {} is registered.".format(name))

        for fn_name in list(self._function_map.keys()):
            if fn_name.startswith(name + ".") or fn_name.startswith(name + ":"):
                self._remove_function(fn_name)

        del self._object_map[name]

    def get_objects(self):
        """Returns the names of the exposed objects."""
        return list(self._object_map.keys())


@has_log
class ControlServer:
    """
    This server opens a ZMQ REP-socket at the given host and port when start_server
    is called.

    The server constructs an :class:`ExposedObjectCollection` from the supplied
    name: object-dictionary and uses that as a handler for JSON-RPC requests. If it is an
    instance of :class:`ExposedObject`, that is used directly.

    Each time process is called, the server tries to get request data and responds to that.
    If there is no data, the method does nothing.

    Please note that this RPC-service comes without any security, authentication, etc.
    Only use it to expose objects on a trusted network and be aware that anyone on that
    network can access the exposed objects without any restrictions.

    :param object_map: Dictionary with name: object-pairs to construct an
                       ExposedObjectCollection or ExposedObject
    :param connection_string: String with host:port pair for binding control server.
    """

    def __init__(self, object_map, connection_string):
        super(ControlServer, self).__init__()

        try:
            host, port = connection_string.split(":")
        except ValueError:
            raise LewisException(
                "'{}' is not a valid control server initialization string. "
                'A string of the form "host:port" is expected.'.format(
                    connection_string
                )
            )

        try:
            self.host = socket.gethostbyname(host)
        except socket.gaierror:
            raise LewisException(
                "Could not resolve control server host: {}".format(host)
            )

        self.port = port

        if isinstance(object_map, ExposedObject):
            self._exposed_object = object_map
        else:
            self._exposed_object = ExposedObjectCollection(object_map)

        self._socket = None

    @property
    def is_running(self):
        """
        This property is ``True`` if the server is running.
        """
        return self._socket is not None

    @property
    def exposed_object(self):
        """
        The exposed object. This is a read only property.
        """
        return self._exposed_object

    def start_server(self):
        """
        Binds the server to the configured host and port and starts listening.
        """
        if self._socket is None:
            context = zmq.Context()
            self._socket = context.socket(zmq.REP)
            self._socket.setsockopt(zmq.RCVTIMEO, 100)
            self._socket.bind("tcp://{0}:{1}".format(self.host, self.port))

            self.log.info("Listening on %s:%s", self.host, self.port)

    def _unhandled_exception_response(self, request_id, exception):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "message": "Server error",
                "code": -32000,
                "data": {
                    "message": exception.args,
                    "args": [exception.args],
                    "type": type(exception).__name__,
                },
            },
        }

    def process(self, blocking=False):
        """
        Each time this method is called, the socket tries to retrieve data and passes
        it to the JSONRPCResponseManager, which in turn passes the RPC to the
        ExposedObjectCollection.

        In case no data are available, the method does nothing. This behavior is required for
        Lewis where everything is running in one thread. The central loop can call process
        at some point to process remote calls, so the RPC-server does not introduce its own
        infinite processing loop.

        If the server has not been started yet (via :meth:`start_server`), a RuntimeError
        is raised.

        :param blocking: If True, this function will block until it has received data or a timeout
                         is triggered. Default is False to preserve behavior of prior versions.
        """
        if self._socket is None:
            raise RuntimeError(
                "The server has not been started yet, use start_server to do so."
            )

        try:
            request = self._socket.recv_unicode(
                flags=zmq.NOBLOCK if not blocking else 0
            )

            self.log.debug("Got request %s", request)

            try:
                response = JSONRPCResponseManager.handle(request, self._exposed_object)
                self._socket.send_unicode(response.json)

                self.log.debug("Sent response %s", response.json)
            except TypeError as e:
                self._socket.send_json(
                    self._unhandled_exception_response(json.loads(request)["id"], e)
                )
        except zmq.Again:
            pass
