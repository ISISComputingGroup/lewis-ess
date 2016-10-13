from devices import StateMachineDevice
from adapters.stream import StreamAdapter, Cmd

from core.statemachine import State
from core import approaches

from collections import OrderedDict


class DefaultMovingState(State):
    def in_state(self, dt):
        self._context.position = approaches.linear(self._context.position, self._context.target,
                                                   self._context.speed, dt)


class SimulatedExampleMotor(StateMachineDevice):
    def _initialize_data(self):
        self.position = 0.0
        self._target = 0.0
        self.speed = 2.0

    def _get_state_handlers(self):
        return {
            'idle': State(),
            'moving': DefaultMovingState()
        }

    def _get_initial_state(self):
        return 'idle'

    def _get_transition_handlers(self):
        return OrderedDict([
            (('idle', 'moving'), lambda: self.position != self.target),
            (('moving', 'idle'), lambda: self.position == self.target)])

    @property
    def state(self):
        return self._csm.state

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, new_target):
        if self.state == 'moving':
            raise RuntimeError('Can not set new target while moving.')

        if not (0 <= new_target <= 250):
            raise ValueError('Target is out of range [0, 250]')

        self._target = new_target

    def stop(self):
        self._target = self.position

        return self.target, self.position


class ExampleMotorStreamInterface(StreamAdapter):
    commands = {
        Cmd('get_status', r'^S\?$'),
        Cmd('get_position', r'^P\?$'),
        Cmd('get_target', r'^T\?$'),
        Cmd('set_target', r'^T=([+-]?\d+)', argument_mappings=(float,)),
        Cmd('stop', r'^H$',
            return_mapping=lambda x: 'T={},P={}'.format(x[0], x[1])),
    }

    in_terminator = '\r\n'
    out_terminator = '\r\n'

    def get_status(self):
        return self._device.state

    def get_position(self):
        return self._device.position

    def get_target(self):
        return self._device.target

    def set_target(self, new_target):
        try:
            self._device.target = new_target
            return 'T={}'.format(new_target)
        except RuntimeError:
            return 'err: not idle'
        except ValueError:
            return 'err: not 0<=T<=250'


setups = dict(
    moving=dict(
        device_type=SimulatedExampleMotor,
        parameters=dict(
            override_initial_state='moving',
            override_initial_data=dict(
                _target=120.0,position=20.0
            )
        )
    )
)
