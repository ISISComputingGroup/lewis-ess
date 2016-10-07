from core import CanProcessComposite, StateMachine, State
from collections import OrderedDict
from adapters.stream import StreamAdapter, Cmd


class LinearAxisSimulationStreamAdapter(StreamAdapter):
    commands = {
        Cmd('get_status', '^S$'),
        Cmd('get_position', '^P$'),
        Cmd('set_position', r'^P=([-+]?[0-9]*\.?[0-9]+)'),
        Cmd('get_speed', '^V$'),
        Cmd('set_speed', r'^V=([-+]?[0-9]*\.?[0-9]+.)'),
        Cmd('stop', '^H$')
    }

    in_terminator = '\r\n'
    out_terminator = '\r\n'


class MovingState(State):
    def in_state(self, dt):
        sign = (self._context.target > self._context.position) - (self._context.target < self._context.position)

        if not sign:
            return

        self._context.position += sign * self._context.speed * dt

        if sign * self._context.position > sign * self._context.target:
            self._context.position = self._context.target

        print(self._context.position)


class LinearAxisSimulation(CanProcessComposite):
    def __init__(self):
        super(LinearAxisSimulation, self).__init__()

        self.position = 0.0
        self.target = 0.0
        self._pos_lolim = -100.0
        self._pos_hilim = 100.0

        self.speed = 1.0
        self._speed_lolim = 0.1
        self._speed_hilim = 10.0

        state_handlers = {
            'idle': State(),
            'moving': MovingState()
        }

        transition_handlers = OrderedDict([
            (('idle', 'moving'), lambda: self.position != self.target),
            (('moving', 'idle'), lambda: self.position == self.target)
        ])

        self._csm = StateMachine({
            'initial': 'idle',
            'states': state_handlers,
            'transitions': transition_handlers
        }, context=self)

        self.addProcessor(self._csm)

    def get_status(self):
        return self._csm.state

    def get_position(self):
        return self.position

    def set_position(self, raw_position):
        if self._csm.state == 'moving':
            raise RuntimeError('New target can only be set in idle state.')

        new_position = float(raw_position)

        if not (self._pos_lolim <= new_position <= self._pos_hilim):
            raise ValueError('New position is not within limits ({}, {})'.format(self._pos_lolim, self._pos_hilim))

        self.target = new_position

    def get_speed(self):
        return self.speed

    def set_speed(self, raw_speed):
        if self._csm.state == 'moving':
            raise RuntimeError('Speed can only be changed in idle state.')

        new_speed = float(raw_speed)

        if not (self._speed_lolim <= new_speed <= self._speed_hilim):
            raise ValueError(
                'New position is not within limits ({}, {})'.format(self._speed_lolim, self._speed_hilim))

        self.speed = new_speed

    def stop(self):
        self.target = self.position

    def handle_error(self, request, error):
        return error.message
