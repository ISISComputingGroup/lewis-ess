import zmq
import json
from jsonrpc import JSONRPCResponseManager


class RPCObject(object):
    def __init__(self, object, methods=()):
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
        :param methods: If supplied, only this list of methods will be exposed.
        """
        self._object = object
        self._method_map = {}

        exposed_method = methods if methods else [prop for prop in dir(self._object) if not prop.startswith('_')]

        for method in exposed_method:
            self._add_method_wrappers(method)

    def _add_method_wrappers(self, member):
        """
        This method probes the supplied member of the wrapped object and inserts an appropriate
        entry into the internal method map. Getters and setters for properties get a suffix
        ':get' and ':set' respectively.

        :param member: The member of the wrapped object to expose
        """
        method_object = getattr(self._object, member)

        if callable(method_object):
            self._method_map[member] = method_object
        else:
            def getter():
                return getattr(self._object, member)

            self._method_map['{}:get'.format(member)] = getter

            def setter(arg):
                return setattr(self._object, member, arg)

            self._method_map['{}:set'.format(member)] = setter

    def get_api(self):
        """
        This method returns the class name and a list of exposed methods. It is exposed to RPC-clients by an
        instance of RPCObjectCollection.

        :return: A dictionary describing the exposed API (consisting of a class name and methods).
        """
        return {'class': type(self._object).__name__, 'methods': list(self._method_map.keys())}

    def __getitem__(self, item):
        return self._method_map[item]

    def __len__(self):
        return len(self._method_map)

    def __iter__(self):
        return iter(self._method_map)


class RPCObjectCollection(object):
    def __init__(self, objects):
        self._object_map = {}
        self._method_map = {}

        for name, obj in objects.items():
            self.add_object(obj, name)

        self._method_map[':objects'] = self.get_objects

    def add_object(self, obj, name):
        if name in self._object_map:
            raise RuntimeError('An object is already registered under that name.')

        exposed_object = self._object_map[name] = obj if isinstance(obj, RPCObject) else RPCObject(obj)

        for method_name in exposed_object:
            self._method_map[name + '.' + method_name] = exposed_object[method_name]
            self._method_map[name + ':api'] = exposed_object.get_api

    def get_objects(self):
        return list(self._object_map.keys())

    def __getitem__(self, item):
        return self._method_map[item]

    def __len__(self):
        return len(self._method_map)

    def __iter__(self):
        return iter(self._method_map)


class ZMQJSONRPCServer(object):
    def __init__(self, object_map={}, host='127.0.0.1', port='10000'):
        super(ZMQJSONRPCServer, self).__init__()
        self.host = host
        self.port = port

        self._rpc_object_collection = RPCObjectCollection(object_map)

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
        try:
            request = self.socket.recv_unicode(flags=zmq.NOBLOCK)

            try:
                response = JSONRPCResponseManager.handle(request, self._rpc_object_collection)
                self.socket.send_unicode(response.json)
            except TypeError as e:
                self.socket.send_json(self._unhandled_exception_response(json.loads(request)['id'], e))
        except zmq.Again:
            pass
