#!/usr/bin/env python
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

import zmq
import json
from jsonrpc import JSONRPCResponseManager


class ExposedObject(object):
    def __init__(self, object, members=None):
        """
        RPCObject is a class that makes it easy to expose an object via the JSONRPCResponseManager
        from the json-rpc package, where it can serve as a dispatcher. For this purpose it exposes
        a read-only dict-like interface.

        The basic problem solved by this wrapper is that plain data members of an object are not
        really captured well by the RPC-approach, where a client performs function calls on a
        remote machine and gets the result back.

        The supplied object is inspected using dir(object) and all entries that do not start
        with a _ are exposed in a way that depends on whether the corresponding member
        is a method or a property (either in the Python-sense or the general OO-sense). Methods
        are stored directly, and stored in an internal dict where the method name is the key and the
        callable method object is the value. For properties, a getter- and a setter function
        are generated, which are then stored in the same dict. The names of these methods for
        a property called 'a' are 'a:get' and 'a:set'. The separator has been chosen to be
        colon because it can't be part of a valid Python identifier.

        If the second argument is not empty, it is interpreted to be the list of members
        to expose and only those are actually exposed. This can be used to explicitly expose
        members of an object that start with an underscore.

        :param object: The object to expose.
        :param members: If supplied, only this list of methods will be exposed.
        """
        super(ExposedObject, self).__init__()

        self._object = object
        self._function_map = {}

        self._add_function(':api', self.get_api)

        exposed_members = members if members else [prop for prop in dir(self._object) if not prop.startswith('_')]

        for method in exposed_members:
            self._add_member_wrappers(method)

    def _add_member_wrappers(self, member):
        """
        This method probes the supplied member of the wrapped object and inserts an appropriate
        entry into the internal method map. Getters and setters for properties get a suffix
        ':get' and ':set' respectively.

        :param member: The member of the wrapped object to expose
        """
        method_object = getattr(self._object, member)

        if callable(method_object):
            self._add_function(member, method_object)
        else:
            self._add_function('{}:get'.format(member), lambda: getattr(self._object, member))

            def setter(arg):
                return setattr(self._object, member, arg)

            self._add_function('{}:set'.format(member), setter)

    def get_api(self):
        """
        This method returns the class name and a list of exposed methods. It is exposed to RPC-clients by an
        instance of ExposedObjectCollection.

        :return: A dictionary describing the exposed API (consisting of a class name and methods).
        """
        return {'class': type(self._object).__name__, 'methods': list(self._function_map.keys())}

    def __getitem__(self, item):
        return self._function_map[item]

    def __len__(self):
        return len(self._function_map)

    def __iter__(self):
        return iter(self._function_map)

    def __contains__(self, item):
        return item in self._function_map

    def _add_function(self, name, function):
        if not callable(function):
            raise TypeError('Only callable objects can be exposed.')

        self._function_map[name] = function


class ExposedObjectCollection(ExposedObject):
    def __init__(self, named_objects):
        """
        This class helps expose a number of objects (plain or RPCObject) by exposing the methods of each object as

            name.method

        Furthermore it exposes each object's API as a method with the following name:

            name:api

        A list of exposed objects can be obtained by calling the following method from the client:

            :objects

        :param named_objects: Dictionary of of name: object pairs.
        """
        super(ExposedObjectCollection, self).__init__(self, ('get_objects',))
        self._object_map = {}

        if named_objects:
            for name, obj in named_objects.items():
                self.add_object(obj, name)

        self._add_function('get_objects', self.get_objects)

    def add_object(self, obj, name):
        if name in self._object_map:
            raise RuntimeError('An object is already registered under that name.')

        exposed_object = self._object_map[name] = obj if isinstance(obj, ExposedObject) else ExposedObject(obj)

        for method_name in exposed_object:
            glue = '.' if not method_name.startswith(':') else ''
            self._add_function(name + glue + method_name, exposed_object[method_name])

    def get_objects(self):
        return list(self._object_map.keys())


class ZMQJSONRPCServer(object):
    def __init__(self, object_map=None, host='127.0.0.1', port='10000'):
        """
        This server opens a ZMQ REP-socket at the given host and port. It constructs an ExposedObjectCollection
        from the supplied name: object-dictionary and uses that as a handler for JSON-RPC requests. If it is an
        instance of ExposedObject, that is used directly.

        Each time process is called, the server tries to get request data and responds to that. If there is
        no data, the method does nothing.

        Please note that this RPC-service comes without any security, authentication, etc. Only use it
        to expose objects on a trusted network and be aware that anyone on that network can access
        the exposed objects without any restrictions.

        :param object_map: Dictionary with name: object-pairs to construct an ExposedObjectCollection or ExposedObject
        :param host: Host on which the RPC service listens. Default is 127.0.0.1.
        :param port: Port on which the RPC service listes.
        """
        super(ZMQJSONRPCServer, self).__init__()
        self.host = host
        self.port = port

        if isinstance(object_map, ExposedObject):
            self._rpc_object_collection = object_map
        else:
            self._rpc_object_collection = ExposedObjectCollection(object_map)

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        uri = 'tcp://{0}:{1}'.format(self.host, self.port)
        self.socket.bind(uri)

    def _unhandled_exception_response(self, id, exception):
        return {"jsonrpc": "2.0", "id": id,
                "error": {"message": "Server error",
                          "code": -32000,
                          "data": {"message": exception.args,
                                   "args": [exception.args],
                                   "type": type(exception).__name__}}}

    def process(self):
        """
        Each time this method is called, the socket tries to retrieve data and passes
        it to the JSONRPCResponseManager, which in turn passes the RPC to the ExposedObjectCollection.

        In case no data are available, the method does nothing. This behavior is required for
        Plankton where everything is running in one thread. The central loop can call process
        at some point to process remote calls, so the RPC-server does not introduce its own
        infinite processing loop.
        """
        try:
            request = self.socket.recv_unicode(flags=zmq.NOBLOCK)

            try:
                response = JSONRPCResponseManager.handle(request, self._rpc_object_collection)
                self.socket.send_unicode(response.json)
            except TypeError as e:
                self.socket.send_json(self._unhandled_exception_response(json.loads(request)['id'], e))
        except zmq.Again:
            pass
