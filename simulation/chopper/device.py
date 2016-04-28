from collections import OrderedDict
from simulation.core import StateMachine, CanProcessComposite, CanProcess, Context
from bearings import MagneticBearings
from defaults import *


class SimulatedBearings(CanProcess, MagneticBearings):
    def __init__(self):
        super(SimulatedBearings, self).__init__()

        self._csm = StateMachine({
            'initial': 'resting',

            'transitions': {
                ('resting', 'levitating'): lambda: self._levitate,
                ('levitating', 'levitated'): self.levitationComplete,
                ('levitated', 'delevitating'): lambda: not self._levitate,
                ('delevitating', 'resting'): self.delevitationComplete,
            }
        })

        self._levitate = False

    def engage(self):
        self.levitate()

    def disengage(self):
        self.delevitate()

    def levitate(self):
        self._levitate = True

    def delevitate(self):
        self._levitate = False

    def levitationComplete(self):
        return True

    def delevitationComplete(self):
        return True

    def doProcess(self, dt):
        self._csm.process(dt)

    @property
    def ready(self):
        return self._csm.state == 'levitated' and self._levitate

    @property
    def idle(self):
        return self._csm.state == 'resting' and not self._levitate


class ChopperContext(Context):
    def setInitialState(self):
        self.speed = 0.0
        self.target_speed = 0.0

        self.phase = 0.0
        self.target_phase = 0.0

        self.parking_position = 0.0
        self.target_parking_position = 0.0

        self.park_commanded = False
        self.stop_commanded = False
        self.start_commanded = False
        self.idle_commanded = False
        self.phase_commanded = False
        self.shutdown_commanded = False
        self.interlocked = False


class SimulatedChopper(CanProcessComposite, object):
    def print_status(self):
        pass

    def __init__(self, override_states=None, override_transitions=None):
        super(SimulatedChopper, self).__init__()

        self._bearings = SimulatedBearings()

        self._context = ChopperContext()

        state_handlers = {
            'init': DefaultInitState(),
            'bearings': {'in_state': self._bearings},
            'stopped': DefaultStoppedState(),
            'stopping': DefaultStoppingState(),
            'accelerating': DefaultAcceleratingState(),
            'phase_locking': DefaultPhaseLockingState(),
            'phase_locked': DefaultPhaseLockedState(),
            'idle': DefaultIdleState(),
            'parking': DefaultParkingState(),
            'parked': DefaultParkedState(),
        }

        if override_states is not None:
            state_handlers.update(override_states)

        transition_handlers = OrderedDict([
            (('init', 'bearings'), lambda: self._context.interlocked),
            (('bearings', 'stopped'), lambda: self._bearings.ready),
            (('bearings', 'init'), lambda: self._bearings.idle),

            (('parking', 'parked'), lambda: self._context.parking_position == self._context.target_parking_position),
            (('parking', 'stopping'), lambda: self._context.stop_commanded),

            (('parked', 'stopping'), lambda: self._context.stop_commanded),
            (('parked', 'accelerating'), lambda: self._context.start_commanded),

            (('stopped', 'accelerating'), lambda: self._context.start_commanded),
            (('stopped', 'parking'), lambda: self._context.park_commanded),
            (('stopped', 'bearings'), lambda: self._context.shutdown_commanded),

            (('accelerating', 'stopping'), lambda: self._context.stop_commanded),
            (('accelerating', 'idle'), lambda: self._context.idle_commanded),
            (('accelerating', 'phase_locking'), lambda: self._context.speed == self._context.target_speed),

            (('idle', 'accelerating'), lambda: self._context.start_commanded),
            (('idle', 'stopping'), lambda: self._context.stop_commanded),

            (('phase_locking', 'stopping'), lambda: self._context.stop_commanded),
            (('phase_locking', 'phase_locked'), lambda: self._context.phase == self._context.target_phase),
            (('phase_locking', 'idle'), lambda: self._context.idle_commanded),

            (('phase_locked', 'accelerating'), lambda: self._context.start_commanded),
            (('phase_locked', 'phase_locking'), lambda: self._context.phase_commanded),
            (('phase_locked', 'stopping'), lambda: self._context.stop_commanded),
            (('phase_locked', 'idle'), lambda: self._context.idle_commanded),

            (('stopping', 'accelerating'), lambda: self._context.start_commanded),
            (('stopping', 'stopped'), lambda: self._context.speed == 0.0),
            (('stopping', 'idle'), lambda: self._context.idle_commanded),
        ])

        if override_transitions is not None:
            transition_handlers.update(override_transitions)

        self._csm = StateMachine({
            'initial': 'init',
            'states': state_handlers,
            'transitions': transition_handlers,
        }, context=self._context)
        self._csm.bind_handlers_by_name(self)

        self.addProcessor(self._csm)

    @property
    def state(self):
        return self._csm.state

    @property
    def interlocked(self):
        return self._context.interlocked

    def interlock(self):
        self._context.interlocked = True
        self._bearings.engage()

    def release(self):
        self._context.shutdown_commanded = True
        self._bearings.disengage()

    def park(self):
        self._context.park_commanded = True

    @property
    def parked(self):
        return self._csm.state == 'parked'

    # Stopping stuff
    def stop(self):
        self._context.stop_commanded = True

    @property
    def stopped(self):
        return self._csm.state == 'stopped'

    # Accelerating stuff
    def start(self):
        self._context.start_commanded = True

    @property
    def started(self):
        return self._csm.state == 'accelerating'

    # Idle stuff
    def unlock(self):
        self._context.idle_commanded = True

    @property
    def idle(self):
        return self._csm.state == 'idle'

    # Phase locking stuff
    def lockPhase(self):
        self._context.phase_commanded = True

    @property
    def phaseLocked(self):
        return self._csm.state == 'phase_locked'

    # Setpoints etc.
    @property
    def speed(self):
        return self._context.speed

    @property
    def targetSpeed(self):
        return self._context.target_speed

    @targetSpeed.setter
    def targetSpeed(self, new_target_speed):
        self._context.target_speed = new_target_speed

    @property
    def phase(self):
        return self._context.phase

    @property
    def targetPhase(self):
        return self._context.target_phase

    @targetPhase.setter
    def targetPhase(self, new_target_phase):
        self._context.target_phase = new_target_phase

    @property
    def parkingPosition(self):
        return self._context.parking_position

    @property
    def targetParkingPosition(self):
        return self._context.target_parking_position

    @targetParkingPosition.setter
    def targetParkingPosition(self, new_target_parking_position):
        self._context.target_parking_position = new_target_parking_position
