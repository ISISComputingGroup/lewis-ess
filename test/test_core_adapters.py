import unittest

from mock import patch, call
import inspect

from lewis.adapters.stream import StreamAdapter
from lewis.core.adapters import is_adapter, Adapter, AdapterContainer
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
        class DummyAdapter(Adapter):
            pass

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
        container = AdapterContainer()
        self.assertEquals(len(container.protocols), 0)

        assertRaisesNothing(self, container.add_adapter, DummyAdapter('foo'))

        self.assertEqual(len(container.protocols), 1)
        self.assertSetEqual(set(container.protocols), {'foo'})

        assertRaisesNothing(self, container.add_adapter, DummyAdapter('bar'))

        self.assertEqual(len(container.protocols), 2)
        self.assertSetEqual(set(container.protocols), {'foo', 'bar'})

        self.assertRaises(RuntimeError, container.add_adapter, DummyAdapter('bar'))

    def test_remove_adapter(self):
        container = AdapterContainer(DummyAdapter('foo'))

        self.assertSetEqual(set(container.protocols), {'foo'})
        self.assertRaises(RuntimeError, container.remove_adapter, 'bar')

        assertRaisesNothing(self, container.remove_adapter, 'foo')

        self.assertEqual(len(container.protocols), 0)

    def test_connect_disconnect_connected(self):
        container = AdapterContainer(
            DummyAdapter('foo', running=False), DummyAdapter('bar', running=False))

        # no arguments connects everything
        container.connect()

        self.assertDictEqual(container.is_connected(), {'bar': True, 'foo': True})
        self.assertTrue(container.is_connected('bar'))
        self.assertTrue(container.is_connected('foo'))

        container.disconnect()

        self.assertDictEqual(container.is_connected(), {'bar': False, 'foo': False})
        self.assertFalse(container.is_connected('bar'))
        self.assertFalse(container.is_connected('foo'))

        container.connect('foo')
        self.assertDictEqual(container.is_connected(), {'bar': False, 'foo': True})
        self.assertFalse(container.is_connected('bar'))
        self.assertTrue(container.is_connected('foo'))

        self.assertRaises(RuntimeError, container.connect, 'baz')
        self.assertRaises(RuntimeError, container.disconnect, 'baz')

    @patch.object(DummyAdapter, 'handle')
    @patch('lewis.core.adapters.sleep')
    def test_handle_calls_all_adapters_or_sleeps(self, sleep_mock, adapter_mock):
        container = AdapterContainer(DummyAdapter('foo', running=False),
                                     DummyAdapter('bar', running=False))
        container.handle(0.1)

        sleep_mock.assert_has_calls([call(0.1), call(0.1)])
        sleep_mock.reset_mock()

        container.connect('foo')

        container.handle(0.1)
        sleep_mock.assert_has_calls([call(0.1)])
        adapter_mock.assert_has_calls([call(0.1)])
