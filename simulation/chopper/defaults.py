from simulation.core import State


class DefaultInitState(State):
    def on_entry(self, dt):
        self._context.setInitialState()


class DefaultParkingState(State):
    def __init__(self, parking_speed=5.0):
        super(DefaultParkingState, self).__init__()
        self._parking_speed = parking_speed

    def in_state(self, dt):
        sign = (self._context.target_parking_position - self._context.parking_position)

        if sign == 0.0:
            return

        sign = sign / abs(sign)
        self._context.parking_position += sign * self._parking_speed * dt

        if sign * self._context.parking_position > sign * self._context.target_parking_position:
            self._context.parking_position = self._context.target_parking_position

    def on_entry(self, dt):
        self._context.park_commanded = False


class DefaultParkedState(State):
    pass


class DefaultStoppingState(State):
    def __init__(self, acceleration=5.0):
        super(DefaultStoppingState, self).__init__()
        self._acceleration = acceleration

    def in_state(self, dt):
        self._context.speed -= self._acceleration * dt

        if self._context.speed < 0:
            self._context.speed = 0.0

    def on_entry(self, dt):
        self._context.stop_commanded = False


class DefaultStoppedState(State):
    pass


class DefaultIdleState(State):
    def __init__(self, acceleration=.05):
        super(DefaultIdleState, self).__init__()
        self._acceleration = acceleration

    def in_state(self, dt):
        self._context.speed -= self._acceleration * dt

        if self._context.speed < 0:
            self._context.speed = 0.0

    def on_entry(self, dt):
        self._context.idle_commanded = False


class DefaultAcceleratingState(State):
    def __init__(self, acceleration=5.0):
        super(DefaultAcceleratingState, self).__init__()
        self._acceleration = acceleration

    def in_state(self, dt):
        sign = (self._context.target_speed - self._context.speed)

        if sign == 0.0:
            return

        sign = sign / abs(sign)
        self._context.speed += sign * self._acceleration * dt

        if sign * self._context.speed > sign * self._context.target_speed:
            self._context.speed = self._context.target_speed

    def on_entry(self, dt):
        self._context.start_commanded = False


class DefaultPhaseLockingState(State):
    def __init__(self, phase_locking_speed=5.0):
        super(DefaultPhaseLockingState, self).__init__()
        self._phase_locking_speed = phase_locking_speed

    def in_state(self, dt):
        sign = (self._context.target_phase - self._context.phase)

        if sign == 0.0:
            return

        sign = sign / abs(sign)

        self._context.phase += sign * self._phase_locking_speed * dt

        if sign * self._context.phase > sign * self._context.target_phase:
            self._context.phase = self._context.target_phase

    def on_entry(self, dt):
        self._context.phase_commanded = False


class DefaultPhaseLockedState(State):
    pass
