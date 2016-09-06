import zmq
import types


class ZMQJSONRPCServerException(Exception):
    def __init__(self, type, message):
        self.type = type
        self.message = message

    def __str__(self):
        return 'Exception on server side of type \'{}\': \'{}\''.format(self.type, self.message)


class ZMQJSONRPCProtocolException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

def json_rpc_call(socket, id, method, args=[]):
    socket.send_json(
        {'method': method,
         'params': args,
         'jsonrpc': '2.0',
         'id': id
         })

    return socket.recv_json()

class ZMQJSONRPCObjectProxyBase(object):
    _remote_getters = set()
    _remote_setters = set()

    def __init__(self, socket, methods=[]):
        self._id = 0
        self.socket = socket
        self._morph_into(methods)

    def _make_request(self, method, args=[]):
        self._id += 1

        response = json_rpc_call(self.socket, self._id, method, args)

        if 'result' in response:
            return response['result']

        if 'error' in response:
            if 'data' in response['error']:
                raise ZMQJSONRPCServerException(response['error']['data']['type'], response['error']['data']['message'])
            else:
                raise ZMQJSONRPCProtocolException(response['error']['message'])

    def _morph_into(self, methods):
        for method in [str(m) for m in methods]:
            if '.set' in method:
                self._remote_setters.add(method)
            elif '.get' in method:
                self._remote_getters.add(method)
            elif not method.startswith('.'):
                setattr(self, method, types.MethodType(self._create_wrapper_method(method), self))

    def _create_wrapper_method(self, method_name):
        def method_wrapper(obj, *args):
            return obj._make_request(method_name, args)

        return method_wrapper

    def __getattribute__(self, item):
        try:
            return super(ZMQJSONRPCObjectProxyBase, self).__getattribute__(item)
        except AttributeError:
            if '{}.get'.format(item) in self._remote_getters:
                return self._make_request('{}.get'.format(item))
            raise

    def __setattr__(self, key, value):
        if '{}.set'.format(key) in self._remote_setters:
            return self._make_request('{}.set'.format(key), [value,])

        return super(ZMQJSONRPCObjectProxyBase, self).__setattr__(key, value)

def ZMQJSONRPCObjectProxy(server='127.0.0.1', port='10000'):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect('tcp://{0}:{1}'.format(server, port))

    api = json_rpc_call(socket, 0, '.api')

    if 'result' in api:
        name = str(api['result']['class'])
        methods = api['result']['methods']

        return type(name, (ZMQJSONRPCObjectProxyBase,), {})(socket, methods)


s = ZMQJSONRPCObjectProxy()


print(s.a)
s.a = 10
print(s.a)
s.doIt()
print(s.a)
s.doItNow(23)
print(s.b)
print(s.a)
print(type(s))
print(s.g)
print(s.c)
s.c = 56