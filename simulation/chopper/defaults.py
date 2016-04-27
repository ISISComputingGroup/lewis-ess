from simulation.core import State


class DefaultInitState(State):
    def on_entry(self, dt):
        self._context.shutdown_commanded = False


class DefaultParkingState(State):
    def in_state(self, dt):
        self._context.parking_position = self._context.target_parking_position

    def on_entry(self, dt):
        self._context.park_commanded = False


class DefaultParkedState(State):
    pass


class DefaultStoppingState(State):
    def in_state(self, dt):
        self._context.speed = 0.0

    def on_entry(self, dt):
        self._context.stop_commanded = False


class DefaultStoppedState(State):
    pass


class DefaultIdleState(State):
    def on_entry(self, dt):
        self._context.idle_commanded = False


class DefaultAcceleratingState(State):
    def in_state(self, dt):
        self._context.speed = self._context.target_speed

    def on_entry(self, dt):
        self._context.start_commanded = False


class DefaultPhaseLockingState(State):
    def in_state(self, dt):
        self._context.phase = self._context.target_phase

    def on_entry(self, dt):
        self._context.phase_commanded = False


class DefaultPhaseLockedState(State):
    pass
