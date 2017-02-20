import unittest

from mock import patch, call
import inspect

from lewis.adapters.stream import StreamAdapter
from lewis.core.adapters import is_adapter, Adapter, AdapterCollection
from . import assertRaisesNothing


class TestIsAdapter(unittest.TestCase):
    def test_not_a_type_returns_false(self):
        self.assertFalse(is_adapter(0.0))
        self.assertFalse(is_adapter(None))

    def test_arbitrary_types_fail(self):
        self.assertFalse(is_adapter(type(3.0)))
        self.assertFalse(is_adapter(property))

    def test_adapter_base_is_ignored(self):
        self.assertFalse(is_adapter(Adapter))
        self.assertFalse(is_adapter(StreamAdapter))

    def test_adapter_types_work(self):
        self.assertTrue(is_adapter(DummyAdapter))


class DummyAdapter(Adapter):
    """
    A dummy adapter for tests.
    """

    def __init__(self, protocol, running=False):
        super(DummyAdapter, self).__init__(None)
        self.protocol = protocol
        self._running = running

    def start_server(self):
        self._running = True

    def stop_server(self):
        self._running = False

    @property
    def is_running(self):
        return self._running


class TestAdapter(unittest.TestCase):
    def test_documentation(self):
        adapter = DummyAdapter('foo')

        self.assertEqual(inspect.cleandoc(adapter.__doc__), adapter.documentation)


class TestAdapterContainer(unittest.TestCase):
    def test_add_adapter(self):
        collection = AdapterCollection()
        self.assertEquals(len(collection.protocols), 0)

        assertRaisesNothing(self, collection.add_adapter, DummyAdapter('foo'))

        self.assertEqual(len(collection.protocols), 1)
        self.assertSetEqual(set(collection.protocols), {'foo'})

        assertRaisesNothing(self, collection.add_adapter, DummyAdapter('bar'))

        self.assertEqual(len(collection.protocols), 2)
        self.assertSetEqual(set(collection.protocols), {'foo', 'bar'})

        self.assertRaises(RuntimeError, collection.add_adapter, DummyAdapter('bar'))

    def test_remove_adapter(self):
        collection = AdapterCollection(DummyAdapter('foo'))

        self.assertSetEqual(set(collection.protocols), {'foo'})
        self.assertRaises(RuntimeError, collection.remove_adapter, 'bar')

        assertRaisesNothing(self, collection.remove_adapter, 'foo')

        self.assertEqual(len(collection.protocols), 0)

    def test_connect_disconnect_connected(self):
        collection = AdapterCollection(
            DummyAdapter('foo', running=False), DummyAdapter('bar', running=False))

        # no arguments connects everything
        collection.connect()

        self.assertDictEqual(collection.is_connected(), {'bar': True, 'foo': True})
        self.assertTrue(collection.is_connected('bar'))
        self.assertTrue(collection.is_connected('foo'))

        collection.disconnect()

        self.assertDictEqual(collection.is_connected(), {'bar': False, 'foo': False})
        self.assertFalse(collection.is_connected('bar'))
        self.assertFalse(collection.is_connected('foo'))

        collection.connect('foo')
        self.assertDictEqual(collection.is_connected(), {'bar': False, 'foo': True})
        self.assertFalse(collection.is_connected('bar'))
        self.assertTrue(collection.is_connected('foo'))

        self.assertRaises(RuntimeError, collection.connect, 'baz')
        self.assertRaises(RuntimeError, collection.disconnect, 'baz')

    @patch.object(DummyAdapter, 'handle')
    @patch('lewis.core.adapters.sleep')
    def test_handle_calls_all_adapters_or_sleeps(self, sleep_mock, adapter_mock):
        collection = AdapterCollection(DummyAdapter('foo', running=False),
                                       DummyAdapter('bar', running=False))
        collection.handle(0.1)

        sleep_mock.assert_has_calls([call(0.05), call(0.05)])
        sleep_mock.reset_mock()

        collection.connect('foo')

        collection.handle(0.1)
        sleep_mock.assert_has_calls([call(0.05)])
        adapter_mock.assert_has_calls([call(0.05)])
