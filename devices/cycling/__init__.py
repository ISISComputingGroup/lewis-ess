from core import State
from devices import StateMachineDevice
from adapters.stream import StreamAdapter, Cmd
from collections import OrderedDict

class CyclingStreamAdapter(StreamAdapter):
    commands = {
        Cmd('get_status', '^S$'),
        Cmd('get_speed', '^V$'),
        Cmd('get_ratio', '^R$'),
        Cmd('set_pedalling', r'^P=(True|False)$'),
        Cmd('set_breaking', r'^B=(True|False)$'),
        Cmd('set_up', '^U$'),
        Cmd('set_down', '^D$')
    }

    in_terminator = '\r\n'
    out_terminator = '\r\n'


def positive_speed(speed):
    return max(speed, 0)

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

class Stopped(State):

    def on_entry(self, dt):
        print('stopped')

class Pedalling(State):

    def on_entry(self, dt):
        print('pedalling')
        self._context.breaking = False

    def in_state(self, dt):
        # TODO this could get quite complex as the gear ratio, gradient etc all play a part.
        new_speed = self._context._speed + (dt/1000 * self._context._gear_ratio)
        self._context._speed = positive_speed(new_speed)

    def on_exit(self, dt):
        print('not pedalling')


class Coasting(State):
    def on_entry(self, dt):
        print('coasting')

    def in_state(self, dt):

        new_speed = self._context._speed - (dt/1000)
        self._context._speed = positive_speed(new_speed)


class ChangeUp(State):
    def on_entry(self, dt):
        print('change up')
        self._context._gear_ratio += 0.1

    def on_exit(self, dt):

        self._context.change_up = False


class ChangeDown(State):
    def on_entry(self, dt):
        print('change down')
        self._context._gear_ratio -= 0.1

    def on_exit(self, dt):
        self._context.change_down = False


class Break(State):

    def on_entry(self, dt):
        print('breaking')
        self._context.pedalling = False

    def in_state(self, dt):
        new_speed = self._context._speed
        new_speed -= dt/100
        self._context._speed = positive_speed(new_speed)


class Cycling(StateMachineDevice):


    def _initialize_data(self):
        print('initialize')
        self._speed = 0.0
        self._gear_ratio = 1.0
        self.pedalling = False
        self.change_up = False
        self.change_down = False
        self.breaking = False

    def _get_state_handlers(self):
        return {
            'stopped': Stopped(),
            'pedalling': Pedalling(),
            'coasting': Coasting(),
            'up' : ChangeUp(),
            'down' : ChangeDown(),
            'break' : Break()
        }

    def _get_transition_handlers(self):
        return OrderedDict([
            (('stopped', 'pedalling'), lambda: self.pedalling),
            (('pedalling', 'coasting'), lambda: not self.pedalling),
            (('pedalling', 'up'), lambda : self.change_up),
            (('pedalling', 'down'), lambda : self.change_down),
            (('coasting', 'pedalling'), lambda: self.pedalling),
            (('coasting', 'stopped'), lambda : self._speed == 0),
            (('up', 'pedalling'), lambda: True),
            (('down', 'pedalling'), lambda: True),
            (('pedalling', 'break'), lambda: self.breaking),
            (('coasting', 'break'), lambda: self.breaking),
            (('break', 'coasting'), lambda: not self.breaking),
            (('break', 'stopped'), lambda: self._speed == 0),
        ])

    def _get_initial_state(self):
        return 'stopped'


    def get_speed(self):
        return self._speed

    def get_ratio(self):
        return self._gear_ratio

    def set_pedalling(self, pedalling):
        self.pedalling = str2bool(pedalling)

    def set_breaking(self, breaking):
        self.breaking = str2bool(breaking)


    def set_up(self):
        self.change_up = True

    def set_down(self):
        self.change_down = True


    def get_status(self):
        return self._csm.state

