import zmq
import uuid
import types
import exceptions


class ZMQJSONRPCServerSideException(Exception):
    def __init__(self, type, message):
        """
        This exception type replaces exceptions that are raised on the server,
        but unknown (i.e. not in the exceptions-module) on the client side.
        To retain as much information as possible, the exception type on the server and
        the message are stored.

        :param type: Type of the exception on the server side.
        :param message: Exception message.
        """
        self.type = type
        self.message = message

    def __str__(self):
        return 'Exception on server side of type \'{}\': \'{}\''.format(self.type, self.message)


class ZMQJSONRPCProtocolException(Exception):
    def __init__(self, message):
        """
        An exception type for exceptions related to the transport protocol, i.e.
        malformed requests etc.

        :param message: A message describing the exception.
        """
        self.message = message

    def __str__(self):
        return self.message


class ZMQJSONRPCConnection(object):
    def __init__(self, host='127.0.0.1', port='10000'):
        context = zmq.Context()
        self._socket = context.socket(zmq.REQ)
        self._socket.connect('tcp://{0}:{1}'.format(host, port))

    def json_rpc(self, method, args=[]):
        """
        This method takes a ZMQ REQ-socket and submits a JSON-object containing
        the RPC (JSON-RPC 2.0 format) to the supplied method with the supplied arguments.
        Then it waits for a reply from the server and blocks until it has received
        a JSON-response. The method returns the response and the id it used to tag
        the original request, which is a random UUID (uuid.uuid4).

        :param socket: ZMQ REQ-socket.
        :param method: Method to call on remote.
        :param args: Arguments to method call.
        :return: JSON result and request id.
        """
        id = str(uuid.uuid4())
        self._socket.send_json(
            {'method': method,
             'params': args,
             'jsonrpc': '2.0',
             'id': id
             })

        return self._socket.recv_json(), id


class ZMQJSONRPCObjectProxy(object):
    def __init__(self, connection, members, prefix=''):
        """
        This class serves as a base class for dynamically created classes on the
        client side that represent server-side objects. Upon initialization,
        this class takes the supplied methods and installs appropriate proxy methods
        or properties into the object and class respectively. Because of that
        class manipulation, this class must never be used directly.
        Instead, it should be used as a base-class for dynamically created types
        that mirror types on the server, like this:

            proxy = type('SomeClassName', (ZMQJSONRPCObjectProxy, ), {})(socket, methods, prefix)

        There is however, the class RemoteObjectCollection, which automates all that
        and provides objects that are ready to use.

        Exceptions on the server are propagated to the client. If the exception is not part
        of the exceptions-module, a ZMQJSONRPCServerSideException is raised instead, which
        contains information about the server side exception.

        All RPC method names are prefixed with the supplied prefix, which is usually the
        object name on the server plus a dot.

        :param connection: ZMQREQConnection-object for remote calls.
        :param members: List of strings to generate methods and properties.
        :param prefix: Usually object name on the server plus dot.
        """
        self._properties = set()

        self._connection = connection
        self._add_member_proxies(members)
        self._prefix = prefix

    def _make_request(self, method, args=[]):
        """
        This method performs a JSON-RPC request via the object's ZMQ socket. If successful,
        the result is returned, otherwise exceptions are raised. Server side exceptions are
        raised using the same type as on the server if they are part of the exceptions-module.
        Otherwise, a ZMQJSONRPCServerSideException is raised.

        :param method: Method of the object to call on the remote.
        :param args: Positional arguments to the method call.
        :return: Result of the remote call if successful.
        """
        response, id = self._connection.json_rpc(self._prefix + method, args)

        if 'result' in response:
            return response['result']

        if 'error' in response:
            if 'data' in response['error']:
                exception_type = response['error']['data']['type']
                exception_message = response['error']['data']['message']

                try:
                    exception = getattr(exceptions, exception_type)
                    raise exception(exception_message)
                except AttributeError:
                    raise ZMQJSONRPCServerSideException(exception_type, exception_message)
            else:
                raise ZMQJSONRPCProtocolException(response['error']['message'])

    def _add_member_proxies(self, members):
        for member in [str(m) for m in members]:
            if ':set' in member or ':get' in member:
                self._properties.add(member.split(':')[-2].split('.')[-1])
            else:
                setattr(self, member, types.MethodType(self._create_method_proxy(member), self))

        for prop in self._properties:
            setattr(type(self), prop, property(self._create_getter_proxy(prop),
                                               self._create_setter_proxy(prop)))

    def _create_getter_proxy(self, property_name):
        def getter(obj):
            return obj._make_request(property_name + ':get')

        return getter

    def _create_setter_proxy(self, property_name):
        def setter(obj, value):
            return obj._make_request(property_name + ':set', [value])

        return setter

    def _create_method_proxy(self, method_name):
        def method_wrapper(obj, *args):
            return obj._make_request(method_name, args)

        return method_wrapper


def get_remote_object(connection, object_name=''):
    api, request_id = connection.json_rpc(object_name + ':api')

    if not 'result' in api or api['id'] != request_id:
        raise ZMQJSONRPCProtocolException('Failed to retrieve API of remote object.')

    object_type = type(str(api['result']['class']), (ZMQJSONRPCObjectProxy,), {})
    methods = api['result']['methods']

    glue = '.' if object_name else ''
    return object_type(connection, methods, object_name + glue)


class RemoteObjectCollection(object):
    def __init__(self, connection):
        """
        The responsibility of this class is to create client side proxies for the objects
        that are exposed by an RPC-server that exposes an ExposedObjectCollection.
        A connection is established to the supplied host and port and the server
        is queried for its objects. The API of each object is queried,
        which includes the type name and the object members.

        Each type that occurs is created as a subclass of ZMQJSONRPCObjectProxy, which
        means that objects sharing type on the server side will also share type
        on the client side. Finally, each object is created and stored in a dictionary.

        Object access would typically be done via the dict-like interface of the collection:

            remote_objects = RemoteObjectCollection(some_host, some_port)
            obj = remote_objects['device']

        Now obj can be used like it could be on the server side, at least the parts that are
        exposed and all actions performed on obj are forwarded to the server.

        :param connection: A ZMQJSONRPCConnection which is used to obtain the objects that are exposed on the server side.
        """
        objects, request_id = connection.json_rpc('get_objects')

        self.objects = {}

        if 'result' in objects and objects['id'] == request_id:
            for obj in objects['result']:
                self.objects[obj] = get_remote_object(connection, obj)
        else:
            raise ZMQJSONRPCProtocolException(
                'The server does not expose a get_objects-method that is required to retrieve objects from the server side.')

    def keys(self):
        return list(self.objects.keys())

    def __iter__(self):
        return iter(self.objects)

    def __getitem__(self, item):
        return self.objects[item]
