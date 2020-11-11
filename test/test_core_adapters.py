import inspect
import unittest

from mock import MagicMock, Mock

from lewis.core.adapters import Adapter, AdapterCollection, NoLock
from lewis.core.exceptions import LewisException

from .utils import assertRaisesNothing


class DummyAdapter(Adapter):
    """
    A dummy adapter for tests.
    """

    default_options = {
        "foo": True,
        "bar": False,
    }

    def __init__(self, protocol, running=False, options=None):
        super(DummyAdapter, self).__init__(options)
        self._protocol = protocol
        self._running = running

    @property
    def protocol(self):
        return self._protocol

    def start_server(self):
        self._running = True

    def stop_server(self):
        self._running = False

    @property
    def is_running(self):
        return self._running


class TestNoLock(unittest.TestCase):
    def test_raises_when_used(self):
        def failing_function():
            with NoLock():
                pass

        self.assertRaises(RuntimeError, failing_function)


class TestAdapter(unittest.TestCase):
    def test_documentation(self):
        adapter = DummyAdapter("foo")

        self.assertEqual(inspect.cleandoc(adapter.__doc__), adapter.documentation)

    def test_not_implemented_errors(self):
        adapter = Adapter()

        self.assertRaises(NotImplementedError, adapter.start_server)
        self.assertRaises(NotImplementedError, adapter.stop_server)
        self.assertRaises(NotImplementedError, getattr, adapter, "is_running")
        assertRaisesNothing(self, adapter.handle, 0)

    def test_interface_property(self):
        adapter = Adapter()
        mock_interface = Mock()

        # Make sure that the default implementation works (for adapters that do
        # not have binding behavior).
        adapter.interface = mock_interface
        self.assertEqual(adapter.interface, mock_interface)

    def test_protocol_is_forwarded_from_interface(self):
        adapter = Adapter()

        adapter.interface = None
        self.assertEqual(adapter.protocol, None)

        mock_interface = MagicMock()
        mock_interface.protocol = "foo"

        adapter.interface = mock_interface

        self.assertEqual(adapter.protocol, "foo")

    def test_options(self):
        assertRaisesNothing(
            self, DummyAdapter, "protocol", options={"bar": 2, "foo": 3}
        )
        self.assertRaises(
            LewisException, DummyAdapter, "protocol", options={"invalid": False}
        )


class TestAdapterCollection(unittest.TestCase):
    def test_add_adapter(self):
        collection = AdapterCollection()
        self.assertEqual(len(collection.protocols), 0)

        assertRaisesNothing(self, collection.add_adapter, DummyAdapter("foo"))

        self.assertEqual(len(collection.protocols), 1)
        self.assertSetEqual(set(collection.protocols), {"foo"})

        assertRaisesNothing(self, collection.add_adapter, DummyAdapter("bar"))

        self.assertEqual(len(collection.protocols), 2)
        self.assertSetEqual(set(collection.protocols), {"foo", "bar"})

        self.assertRaises(RuntimeError, collection.add_adapter, DummyAdapter("bar"))

    def test_remove_adapter(self):
        collection = AdapterCollection(DummyAdapter("foo"))

        self.assertSetEqual(set(collection.protocols), {"foo"})
        self.assertRaises(RuntimeError, collection.remove_adapter, "bar")

        assertRaisesNothing(self, collection.remove_adapter, "foo")

        self.assertEqual(len(collection.protocols), 0)

    def test_connect_disconnect_connected(self):
        collection = AdapterCollection(
            DummyAdapter("foo", running=False), DummyAdapter("bar", running=False)
        )

        # no arguments connects everything
        collection.connect()

        self.assertDictEqual(collection.is_connected(), {"bar": True, "foo": True})
        self.assertTrue(collection.is_connected("bar"))
        self.assertTrue(collection.is_connected("foo"))

        collection.disconnect()

        self.assertDictEqual(collection.is_connected(), {"bar": False, "foo": False})
        self.assertFalse(collection.is_connected("bar"))
        self.assertFalse(collection.is_connected("foo"))

        collection.connect("foo")
        self.assertDictEqual(collection.is_connected(), {"bar": False, "foo": True})
        self.assertFalse(collection.is_connected("bar"))
        self.assertTrue(collection.is_connected("foo"))

        self.assertRaises(RuntimeError, collection.connect, "baz")
        self.assertRaises(RuntimeError, collection.disconnect, "baz")

        collection.disconnect()  # Clean up so that the test does not hang

    def test_configuration(self):
        collection = AdapterCollection(
            DummyAdapter("protocol_a", options={"bar": 2, "foo": 3}),
            DummyAdapter("protocol_b", options={"bar": True, "foo": False}),
        )

        self.assertDictEqual(
            collection.configuration(),
            {
                "protocol_a": {"bar": 2, "foo": 3},
                "protocol_b": {"bar": True, "foo": False},
            },
        )

        self.assertDictEqual(
            collection.configuration("protocol_a"),
            {
                "protocol_a": {"bar": 2, "foo": 3},
            },
        )

        self.assertDictEqual(
            collection.configuration("protocol_b"),
            {
                "protocol_b": {"bar": True, "foo": False},
            },
        )

    def test_set_device(self):
        adapter = DummyAdapter(protocol="foo")
        adapter.interface = MagicMock()

        collection = AdapterCollection(adapter)
        collection.set_device("test")

        self.assertEqual(adapter.interface.device, "test")
