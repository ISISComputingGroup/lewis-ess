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

import socket
import unittest

import zmq
from mock import Mock, call, patch

from lewis.core.control_server import (
    ControlServer,
    ExposedObject,
    ExposedObjectCollection,
)
from lewis.core.exceptions import LewisException

from .utils import assertRaisesNothing


class DummyObject:
    a = 10
    b = 20

    def __init__(self):
        self.getTest = Mock()
        self.setTest = Mock()


class DummyObjectChild(DummyObject):
    c = 30


class TestRPCObject(unittest.TestCase):
    def test_all_methods_exposed(self):
        rpc_object = ExposedObject(DummyObject())

        expected_methods = [
            ":api",
            "a:get",
            "a:set",
            "b:get",
            "b:set",
            "getTest",
            "setTest",
        ]
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_select_methods_exposed(self):
        rpc_object = ExposedObject(DummyObject(), ("a", "getTest"))

        expected_methods = [":api", "a:get", "a:set", "getTest"]
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_excluded_methods_not_exposed(self):
        rpc_object = ExposedObject(DummyObject(), exclude=("a", "setTest"))

        expected_methods = [":api", "b:get", "b:set", "getTest"]
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_selected_and_excluded_methods(self):
        rpc_object = ExposedObject(
            DummyObject(), members=("a", "getTest"), exclude=("a")
        )

        expected_methods = [":api", "getTest"]
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_inherited_not_exposed(self):
        rpc_object = ExposedObject(
            DummyObjectChild(), members=("a", "c"), exclude_inherited=True
        )

        expected_methods = [":api", "c:get", "c:set"]
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_inherited_exposed(self):
        rpc_object = ExposedObject(DummyObjectChild(), members=("a", "c"))

        expected_methods = [":api", "a:get", "a:set", "c:get", "c:set"]
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_invalid_method_raises(self):
        self.assertRaises(
            AttributeError, ExposedObject, DummyObject(), ("nonExisting",)
        )

    def test_attribute_wrapper_gets_value(self):
        obj = DummyObject()
        obj.a = 233

        rpc_object = ExposedObject(obj)
        self.assertEqual(rpc_object["a:get"](), obj.a)

    def test_attribute_wrapper_sets_value(self):
        obj = DummyObject()
        obj.a = 233

        rpc_object = ExposedObject(obj)

        self.assertEqual(obj.a, 233)
        rpc_object["a:set"](20)
        self.assertEqual(obj.a, 20)

    def test_attribute_wrapper_argument_number(self):
        rpc_object = ExposedObject(DummyObject())

        self.assertRaises(TypeError, rpc_object["a:get"], 20)
        self.assertRaises(TypeError, rpc_object["a:set"])
        self.assertRaises(TypeError, rpc_object["a:set"], 40, 30)

    def test_method_wrapper_calls(self):
        obj = DummyObject()
        rpc_object = ExposedObject(obj)

        rpc_object["getTest"](45, 56)

        obj.getTest.assert_called_with(45, 56)

    def test_get_api(self):
        obj = DummyObject()
        rpc_object = ExposedObject(obj, ["a"])
        api = rpc_object.get_api()

        self.assertTrue("class" in api)
        self.assertEqual(api["class"], type(obj).__name__)

        self.assertTrue("methods" in api)
        self.assertEqual(set(api["methods"]), {":api", "a:set", "a:get"})

    def test_lock_is_used_if_supplied(self):
        mock_lock = Mock()
        mock_lock.__enter__ = Mock()
        mock_lock.__exit__ = Mock()

        obj = DummyObject()
        exposed_object = ExposedObject(obj, ["a"], lock=mock_lock)

        self.assertEqual(exposed_object["a:get"](), obj.a)

        mock_lock.__enter__.assert_called_once()
        mock_lock.__exit__.assert_called_once()


