#!/usr/bin/env python
#  -*- coding: utf-8 -*-
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

try:
    from unittest.mock import Mock, patch, call
except ImportError:
    from mock import Mock, patch, call

from core.rpc_client import JSONRPCObjectProxy, ZMQJSONRPCConnection, JSONRPCProtocolException
from core.rpc_client import get_remote_object, get_remote_object_collection


class TestJSONRPCObjectProxy(unittest.TestCase):
    def test_init_adds_members(self):
        mock_connection = Mock()
        obj = type('TestType', (JSONRPCObjectProxy,), {})(mock_connection, ['a:get', 'a:set', 'setTest'])
        self.assertTrue(hasattr(type(obj), 'a'))
        self.assertTrue(hasattr(obj, 'setTest'))

        mock_connection.assert_not_called()

    def test_member_access_calls_make_request(self):
        obj = type('TestType', (JSONRPCObjectProxy,), {})(Mock(), ['a:get', 'a:set', 'setTest'])

        with patch.object(obj, '_make_request') as request_mock:
            b = obj.a
            obj.a = 4
            obj.setTest()

        request_mock.assert_has_calls([call('a:get'), call('a:set', [4]), call('setTest', ())])


class TestRemoteObjectFunctions(unittest.TestCase):
    def test_get_remote_object_works(self):
        mock_connection = Mock(ZMQJSONRPCConnection)
        mock_connection.json_rpc = Mock(return_value=({'id': 2,
                                                       'result': {'class': 'Test',
                                                                  'methods': ['a:set', 'a:get', 'setTest']}}
                                                      , 2))

        obj = get_remote_object(mock_connection)

        self.assertTrue(hasattr(type(obj), 'a'))
        self.assertTrue(hasattr(obj, 'setTest'))

        mock_connection.json_rpc.assert_has_calls([call(':api')])

    def test_get_remote_object_no_result_raises(self):
        mock_connection = Mock(ZMQJSONRPCConnection)
        mock_connection.json_rpc = Mock(return_value=({'id': 2}, 2))

        self.assertRaises(JSONRPCProtocolException, get_remote_object, mock_connection)

        mock_connection.json_rpc.assert_has_calls([call(':api')])

    @patch('core.rpc_client.get_remote_object')
    def test_get_remote_object_collection(self, mock_get_remote_object):
        mock_get_remote_object.return_value = 'test'

        mock_connection = Mock(ZMQJSONRPCConnection)
        mock_connection.json_rpc = Mock(return_value=({'id': 2,
                                                       'result': ['obj1', 'obj2']}, 2))

        objects = get_remote_object_collection(mock_connection)

        self.assertTrue('obj1' in objects)
        self.assertTrue('obj2' in objects)

        mock_get_remote_object.assert_has_calls([call(mock_connection, 'obj1'),
                                                 call(mock_connection, 'obj2')])
