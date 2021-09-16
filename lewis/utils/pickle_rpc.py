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
This module essentially a copy of json-rpc (https://github.com/pavlov99/json-rpc), 
but uses pickle for serialization to allow for sending and receiving of more complex types
"""

import inspect
import pickle

from .pickle_RPC_exceptions import (
    PickleRPCInvalidRequest,
    PickleRPCError,
    PickleRPCInvalidRequestException,
    PickleRPCParseError,
    PickleRPCMethodNotFound,
    PickleRPCDispatchException,
    PickleRPCInvalidParams,
    PickleRPCServerError,
)


class PickleRPCResponseManager:
    """Pickle-RPC response manager.

    An analogue of the same in the JSON-RPC library. Given a dispatcher it handles reqeuest and errors.

    :param bytes request: a pickled object representing an RPC request. Converted into a Pickle-RPCRequest

    :param dict dispatcher: dict<function_name:function>.

    """

    @classmethod
    def handle(cls, request_bytes, dispatcher):
        try:
            data = pickle.loads(request_bytes)
        except (TypeError, ValueError):
            return PickleRPCResponse(error=PickleRPCParseError()._data)

        try:
            request = PickleRPCRequest.from_data(data)
        except PickleRPCInvalidRequestException:
            return PickleRPCResponse(error=PickleRPCInvalidRequest()._data)

        return cls.handle_request(request, dispatcher)

    @classmethod
    def handle_request(cls, request, dispatcher):
        """Handle request data.

        At this moment request has been validated by self.handle()

        :param dict request: data parsed from request_bytes.
        :param picklerpc.dispatcher.Dispatcher dispatcher:

        """
        rs = request if isinstance(request, PickleRPCBatchRequest) else [request]
        responses = [r for r in cls._get_responses(rs, dispatcher) if r is not None]

        # notifications
        if not responses:
            return

        if isinstance(request, PickleRPCBatchRequest):
            response = PickleRPCBatchResponse(*responses)
            response.request = request
            return response
        else:
            return responses[0]

    @classmethod
    def _get_responses(cls, requests, dispatcher):
        """Response to each single Pickle-RPC Request.

        :return iterator(PickleRPCResponse):

        """
        for request in requests:

            def make_response(**kwargs):
                response = PickleRPCResponse(_id=request._id, **kwargs)
                response.request = request
                return response

            output = None
            try:
                method = dispatcher[request.method]
            except KeyError:
                output = make_response(error=PickleRPCMethodNotFound()._data)
            else:
                try:
                    result = method(*request.args, **request.kwargs)
                except PickleRPCDispatchException as e:
                    output = make_response(error=e.error._data)
                except Exception as e:
                    data = {
                        "type": e.__class__.__name__,
                        "args": e.args,
                        "message": str(e),
                    }
                    # no logger yet
                    # logger.exception("API Exception: {0}".format(data))

                    if isinstance(e, TypeError) and is_invalid_params(
                        method, *request.args, **request.kwargs
                    ):
                        output = make_response(
                            error=PickleRPCInvalidParams(data=data)._data
                        )
                    else:
                        output = make_response(
                            error=PickleRPCServerError(data=data)._data
                        )
                else:
                    output = make_response(result=result)
            finally:
                if not request.is_notification:
                    yield output


class PickleRPCRequest:
    """Define the format of the RPC request

    Pretty much a direct copy of JSONRPC20Request in json-rpc.
    Adopting that format as version 1 of our PickleRPCRequest format

    :param str method: A String containing the name of the method to be
        invoked. Method names that begin with the word rpc followed by a
        period character (U+002E or ASCII 46) are reserved for rpc-internal
        methods and extensions and MUST NOT be used for anything else.

    :param params: A Structured value that holds the parameter values to be
        used during the invocation of the method. This member MAY be omitted.
    :type params: iterable or dict

    :param _id: An identifier established by the Client that MUST contain a
        String, Number, or NULL value if included. If it is not included it is
        assumed to be a notification.
    :type _id: str or int or None

    :param bool is_notification: Whether request is notification or not. If
        value is True, _id is not included to request. It allows to create
        requests with id = null.

    The Server MUST reply with the same value in the Response object if
    included. This member is used to correlate the context between the two
    objects.

    """

    VERSION = "1"
    REQUIRED_FIELDS = set(["picklerpc", "method"])
    POSSIBLE_FIELDS = set(["picklerpc", "method", "params", "id"])

    def __init__(self, method=None, params=None, _id=None, is_notification=None):
        self.data = dict()
        self.method = method
        self.params = params
        self._id = _id
        self.is_notification = is_notification

    @property
    def data(self):
        data = dict(
            (k, v)
            for k, v in self._data.items()
            if not (k == "id" and self.is_notification)
        )
        data["picklerpc"] = self.VERSION
        return data

    @data.setter
    def data(self, value):
        if not isinstance(value, dict):
            raise ValueError("data should be dict")

        self._data = value

    @property
    def params(self):
        return self._data.get("params")

    @params.setter
    def params(self, value):
        # Add some guard here perhaps?
        value = list(value) if isinstance(value, tuple) else value

        if value is not None:
            self._data["params"] = value

    @property
    def _id(self):
        return self._data.get("id")

    @_id.setter
    def _id(self, value):
        if value is not None and not isinstance(value, (str, int)):
            raise ValueError("id should be string or integer")
        self._data["id"] = value

    @property
    def args(self):
        """Method position arguments.

        :return tuple args: method position arguments.

        """
        return tuple(self.params) if isinstance(self.params, list) else ()

    @property
    def kwargs(self):
        """Method named arguments.

        :return dict kwargs: method named arguments.

        """
        return self.params if isinstance(self.params, dict) else {}

    @property
    def json(self):
        return self.serialize(self.data)

    @classmethod
    def from_pickle(cls, pickled_object):
        data = pickle.loads(pickled_object)
        return cls.from_data(data)

    @classmethod
    def from_data(cls, data):
        is_batch = isinstance(data, list)
        data = data if is_batch else [data]

        if not data:
            raise PickleRPCInvalidRequestException("[] value is not accepted")

        if not all(isinstance(d, dict) for d in data):
            raise PickleRPCInvalidRequestException(
                "Each request should be an object (dict)"
            )

        result = []
        for d in data:
            if not cls.REQUIRED_FIELDS <= set(d.keys()) <= cls.POSSIBLE_FIELDS:
                extra = set(d.keys()) - cls.POSSIBLE_FIELDS
                missed = cls.REQUIRED_FIELDS - set(d.keys())
                msg = "Invalid request. Extra fields: {0}, Missed fields: {1}"
                raise PickleRPCInvalidRequestException(msg.format(extra, missed))

            try:
                result.append(
                    PickleRPCRequest(
                        method=d["method"],
                        params=d.get("params"),
                        _id=d.get("id"),
                        is_notification="id" not in d,
                    )
                )
            except ValueError as e:
                raise PickleRPCInvalidRequestException(str(e))

        return PickleRPCBatchRequest(*result) if is_batch else result[0]


class PickleRPCBatchRequest:

    """Batch Pickle-RPC Request.

    :param PickleRPCRequest *requests: requests

    """

    VERSION = "1"

    def __init__(self, *requests):
        self.requests = requests

    @classmethod
    def from_pickle(cls, pickled_object):
        return PickleRPCRequest.from_pickle(pickled_object)

    @property
    def pickled(self):
        return pickle.dumps([r.data for r in self.requests])

    def __iter__(self):
        return iter(self.requests)


class PickleRPCResponse:

    """Pickle-RPC response object to PickleRPCRequest.

    When a rpc call is made, the Server MUST reply with a Response, except for
    in the case of Notifications. The Response is expressed as a dictionary
    with the following members:

    :param str picklerpc: A String specifying the version of the Pickle-RPC
        protocol. Currently only version 1 exists.

    :param result: This member is REQUIRED on success.
        This member MUST NOT exist if there was an error invoking the method.
        The value of this member is determined by the method invoked on the
        Server.

    :param dict error: This member is REQUIRED on error.
        This member MUST NOT exist if there was no error triggered during
        invocation. The value for this member MUST be an Object.

    :param id: This member is REQUIRED.
        It MUST be the same as the value of the id member in the Request
        Object. If there was an error in detecting the id in the Request
        object (e.g. Parse error/Invalid Request), it MUST be Null.
    :type id: str or int or None

    Either the result member or error member MUST be included, but both
    members MUST NOT be included.

    """

    VERSION = "1"

    def __init__(self, **kwargs):
        self.data = dict()
        try:
            self.result = kwargs["result"]
        except KeyError:
            pass

        try:
            self.error = kwargs["error"]
        except KeyError:
            pass

        self._id = kwargs.get("_id")

        if "result" not in kwargs and "error" not in kwargs:
            raise ValueError("Either result or error should be used")

        self.request = None

    @property
    def data(self):
        data = dict((k, v) for k, v in self._data.items())
        data["picklerpc"] = self.VERSION
        return data

    @data.setter
    def data(self, value):
        if not isinstance(value, dict):
            raise ValueError("data should be dict")
        self._data = value

    @property
    def result(self):
        return self._data.get("result")

    @result.setter
    def result(self, value):
        if self.error:
            raise ValueError("Either result or error should be used")
        self._data["result"] = value

    @property
    def error(self):
        return self._data.get("error")

    @error.setter
    def error(self, value):
        self._data.pop("value", None)
        if value:
            self._data["error"] = value
            # Test error
            PickleRPCError(**value)

    @property
    def _id(self):
        return self._data.get("id")

    @_id.setter
    def _id(self, value):
        if value is not None and not isinstance(value, (str, int)):
            raise ValueError("id should be string or integer")

        self._data["id"] = value

    @property
    def pickled(self):
        return pickle.dumps(self.data)


class PickleRPCBatchResponse:

    VERSION = "1"

    def __init__(self, *responses):
        self.responses = responses
        self.request = None

    @property
    def data(self):
        return [r.data for r in self.responses]

    @property
    def pickled(self):
        return pickle.dumps(self.data)

    def __iter__(self):
        return iter(self.responses)


def is_invalid_params(func, *args, **kwargs):
    """
    Use inspect.signature instead of inspect.getargspec or
    inspect.getfullargspec (based on inspect.signature itself) as it provides
    more information about function parameters.

    """
    signature = inspect.signature(func)
    parameters = signature.parameters

    unexpected = set(kwargs.keys()) - set(parameters.keys())
    if len(unexpected) > 0:
        return True

    params = [parameter for name, parameter in parameters.items() if name not in kwargs]
    params_required = [param for param in params if param.default is param.empty]

    return not (len(params_required) <= len(args) <= len(params))