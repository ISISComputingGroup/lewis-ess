import unittest

from lewis.adapters.stream import StreamAdapter
from lewis.core.adapters import is_adapter, Adapter


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