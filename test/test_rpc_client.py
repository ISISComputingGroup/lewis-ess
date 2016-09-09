import unittest

from . import assertRaisesNothing

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from core.rpc_client import JSONRPCObjectProxy, get_remote_object, get_remote_object_collection


class TestZMQJSONRPCObjectProxy(unittest.TestCase):
    def test_init_adds_members(self):
        with Mock() as mock_connection:
            obj = type('TestType', (JSONRPCObjectProxy,), {})(mock_connection, ['a:get', 'a:set', 'setTest'])

            self.assertTrue(hasattr(obj, 'a'))
            self.assertTrue(hasattr(obj, 'setTest'))
