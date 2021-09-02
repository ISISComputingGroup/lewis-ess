import unittest
from lewis.adapters.stream import StreamHandler
from mock import patch, MagicMock
from parameterized import parameterized


@patch("asynchat.async_chat")
class TestStreamHandler(unittest.TestCase):
    def setUp(self):
        self.target = MagicMock()
        self.handler = StreamHandler(MagicMock(), self.target, MagicMock)

    @parameterized.expand([(b"\n", "test", b"test\n"),
                           (b"\n", b"test", b"test\n"),
                           ("\n", "test", b"test\n"),
                           ("\n", "test", b"test\n")])
    @patch("asynchat.async_chat.push")
    def test_terminator_and_replies_of_different_types_can_be_concatenated(self, terminator, message, expected, async_push, _):
        self.target.out_terminator = terminator
        self.handler.unsolicited_reply(message)
        self.assertEqual(expected, async_push.call_args[0][0])
