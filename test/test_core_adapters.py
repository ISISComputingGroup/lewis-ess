import inspect
import unittest

from mock import patch, call, Mock, MagicMock

from lewis.core.adapters import Adapter, AdapterCollection
from lewis.core.exceptions import LewisException
from . import assertRaisesNothing


class DummyAdapter(Adapter):
    """
    A dummy adapter for tests.
    """

    default_options = {
        'foo': True,
        'bar': False,
    }

    def __init__(self, protocol, running=False, options=None):
        super(DummyAdapter, self).__init__(options)
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

    def test_not_implemented_errors(self):
        adapter = Adapter()

        self.assertRaises(NotImplementedError, adapter.start_server)
        self.assertRaises(NotImplementedError, adapter.stop_server)
        self.assertRaises(NotImplementedError, getattr, adapter, 'is_running')
        assertRaisesNothing(self, adapter.handle, 0)

    def test_device_property(self):
        adapter = Adapter()
        mock_device = Mock()

        # Make sure that the default implementation works (for adapters that do
        # not have binding behavior).
        adapter.device = mock_device
        self.assertEqual(adapter.device, mock_device)

        with patch('lewis.core.adapters.Adapter._bind_device') as bind_mock:
            adapter.device = None

            bind_mock.assert_called_once()
            self.assertEqual(adapter.device, None)

    def test_options(self):
        assertRaisesNothing(self, DummyAdapter, 'protocol', options={'bar': 2, 'foo': 3})
        self.assertRaises(LewisException, DummyAdapter, 'protocol', options={'invalid': False})


class TestAdapterCollection(unittest.TestCase):
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

    def test_set_device(self):
        mock_adapter1 = MagicMock()
        mock_adapter2 = MagicMock()

        collection = AdapterCollection(mock_adapter1, mock_adapter2)
        collection.device = 'foo'

        self.assertEqual(mock_adapter1.device, 'foo')
        self.assertEqual(mock_adapter2.device, 'foo')

        mock_adapter3 = MagicMock()
        mock_adapter3.device = 'other'

        collection.add_adapter(mock_adapter3)

        self.assertEqual(mock_adapter3.device, 'foo')
        collection.device = None

        self.assertEqual(mock_adapter1.device, None)

        mock_adapter4 = MagicMock()
        mock_adapter4.device = 'bar'

        collection.add_adapter(mock_adapter4)

        self.assertEqual(mock_adapter1.device, 'bar')

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

    def test_configuration(self):
        collection = AdapterCollection(
            DummyAdapter('protocol_a', options={'bar': 2, 'foo': 3}),
            DummyAdapter('protocol_b', options={'bar': True, 'foo': False}))

        self.assertDictEqual(collection.configuration(),
                             {
                                 'protocol_a': {'bar': 2, 'foo': 3},
                                 'protocol_b': {'bar': True,
                                                'foo': False}
                             })

        self.assertDictEqual(collection.configuration('protocol_a'),
                             {
                                 'protocol_a': {'bar': 2, 'foo': 3},
                             })

        self.assertDictEqual(collection.configuration('protocol_b'),
                             {
                                 'protocol_b': {'bar': True, 'foo': False},
                             })
