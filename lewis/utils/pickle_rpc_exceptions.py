"""Pickle-RPC Exceptions."""
import pickle


class PickleRPCError(object):

    """Error for Pickle-RPC communication.

    Using the same exceptions and error codes as JSON-RPC

    """

    serialize = staticmethod(pickle.dumps)
    deserialize = staticmethod(pickle.loads)

    def __init__(self, code=None, message=None, data=None):
        self._data = dict()
        self.code = getattr(self.__class__, "CODE", code)
        self.message = getattr(self.__class__, "MESSAGE", message)
        self.data = data

    def __get_code(self):
        return self._data["code"]

    def __set_code(self, value):
        if not isinstance(value, int):
            raise ValueError("Error code should be integer")

        self._data["code"] = value

    code = property(__get_code, __set_code)

    def __get_message(self):
        return self._data["message"]

    def __set_message(self, value):
        if not isinstance(value, str):
            raise ValueError("Error message should be string")

        self._data["message"] = value

    message = property(__get_message, __set_message)

    def __get_data(self):
        return self._data.get("data")

    def __set_data(self, value):
        if value is not None:
            self._data["data"] = value

    data = property(__get_data, __set_data)

    @classmethod
    def from_pickled(cls, pickled_object):
        data = cls.deserialize(pickled_object)
        return cls(code=data["code"], message=data["message"], data=data.get("data"))

    @property
    def pickled(self):
        return self.serialize(self._data)


class PickleRPCParseError(PickleRPCError):

    """Parse Error.

    Invalid Pickle was received by the server.
    An error occurred on the server while parsing the Pickle text.

    """

    CODE = -32700
    MESSAGE = "Parse error"


class PickleRPCInvalidRequest(PickleRPCError):

    """Invalid Request.

    The Pickle sent is not a valid Request object.

    """

    CODE = -32600
    MESSAGE = "Invalid Request"


class PickleRPCMethodNotFound(PickleRPCError):

    """Method not found.

    The method does not exist / is not available.

    """

    CODE = -32601
    MESSAGE = "Method not found"


class PickleRPCInvalidParams(PickleRPCError):

    """Invalid params.

    Invalid method parameter(s).

    """

    CODE = -32602
    MESSAGE = "Invalid params"


class PickleRPCInternalError(PickleRPCError):

    """Internal error.

    Internal Pickle-RPC error.

    """

    CODE = -32603
    MESSAGE = "Internal error"


class PickleRPCServerError(PickleRPCError):

    """Server error.

    Reserved for implementation-defined server-errors.

    """

    CODE = -32000
    MESSAGE = "Server error"


class PickleRPCException(Exception):

    """ Pickle-RPC Exception."""

    pass


class PickleRPCInvalidRequestException(PickleRPCException):

    """ Request is not valid."""

    pass


class PickleRPCDispatchException(PickleRPCException):

    """Pickle-RPC Dispatch Exception.

    Should be thrown in dispatch methods.

    """

    def __init__(self, code=None, message=None, data=None, *args, **kwargs):
        super(PickleRPCDispatchException, self).__init__(args, kwargs)
        self.error = PickleRPCError(code=code, data=data, message=message)
