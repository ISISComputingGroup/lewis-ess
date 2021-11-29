import unittest

from mock import MagicMock, patch
from parameterized import parameterized

from lewis.adapters.stream import StreamHandler


@patch("asynchat.async_chat")
class TestStreamHandler(unittest.TestCase):
    def setUp(self):
        """Create a mock for the async_chat class"""
        self.target = MagicMock()
        self.stream_server = MagicMock()
        self.socket = MagicMock()
        self.handler = StreamHandler(self.socket, self.target, self.stream_server)

    @parameterized.expand(
        [
            (b"\n", "test", b"test\n"),
            (b"\n", b"test", b"test\n"),
            ("\n", "test", b"test\n"),
            ("\n", "test", b"test\n"),
        ]
    )
    @patch("asynchat.async_chat.push")
    def test_terminator_and_replies_of_different_types_can_be_concatenated(
        self, terminator, message, expected, async_push, _
    ):
        self.target.out_terminator = terminator
        self.handler.unsolicited_reply(message)

        self.assertEqual(expected, async_push.call_args[0][0])
