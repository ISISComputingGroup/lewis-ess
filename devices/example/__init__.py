from adapters.stream import StreamAdapter, Cmd
from devices import Device

class VerySimpleDevice(Device):
    param = 10


class VerySimpleAdapter(StreamAdapter):
    commands = {
        Cmd('get_param', '^P$'),
        Cmd('set_param', '^P=(.+)$'),
    }

    in_terminator = '\r\n'
    out_terminator = '\r\n'

    def get_param(self):
        return self._device.param

    def set_param(self, new_param):
        self._device.param = new_param

    def handle_error(self, request, error):
        return 'An error occurred: ' + repr(error)
