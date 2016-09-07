import zmq
import json
from jsonrpc import JSONRPCResponseManager


class RPCObject(object):
    def __init__(self, object, object_name, methods=()):
        self.name = object_name
        self._object = object
        self._object_members = dir(self._object)

        self._method_map = {}

        if not methods:
            methods = [prop for prop in self._object_members if not prop.startswith('_')]

        for method in methods:
            func_specs = self._create_method_wrappers(method)

            for name, func in func_specs:
                self._method_map[name] = func

        self._method_map[':api'] = self.get_api

    def _create_method_wrappers(self, method):
        method_object = getattr(self._object, method)

        func_specs = []

        if not callable(method_object):
            def getter():
                return getattr(self._object, method)

            func_specs.append(('{}:get'.format(method), getter,))

            def setter(arg):
                return setattr(self._object, method, arg)

            func_specs.append(('{}:set'.format(method), setter,))
        else:
            def method_wrapper(*args, **kwargs):
                return getattr(self._object, method)(*args, **kwargs)

            func_specs.append((method, method_wrapper,))

        return func_specs

    def get_api(self):
        return {'name': self.name, 'class': type(self._object).__name__, 'methods': list(self._method_map.keys())}

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

        for obj in objects:
            self.add_object(obj)

        self._method_map[':objects'] = self.get_objects

    @staticmethod
    def create(plain_object_specs):
        wrapped_objects = [RPCObject(obj, name) for obj, name in plain_object_specs]

        return RPCObjectCollection(wrapped_objects)

    def add_object(self, obj):
        if isinstance(obj, RPCObject):
            self._object_map[obj.name] = obj

            for method_name in obj:
                glue = '.' if not method_name.startswith(':') else ''
                self._method_map[obj.name + glue + method_name] = obj[method_name]

    def get_objects(self):
        return list(self._object_map.keys())

    def __getitem__(self, item):
        return self._method_map[item]

    def __len__(self):
        return len(self._method_map)

    def __iter__(self):
        return iter(self._method_map)


class ZMQJSONRPCServer(object):
    def __init__(self, rpc_object, host='127.0.0.1', port='10000'):
        super(ZMQJSONRPCServer, self).__init__()
        self.host = host
        self.port = port

        if isinstance(rpc_object, RPCObjectCollection):
            self.rpc_object = rpc_object
        else:
            self.rpc_object = RPCObjectCollection.create(rpc_object)

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        uri = 'tcp://{0}:{1}'.format(self.host, self.port)
        self.socket.bind(uri)

    def unhandled_exception_response(self, id, exception):
        return {"jsonrpc": "2.0", "id": id,
                "error": {"message": "Server error",
                          "code": -32000,
                          "data": {"message": exception.message,
                                   "args": [exception.message],
                                   "type": type(exception).__name__}
                          }
                }

    def process(self):
        try:
            request = self.socket.recv_unicode(flags=zmq.NOBLOCK)
            print('Got request: ', request)

            try:
                response = JSONRPCResponseManager.handle(request, self.rpc_object)
                print('Sending response: ', response.json)
                self.socket.send_unicode(response.json)
            except TypeError as e:
                self.socket.send_json(self.unhandled_exception_response(json.loads(request)['id'], e))
        except zmq.Again:
            pass
