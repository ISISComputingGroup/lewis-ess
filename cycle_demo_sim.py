from simulation import StateMachine
from simulation import CanProcessComposite


class SimpleChopper(CanProcessComposite, object):
    def print_status(self):
        pass

    def __init__(self):
        super(SimpleChopper, self).__init__()

        self._csm = StateMachine({
            'initial': 'off',
            'transitions': [
                # From State, To State, Condition Function
                ('off', 'bearings', lambda: self.power_switch),

                ('parked', 'off', lambda: not self.power_switch),
                ('parked', 'idle', lambda: self.bearings_ready),

                ('idle', 'off', lambda: not self.power_switch),
                ('idle', 'adjust_speed', self._check_target_speed_changed),
                ('idle', 'stopping', self._check_target_speed_zero),

                ('adjust_speed', 'speed_locked', self._check_target_speed_reached),
                ('adjust_speed', 'stopping', self._check_target_speed_zero),

                ('speed_locked', 'adjust_speed', self._check_target_speed_changed),
                ('speed_locked', 'stopping', self._check_target_speed_zero),
                ('speed_locked', 'idle', lambda: not self._speed_locked),

                ('stopping', 'idle', lambda: self.speed == 0),
            ]
        })
        self._csm.bind_handlers_by_name(self)

        self.addProcessor(self._csm)

        self._init_vars()

    def _init_vars(self):
        # Properties
        self._power_switch = False
        self._bearings_ready = False
        self._speed = 0
        self._speed_target = 0
        self._speed_locked = False
        self._command_issued = False

        # Internal
        self._timer_bearings = 0

    # Properties and functions that the client can access
    @property
    def power_switch(self):
        return self._power_switch

    @power_switch.setter
    def power_switch(self, value):
        self._power_switch = True if value else False

    @property
    def bearings_ready(self):
        return self._bearings_ready

    @property
    def speed(self):
        return self._speed

    @property
    def state(self):
        return self._csm.state

    @property
    def speed_locked(self):
        return self._speed_locked

    def unlock(self):
        self._speed_locked = False

    def speed_command(self, speed):
        self._speed_target = speed
        self._command_issued = True

    # Condition Functions (StateMachine calls these by name, based on init settings)
    def _check_target_speed_changed(self):
        return self._speed_target != self._speed and \
               self._speed_target != 0 and \
               self._command_issued

    def _check_target_speed_reached(self):
        return self._speed_target == self._speed and \
               self._speed_target != 0

    def _check_target_speed_zero(self):
        return self._speed_target == 0 and \
               self._speed != 0 and \
               self._command_issued

    # State Handlers (StateMachine calls these by name if defined, based on state names)
    def _on_entry_off(self, dt):
        self._init_vars()

    def _on_exit_off(self, dt):
        print "Hello World! Initializing bearings!"
        self._timer_bearings = 3.0

    def _in_state_parked(self, dt):
        if self._timer_bearings > 0:
            self._timer_bearings -= dt

        if self._timer_bearings <= 0:
            self._bearings_ready = True  # Will trigger transition on next cycle

    def _on_exit_parked(self, dt):
        print "Bearings initialized, ready to go!"

    def _in_state_idle(self, dt):
        # Decelerate gradually if we're still spinning
        if self._speed < 0.1:
            self._speed = 0
        else:
            self._speed -= ((self._speed / 8.0) * dt)

    def _on_entry_adjust_speed(self, dt):
        # We've processed a command by coming here
        self._command_issued = False

    def _in_state_adjust_speed(self, dt):
        # Approach target speed, rate based on dt
        if abs(self._speed - self._speed_target) < 0.1:
            self._speed = self._speed_target
        else:
            self._speed += ((self._speed_target - self._speed) / (3.0 / dt))

    def _on_entry_speed_locked(self, dt):
        # Notice there's an exit condition from Speed_Locked to Idle based on _speed_locked == False
        # But this will not be checked until the next cycle, so setting it True here works fine
        self._speed_locked = True

    def _on_exit_speed_locked(self, dt):
        # Similarly to above, this doesn't hurt since we're already leaving this state
        self._speed_locked = False

    def _on_entry_stopping(self, dt):
        # We've processed a command by coming here
        self._command_issued = False

    def _in_state_stopping(self, dt):
        # Decelerate quickly based on dt
        if self._speed < 0.1:
            self._speed = 0
        else:
            self._speed -= ((self._speed / 3.0) * dt)
