# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2020 European Spallation Source ERIC
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

import unittest

import zmq
from mock import Mock, call, patch

from lewis.core.control_client import (
    ControlClient,
    ObjectProxy,
    ProtocolException,
    RemoteException,
)


class TestControlClient(unittest.TestCase):
    @patch("zmq.Context")
    def test_zmq_socket_uses_timeout(self, mock_zmq_context):
        timeout = 100
        ControlClient(host="127.0.0.1", port="10002", timeout=timeout)

        mock_zmq_context.assert_has_calls(
            [
                call().setsockopt(zmq.SNDTIMEO, timeout),
                call().setsockopt(zmq.RCVTIMEO, timeout),
            ]
        )

    @patch("uuid.uuid4")
    @patch("lewis.core.control_client.ControlClient._get_zmq_req_socket")
    def test_json_rpc_timeout_raises(self, mock_socket, mock_uuid):
        def zmq_again(self):
            raise zmq.error.Again()

        raising_send = Mock(side_effect=zmq_again)
        mock_uuid.return_value = "2"

        connection = ControlClient(host="127.0.0.1", port="10001")
        connection._socket.send_json = raising_send
        self.assertRaises(ProtocolException, connection.json_rpc, "foo")

        raising_send.assert_called_once_with(
            {"method": "foo", "params": (), "jsonrpc": "2.0", "id": "2"}
        )

    @patch("uuid.uuid4")
    @patch("lewis.core.control_client.ControlClient._get_zmq_req_socket")
    def test_json_rpc(self, mock_socket, mock_uuid):
        mock_uuid.return_value = "2"

        connection = ControlClient(host="127.0.0.1", port="10001")
        connection.json_rpc("foo")

        mock_socket.assert_has_calls(
            [
                call(),
                call().connect("tcp://127.0.0.1:10001"),
                call().send_json(
                    {"method": "foo", "params": (), "jsonrpc": "2.0", "id": "2"}
                ),
                call().recv_json(),
            ]
        )

    @patch("lewis.core.control_client.ControlClient._get_zmq_req_socket")
    def test_get_remote_object_works(self, mock_socket):
        client = ControlClient(host="127.0.0.1", port="10001")

        with patch.object(client, "json_rpc") as json_rpc_mock:
            json_rpc_mock.return_value = (
                {
                    "id": 2,
                    "result": {
                        "class": "Test",
                        "methods": ["a:set", "a:get", "setTest"],
                    },
                },
                2,
            )

            obj = client.get_object()

            self.assertTrue(hasattr(type(obj), "a"))
            self.assertTrue(hasattr(obj, "setTest"))

            json_rpc_mock.assert_has_calls([call(":api")])

    @patch("lewis.core.control_client.ControlClient._get_zmq_req_socket")
    def test_get_remote_object_raises_exception(self, mock_socket):
        client = ControlClient(host="127.0.0.1", port="10001")

        with patch.object(client, "json_rpc") as json_rpc_mock:
            json_rpc_mock.return_value = ({"id": 2}, 2)

            self.assertRaises(ProtocolException, client.get_object)

            json_rpc_mock.assert_has_calls([call(":api")])

    @patch("lewis.core.control_client.ControlClient._get_zmq_req_socket")
    def test_get_remote_object_collection(self, mock_socket):
        client = ControlClient(host="127.0.0.1", port="10001")

        returned_object = Mock()
        returned_object.get_objects = Mock(return_value=["obj1", "obj2"])

        with patch.object(client, "get_object") as get_object_mock:
            get_object_mock.side_effect = [
                returned_object,
                "obj1_object",
                "obj2_object",
            ]

            objects = client.get_object_collection()

            self.assertTrue("obj1" in objects)
            self.assertTrue("obj2" in objects)

            returned_object.get_objects.assert_has_calls([call()])
            get_object_mock.assert_has_calls([call(""), call("obj1"), call("obj2")])


class TestObjectProxy(unittest.TestCase):
    def test_init_adds_members(self):
        mock_connection = Mock()
        obj = type("TestType", (ObjectProxy,), {})(
            mock_connection, ["a:get", "a:set", "setTest"]
        )
        self.assertTrue(hasattr(type(obj), "a"))
        self.assertTrue(hasattr(obj, "setTest"))

        mock_connection.assert_not_called()

    def test_member_access_calls_make_request(self):
        obj = type("TestType", (ObjectProxy,), {})(
            Mock(), ["a:get", "a:set", "setTest"]
        )

        with patch.object(obj, "_make_request") as request_mock:
            obj.a
            obj.a = 4
            obj.setTest()

        request_mock.assert_has_calls(
            [call("a:get"), call("a:set", 4), call("setTest")]
        )

    def test_response_without_id_raises_exception(self):
        mock_connection = Mock(ControlClient)
        mock_connection.json_rpc.return_value = ({"result": "test"}, 2)
        obj = type("TestType", (ObjectProxy,), {})(mock_connection, ["setTest"])

        self.assertRaises(ProtocolException, obj.setTest)

    def test_response_with_id_mismatch_raises_exception(self):
        mock_connection = Mock(ControlClient)
        mock_connection.json_rpc.return_value = ({"result": "test", "id": 3}, 2)
        obj = type("TestType", (ObjectProxy,), {})(mock_connection, ["setTest"])

        self.assertRaises(ProtocolException, obj.setTest)

    def test_make_request_with_result(self):
        mock_connection = Mock(ControlClient)
        mock_connection.json_rpc.return_value = ({"result": "test", "id": 2}, 2)
        obj = type("TestType", (ObjectProxy,), {})(mock_connection, ["setTest"])

        result = obj.setTest()

        self.assertEqual(result, "test")
        mock_connection.json_rpc.assert_has_calls([call("setTest")])

    def test_make_request_with_known_exception(self):
        mock_connection = Mock(ControlClient)
        mock_connection.json_rpc.return_value = (
            {
                "error": {
                    "data": {"type": "AttributeError", "message": "Some message"}
                },
                "id": 2,
            },
            2,
        )

        obj = type("TestType", (ObjectProxy,), {})(mock_connection, ["setTest"])

        self.assertRaises(AttributeError, obj.setTest)
        mock_connection.json_rpc.assert_has_calls([call("setTest")])

    def test_make_request_with_unknown_exception(self):
        mock_connection = Mock(ControlClient)
        mock_connection.json_rpc.return_value = (
            {
                "error": {
                    "data": {"type": "NonExistingException", "message": "Some message"}
                },
                "id": 2,
            },
            2,
        )

        obj = type("TestType", (ObjectProxy,), {})(mock_connection, ["setTest"])

        self.assertRaises(RemoteException, obj.setTest)
        mock_connection.json_rpc.assert_has_calls([call("setTest")])

    def test_make_request_with_missing_error_data(self):
        mock_connection = Mock(ControlClient)
        mock_connection.json_rpc.return_value = (
            {"error": {"message": "Some message"}},
            2,
        )

        obj = type("TestType", (ObjectProxy,), {})(mock_connection, ["setTest"])

        self.assertRaises(ProtocolException, obj.setTest)
        mock_connection.json_rpc.assert_has_calls([call("setTest")])
