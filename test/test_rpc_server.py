import unittest

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from core.rpc_server import RPCObject, RPCObjectCollection, ZMQJSONRPCServer


class TestObject(object):
    def __init__(self):
        self.a = 10
        self.b = 20

        self.getTest = Mock()
        self.setTest = Mock()


class TestRPCObject(unittest.TestCase):
    def test_all_methods_exposed(self):
        rpc_object = RPCObject(TestObject())

        expected_methods = ['a:get', 'a:set', 'b:get', 'b:set', 'getTest', 'setTest']
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_select_methods_exposed(self):
        rpc_object = RPCObject(TestObject(), ('a', 'getTest'))

        expected_methods = ['a:get', 'a:set', 'getTest']
        self.assertEqual(len(rpc_object), len(expected_methods))

        for method in expected_methods:
            self.assertTrue(method in rpc_object)

    def test_invalid_method_raises(self):
        self.assertRaises(AttributeError, RPCObject, TestObject(), ('nonExisting',))

    def test_attribute_wrapper_gets_value(self):
        obj = TestObject()
        obj.a = 233

        rpc_object = RPCObject(obj)
        self.assertEqual(rpc_object['a:get'](), obj.a)

    def test_attribute_wrapper_sets_value(self):
        obj = TestObject()
        obj.a = 233

        rpc_object = RPCObject(obj)

        self.assertEqual(obj.a, 233)
        rpc_object['a:set'](20)
        self.assertEqual(obj.a, 20)

    def test_attribute_wrapper_argument_number(self):
        rpc_object = RPCObject(TestObject())

        self.assertRaises(TypeError, rpc_object['a:get'], 20)
        self.assertRaises(TypeError, rpc_object['a:set'])
        self.assertRaises(TypeError, rpc_object['a:set'], 40, 30)

    def test_method_wrapper_calls(self):
        obj = TestObject()
        rpc_object = RPCObject(obj)

        rpc_object['getTest'](45, 56)

        obj.getTest.assert_called_with(45, 56)

    def test_get_api(self):
        obj = TestObject()
        rpc_object = RPCObject(obj, ['a'])
        api = rpc_object.get_api()

        self.assertTrue('class' in api)
        self.assertEqual(api['class'], type(obj).__name__)

        self.assertTrue('methods' in api)
        self.assertEqual(set(api['methods']), {'a:set', 'a:get'})

class TestRPCObjectCollection(unittest.TestCase):
    pass