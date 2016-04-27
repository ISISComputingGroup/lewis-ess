from simulation import StateMachine
from simulation import CanProcessComposite, CanProcess
from components import MagneticBearings


class SimulatedBearings(CanProcess, MagneticBearings):
    def __init__(self):
        super(SimulatedBearings, self).__init__()

        self._csm = StateMachine({
            'initial': 'resting',

            'transitions': [
                ('resting', 'levitating', lambda: self._levitate),
                ('levitating', 'levitated', self.levitationComplete),
                ('levitated', 'delevitating', lambda: not self._levitate),
                ('delevitating', 'resting', self.delevitationComplete),
            ]
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


from abc import abstractproperty, abstractmethod


class Parkable(object):
    def __init__(self):
        super(Parkable, self).__init__()
        self.__in_progress = False

    def park(self):
        if self.canPark():
            self.__in_progress = True

            if hasattr(self, 'doPark'):
                self.doPark()

    @abstractmethod
    def canPark(self):
        return self._csm.can('stopped')

    def doPark(self):
        self._csm.start()

    @abstractproperty
    def parked(self):
        pass

    def __call__(self):

    @abstractmethod
    def parkingComplete(self):
        pass

    def _setParkingComplete(self):
        self.__in_progress = False


class Command(object):
    def __init__(self):
        self._triggered = False

    def canTrigger(self):
        pass

    def doTrigger(self):
        pass

    @property
    def triggered(self):
        return caget('state') == 'parking'

    def trigger(self):
        if self.canTrigger():
            self._triggered = True

            self.doTrigger()

    def reset(self):
        self._triggered = False

class Accelerating(object):
    def __init__(self, obj):
        self._obj = obj

    def on_entry(self, dt):
        pass

    def in_state(self, dt):
        pass

    def on_exit(self, dt):
        pass

    def is_complete(self):
        if isinstance(self._obj, 'HasSpeed'):
            self._obj.speed == self._obj.speed_setpoint

        return True

class Idle(object):
    def in_state(self, dt):
        pass

    def is_complete(self):
        return True



class SimulatedChopper(CanProcessComposite, object):
    def print_status(self):
        pass

    def __init__(self, beschleuniger):
        super(SimulatedChopper, self).__init__()

        self._bearings = SimulatedBearings()
        self._interlocked = False
        self._in_shutdown = False

        self.parking = Command()

        self._in_parking = False
        self._in_stopping = False
        self._in_starting = False
        self._in_idling = False
        self._in_locking = False

        self._csm = StateMachine({
            'initial': 'init',

            'states': {
                'bearings': {'in_state': self._bearings},
                'parking': {'on_exit': self.parking.reset},
                'accelerating': {'in_state': self._doStartingSimulation, 'on_exit': self._setStartingComplete},
                'idle': {'on_entry': self._setIdlingComplete},
                'phase_locking': {'on_exit': self._setPhaseLockingComplete},
                'stopping': {'on_exit': self._setStoppingComplete},
            },

            'transitions': [
                # From State, To State, Condition Function
                ('init', 'bearings', lambda: self.interlocked),
                ('bearings', 'stopped', lambda: self._bearings.ready),
                ('stopped', 'bearings', lambda: self._in_shutdown),
                ('bearings', 'init', lambda: self._bearings.idle),

                ('stopped', 'parking', lambda: self.parking.triggered and not self._parking_failure),
                ('parking', 'parked', self.parkingComplete),

                ('stopped', 'accelerating', lambda: self._in_starting),
                ('accelerating', 'phase_locking', self.startingComplete),
                ('accelerating', 'idle', lambda: self._in_idling),
                ('idle', 'accelerating', lambda: self._in_starting),
                ('phase_locking', 'phase_locked', self.phaseLockingComplete),
                ('phase_locked', 'accelerating', lambda: self._in_starting),
                ('phase_locked', 'phase_locking', lambda: self._in_locking),

                ('phase_locked', 'stopping', lambda: self._in_stopping),
                ('phase_locking', 'stopping', lambda: self._in_stopping),
                ('accelerating', 'stopping', lambda: self._in_stopping),
                ('parking', 'stopping', lambda: self._in_stopping),
                ('parked', 'stopping', lambda: self._in_stopping),
                ('idle', 'stopping', lambda: self._in_stopping),

                ('stopping', 'accelerating', lambda: self._in_starting),
                ('stopping', 'stopped', self.stoppingComplete),
                ('stopping', 'idle', lambda: self._in_idling)

            ],
        })
        self._csm.bind_handlers_by_name(self)

        self.addProcessor(self._csm)

    @property
    def interlocked(self):
        return self._interlocked

    def interlock(self):
        self._interlocked = True
        self._bearings.engage()

    def release(self):
        self._in_shutdown = True
        self._bearings.disengage()

    def park(self):
        self.parking.trigger()

    @property
    def parked(self):
        return self._csm.state == 'parked'

    # Stopping stuff
    def stop(self):
        self._in_stopping = True

    @property
    def stopped(self):
        return self._csm.state == 'stopped'

    def stoppingComplete(self):
        return True

    def _setStoppingComplete(self):
        self._in_stopping = False

    # Accelerating stuff
    def start(self):
        self._in_starting = True

    @property
    def started(self):
        return self._csm.state == 'accelerating'

    def startingComplete(self):
        # This is really bad.
        self.lock()
        return True

    def _setStartingComplete(self):
        self._in_starting = False

    # Idle stuff
    def unlock(self):
        self._in_idling = True

    @property
    def idle(self):
        return self._csm.state == 'idle'

    def _setIdlingComplete(self):
        self._in_idling = False

    # Phase locking stuff
    def lock(self):
        self._in_locking = True

    @property
    def locked(self):
        return self._csm.state == 'phase_locked'

    def phaseLockingComplete(self):
        return True

    def _setPhaseLockingComplete(self):
        self._in_locking = False


def cycles(c, num):
    for i in range(num):
        c.process(0.1)


if __name__ == '__main__':
    c = SimulatedChopper()

    c.process(0.1)

    c.interlock()

    cycles(c, 4)

    c.park()

    cycles(c, 4)

    c.stop()

    cycles(c, 4)

    c.start()

    cycles(c, 1)

    c.unlock()

    cycles(c, 4)

    c.start()

    cycles(c, 4)

    c.lock()

    cycles(c, 4)

    c.stop()

    cycles(c, 1)

    c.start()

    cycles(c, 4)

    c.lock()

    cycles(c, 1)

    c.stop()
