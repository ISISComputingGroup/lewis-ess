# -*- coding: utf-8 -*-
# *********************************************************************
# plankton - a library for creating hardware device simulators
# Copyright (C) 2016 European Spallation Source ERIC
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

from mock import Mock, patch, call
import zmq

from plankton.core.control_server import ExposedObject, ExposedObjectCollection, ControlServer
from . import assertRaisesNothing


class TestObject(object):
    def __init__(self):
        self.a = 10
        self.b = 20

        self.getTest = Mock()
        self.setTest = Mock()


class TestRPCObject(unittest.TestCase):
    def test_all_methods_exposed(self):
        rpc_object = ExposedObject(TestObject())

        expected_methods = [':api', 'a:get', 'a:set', 'b:get', 'b:set', 'getTest', 'setTest']
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_select_methods_exposed(self):
        rpc_object = ExposedObject(TestObject(), ('a', 'getTest'))

        expected_methods = [':api', 'a:get', 'a:set', 'getTest']
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_excluded_methods_not_exposed(self):
        rpc_object = ExposedObject(TestObject(), exclude=('a', 'setTest'))

        expected_methods = [':api', 'b:get', 'b:set', 'getTest']
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_selected_and_excluded_methods(self):
        rpc_object = ExposedObject(TestObject(), members=('a', 'getTest'), exclude=('a'))

        expected_methods = [':api', 'getTest']
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_invalid_method_raises(self):
        self.assertRaises(AttributeError, ExposedObject, TestObject(), ('nonExisting',))

    def test_attribute_wrapper_gets_value(self):
        obj = TestObject()
        obj.a = 233

        rpc_object = ExposedObject(obj)
        self.assertEqual(rpc_object['a:get'](), obj.a)

    def test_attribute_wrapper_sets_value(self):
        obj = TestObject()
        obj.a = 233

        rpc_object = ExposedObject(obj)

        self.assertEqual(obj.a, 233)
        rpc_object['a:set'](20)
        self.assertEqual(obj.a, 20)

    def test_attribute_wrapper_argument_number(self):
        rpc_object = ExposedObject(TestObject())

        self.assertRaises(TypeError, rpc_object['a:get'], 20)
        self.assertRaises(TypeError, rpc_object['a:set'])
        self.assertRaises(TypeError, rpc_object['a:set'], 40, 30)

    def test_method_wrapper_calls(self):
        obj = TestObject()
        rpc_object = ExposedObject(obj)

        rpc_object['getTest'](45, 56)

        obj.getTest.assert_called_with(45, 56)

    def test_get_api(self):
        obj = TestObject()
        rpc_object = ExposedObject(obj, ['a'])
        api = rpc_object.get_api()

        self.assertTrue('class' in api)
        self.assertEqual(api['class'], type(obj).__name__)

        self.assertTrue('methods' in api)
        self.assertEqual(set(api['methods']), {':api', 'a:set', 'a:get'})


class TestExposedObjectCollection(unittest.TestCase):
    def test_empty_initialization(self):
        exposed_objects = ExposedObjectCollection(named_objects={})
        self.assertEqual(set(exposed_objects), {':api', 'get_objects'})

        self.assertEqual(len(exposed_objects.get_objects()), 0)
        self.assertEqual(exposed_objects['get_objects'](), exposed_objects.get_objects())

    def test_api(self):
        exposed_objects = ExposedObjectCollection(named_objects={})

        api = exposed_objects[':api']()
        self.assertTrue('class' in api)
        self.assertEqual(api['class'], 'ExposedObjectCollection')
        self.assertTrue('methods' in api)
        self.assertEqual(set(api['methods']), {'get_objects', ':api'})

    def test_add_plain_object(self):
        exposed_objects = ExposedObjectCollection({})
        obj = TestObject()

        assertRaisesNothing(self, exposed_objects.add_object, obj, 'testObject')

        # There should be :api, get_objects, testObject:api, testObject.a:get, testObject.a:set,
        # testObject.b:get, testObject.b:set, testObject.getTest, testObject.setTest
        self.assertEqual(len(exposed_objects), 9)

        exposed_objects['testObject.getTest'](34, 55)
        obj.getTest.assert_called_once_with(34, 55)

    def test_add_exposed_object(self):
        exposed_objects = ExposedObjectCollection({})
        obj = TestObject()

        assertRaisesNothing(self, exposed_objects.add_object,
                            ExposedObject(obj, ('setTest', 'getTest')), 'testObject')
        exposed_objects['testObject.getTest'](41, 11)
        obj.getTest.assert_called_once_with(41, 11)

    def test_nested_collections(self):
        obj = TestObject()
        exposed_objects = ExposedObjectCollection(
            {'container': ExposedObjectCollection({'test': obj})})

        exposed_objects['container.test.getTest'](454, 43)
        obj.getTest.assert_called_once_with(454, 43)


class TestControlServer(unittest.TestCase):
    @patch('plankton.core.control_server.ControlServer.start_server')
    def test_start_server_behaves_properly(self, start_server_mock):
        ControlServer()
        start_server_mock.assert_not_called()
        ControlServer(start=False)
        start_server_mock.assert_not_called()

        ControlServer(start=True)
        start_server_mock.assert_has_calls([call()])

    @patch('zmq.Context')
    def test_connection(self, mock_context):
        ControlServer(host='127.0.0.1', port='10001', start=True)

        mock_context.assert_has_calls([call(), call().socket(zmq.REP),
                                       call().socket().bind('tcp://127.0.0.1:10001')])

    @patch('zmq.Context')
    def test_server_can_only_be_started_once(self, mock_context):
        server = ControlServer(host='127.0.0.1', port='10000')
        server.start_server()
        server.start_server()

        mock_context.assert_has_calls([call(), call().socket(zmq.REP),
                                       call().socket().bind('tcp://127.0.0.1:10000')])

    def test_process_raises_if_not_started(self):
        server = ControlServer()

        self.assertRaises(Exception, server.process)

    def test_process_does_not_block(self):
        mock_socket = Mock()
        mock_socket.recv_unicode.side_effect = zmq.Again()

        server = ControlServer()
        server._socket = mock_socket
        assertRaisesNothing(self, server.process)

        mock_socket.recv_unicode.assert_has_calls([call(flags=zmq.NOBLOCK)])

    def test_exposed_object_is_exposed_directly(self):
        mock_collection = Mock(spec=ExposedObject)

        server = ControlServer(object_map=mock_collection)
        self.assertEqual(server.exposed_object, mock_collection)

    @patch('plankton.core.control_server.ExposedObjectCollection')
    def test_exposed_object_collection_is_constructed(self, exposed_object_mock):
        ControlServer(object_map='test')

        exposed_object_mock.assert_called_once_with('test')

    @patch('zmq.Context')
    def test_is_running(self, mock_context):
        server = ControlServer(start=False)
        self.assertFalse(server.is_running)
        server.start_server()
        self.assertTrue(server.is_running)
