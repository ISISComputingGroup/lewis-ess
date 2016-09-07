import zmq
import uuid
import types


class ZMQJSONRPCServerSideException(Exception):
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


def json_rpc_call(socket, method, args=[]):
    id = str(uuid.uuid4())
    socket.send_json(
        {'method': method,
         'params': args,
         'jsonrpc': '2.0',
         'id': id
         })

    return socket.recv_json(), id


class ZMQJSONRPCObjectProxy(object):
    _remote_getters = set()
    _remote_setters = set()

    def __init__(self, socket, prefix='', methods=[]):
        self.socket = socket
        self._morph_into(methods)
        self.prefix = prefix

    def _make_request(self, method, args=[]):
        response, id = json_rpc_call(self.socket, self.prefix + method, args)

        if 'result' in response:
            return response['result']

        if 'error' in response:
            if 'data' in response['error']:
                raise ZMQJSONRPCServerSideException(response['error']['data']['type'],
                                                    response['error']['data']['message'])
            else:
                raise ZMQJSONRPCProtocolException(response['error']['message'])

    def _morph_into(self, methods):
        for method in [str(m) for m in methods]:
            if ':set' in method:
                self._remote_setters.add(method)
            elif ':get' in method:
                self._remote_getters.add(method)
            elif not method.startswith('.'):
                setattr(self, method, types.MethodType(self._create_wrapper_method(method), self))

    def _create_wrapper_method(self, method_name):
        def method_wrapper(obj, *args):
            return obj._make_request(method_name, args)

        return method_wrapper

    def __getattribute__(self, item):
        try:
            return super(ZMQJSONRPCObjectProxy, self).__getattribute__(item)
        except AttributeError:
            if '{}:get'.format(item) in self._remote_getters:
                return self._make_request('{}:get'.format(item))
            raise

    def __setattr__(self, key, value):
        if '{}:set'.format(key) in self._remote_setters:
            return self._make_request('{}:set'.format(key), [value, ])

        return super(ZMQJSONRPCObjectProxy, self).__setattr__(key, value)


class RemoteObjectCollection(object):
    def __init__(self, server='127.0.0.1', port='10000'):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect('tcp://{0}:{1}'.format(server, port))

        objects, id = json_rpc_call(socket, ':objects')

        self.objects = {}

        if 'result' in objects and objects['id'] == id:
            for obj in objects['result']:
                api, id = json_rpc_call(socket, obj + ':api')

                if 'result' in api and api['id'] == id:
                    name = str(api['result']['class'])
                    methods = api['result']['methods']

                    self.objects[obj] = type(name, (ZMQJSONRPCObjectProxy,), {})(socket, obj + '.', methods)

    def keys(self):
        return list(self.objects.keys())

    def __iter__(self):
        return iter(self.objects)

    def __getitem__(self, item):
        return self.objects[item]