class TestExposedObjectCollection(unittest.TestCase):
    def test_empty_initialization(self):
        exposed_objects = ExposedObjectCollection(named_objects={})
        self.assertEqual(set(exposed_objects), {":api", "get_objects"})

        self.assertEqual(len(exposed_objects.get_objects()), 0)
        self.assertEqual(
            exposed_objects["get_objects"](), exposed_objects.get_objects()
        )

    def test_api(self):
        exposed_objects = ExposedObjectCollection(named_objects={})

        api = exposed_objects[":api"]()
        self.assertTrue("class" in api)
        self.assertEqual(api["class"], "ExposedObjectCollection")
        self.assertTrue("methods" in api)
        self.assertEqual(set(api["methods"]), {"get_objects", ":api"})

    def test_add_plain_object(self):
        exposed_objects = ExposedObjectCollection({})
        obj = DummyObject()

        assertRaisesNothing(self, exposed_objects.add_object, obj, "testObject")

        # There should be :api, get_objects, testObject:api, testObject.a:get, testObject.a:set,
        # testObject.b:get, testObject.b:set, testObject.getTest, testObject.setTest
        self.assertEqual(len(exposed_objects), 9)

        exposed_objects["testObject.getTest"](34, 55)
        obj.getTest.assert_called_once_with(34, 55)

    def test_add_exposed_object(self):
        exposed_objects = ExposedObjectCollection({})
        obj = DummyObject()

        assertRaisesNothing(
            self,
            exposed_objects.add_object,
            ExposedObject(obj, ("setTest", "getTest")),
            "testObject",
        )
        exposed_objects["testObject.getTest"](41, 11)
        obj.getTest.assert_called_once_with(41, 11)

    def test_nested_collections(self):
        obj = DummyObject()
        exposed_objects = ExposedObjectCollection(
            {"container": ExposedObjectCollection({"test": obj})}
        )

        exposed_objects["container.test.getTest"](454, 43)
        obj.getTest.assert_called_once_with(454, 43)

    def test_duplicate_name_raises(self):
        exposed_objects = ExposedObjectCollection({})
        exposed_objects.add_object(DummyObject(), "testObject")

        self.assertRaises(
            RuntimeError, exposed_objects.add_object, DummyObject(), "testObject"
        )

    def test_remove_object(self):
        exposed_objects = ExposedObjectCollection({})
        own_functions_count = len(exposed_objects)

        obj = DummyObject()
        exposed_objects.add_object(obj, "testObject")

        self.assertListEqual(exposed_objects.get_objects(), ["testObject"])
        assertRaisesNothing(self, exposed_objects.remove_object, "testObject")
        self.assertEqual(len(exposed_objects), own_functions_count)

        self.assertRaises(RuntimeError, exposed_objects.remove_object, "does_not_exist")


class TestControlServer(unittest.TestCase):
    @patch("zmq.Context")
    def test_connection(self, mock_context):
        cs = ControlServer(None, connection_string="127.0.0.1:10001")
        cs.start_server()

        mock_context.assert_has_calls(
            [
                call(),
                call().socket(zmq.REP),
                call().socket().setsockopt(zmq.RCVTIMEO, 100),
                call().socket().bind("tcp://127.0.0.1:10001"),
            ]
        )

    @patch("zmq.Context")
    def test_server_can_only_be_started_once(self, mock_context):
        server = ControlServer(None, connection_string="127.0.0.1:10000")
        server.start_server()
        server.start_server()

        mock_context.assert_has_calls(
            [
                call(),
                call().socket(zmq.REP),
                call().socket().setsockopt(zmq.RCVTIMEO, 100),
                call().socket().bind("tcp://127.0.0.1:10000"),
            ]
        )

    def test_process_raises_if_not_started(self):
        server = ControlServer(None, connection_string="127.0.0.1:10000")

        self.assertRaises(Exception, server.process)

    def test_process_does_not_block(self):
        mock_socket = Mock()
        mock_socket.recv_unicode.side_effect = zmq.Again()

        server = ControlServer(None, connection_string="127.0.0.1:10000")
        server._socket = mock_socket
        assertRaisesNothing(self, server.process)

        mock_socket.recv_unicode.assert_has_calls([call(flags=zmq.NOBLOCK)])

    def test_exposed_object_is_exposed_directly(self):
        mock_collection = Mock(spec=ExposedObject)

        server = ControlServer(
            object_map=mock_collection, connection_string="127.0.0.1:10000"
        )
        self.assertEqual(server.exposed_object, mock_collection)

    @patch("lewis.core.control_server.ExposedObjectCollection")
    def test_exposed_object_collection_is_constructed(self, exposed_object_mock):
        ControlServer(object_map="test", connection_string="127.0.0.1:10000")

        exposed_object_mock.assert_called_once_with("test")

    @patch("zmq.Context")
    def test_is_running(self, mock_context):
        server = ControlServer(None, connection_string="127.0.0.1:10000")
        self.assertFalse(server.is_running)
        server.start_server()
        self.assertTrue(server.is_running)

    @patch("lewis.core.control_server.socket.gethostbyname")
    def test_invalid_hostname_raises_LewisException(self, gethostbyname_mock):
        def raise_exception(self):
            raise socket.gaierror

        gethostbyname_mock.side_effect = raise_exception

        self.assertRaises(
            LewisException,
            ControlServer,
            object_map=None,
            connection_string="some_invalid_host.local:10000",
        )

        gethostbyname_mock.assert_called_once_with("some_invalid_host.local")

    def test_localhost_does_not_raise_socket_error(self):
        assertRaisesNothing(
            self, ControlServer, object_map=None, connection_string="localhost:10000"
        )
