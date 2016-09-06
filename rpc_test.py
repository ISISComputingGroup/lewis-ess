class Stuff(object):
    def __init__(self):
        self._a = 0
        self._b = (0, 0)

        self.g = 'test'

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        if value < 0:
            raise ValueError('No values < 0!')

        self._a = value

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, one):
        self._b = one

    @property
    def c(self):
        return self._a + self._b[0]

    def doIt(self):
        self._a = 42

    def doItNow(self, foo, bar=34):
        self._a = foo
        self._b = (self._b[0], bar)


class RPCObjectWrapper(object):
    def __init__(self, object, methods=()):
        self._object = object
        self._object_members = dir(self._object)

        self._method_map = {}

        if not methods:
            methods = [prop for prop in self._object_members if not prop.startswith('_')]

        for method in methods:
            func_specs = self._create_method_wrappers(method)

            for name, func in func_specs:
                self._method_map[name] = func

        self._method_map['.api'] = self.get_api

    def _create_method_wrappers(self, method):
        method_object = getattr(self._object, method)

        func_specs = []

        if not callable(method_object):
            def getter():
                return getattr(self._object, method)

            func_specs.append(('{}.get'.format(method), getter,))

            def setter(arg):
                return setattr(self._object, method, arg)

            func_specs.append(('{}.set'.format(method), setter,))
        else:
            def method_wrapper(*args, **kwargs):
                return getattr(self._object, method)(*args, **kwargs)

            func_specs.append((method, method_wrapper,))

        return func_specs

    def get_api(self):
        return {'class': type(self._object).__name__, 'methods': list(self._method_map.keys())}

    def __call__(self, method, *args, **kwargs):
        method = self._method_map.get(method)

        if callable(method):
            return method(*args, **kwargs)

    def __getitem__(self, item):
        return self._method_map[item]

    def __setitem__(self, key, value):
        self._method_map[key] = value

    def __delitem__(self, key):
        del self._method_map[key]

    def __len__(self):
        return len(self._method_map)

    def __iter__(self):
        return iter(self._method_map)


import zmq
from jsonrpc import JSONRPCResponseManager
from time import sleep


class ZMQJSONRPCServer(object):
    def __init__(self, wrapper, host='127.0.0.1', port='10000'):
        self.wrapper = wrapper
        self.host = host
        self.port = port

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        uri = 'tcp://{0}:{1}'.format(self.host, self.port)
        self.socket.bind(uri)

    def process(self):
        try:
            request = self.socket.recv_unicode(flags=zmq.NOBLOCK)
            print('Request: ', request)
            response = JSONRPCResponseManager.handle(request, self.wrapper)
            print('Sending response: ', response.json)
            self.socket.send_unicode(response.json)
        except zmq.Again:
            pass



s = Stuff()
e = RPCObjectWrapper(s)

print(dir(s))

server = ZMQJSONRPCServer(e)

while True:
    server.process()
    sleep(0.1)
