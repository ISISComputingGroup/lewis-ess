from fysom import Fysom as Statemachine
from time import sleep
from threading import Thread
from functools import partial


def printhandler(e):
    print str(e.src).rjust(15, ' ') + ' --- ' + str(e.event).center(25, ' ') + ' ---> ' + e.dst


class CallbackOnceWrapper(object):
    def __init__(self, fsm, state, callback):
        self._fsm = fsm
        self._state = state
        self._callback = callback

    def __call__(self, *args, **kwargs):
        if self._callback is not None:
            self._callback()

        delattr(self._fsm, 'on' + self._state)


class Device(object):
    def state(self):
        return None


class LevitationDevice(Device):
    def __init__(self):
        self.fsm = Statemachine({
            'initial': 'resting',
            'final': 'levitated',
            'events': [
                ('levitate', 'resting', 'levitating'),
                ('levitation_complete', 'levitating', 'levitated'),
                ('delevitate', 'levitated', 'delevitating'),
                ('delevitation_complete', 'delevitating', 'resting'),
                ('lock', 'levitated', 'locked'),
                ('unlock', 'locked', 'levitated')
            ],
            'callbacks': {
                'onleavelevitating': self._on_levitating_leave_handler,
                'onleavedelevitating': self._on_delevitating_enter_handler,
            }
        })

        self.statemap = {
            'resting': 'idle',
            'levitating': 'busy',
            'delevitating': 'busy',
            'levitated': 'idle',
            'locked': 'idle',
        }

    def _on_levitating_leave_handler(self, e):
        if hasattr(self, 'doLevitate'):
            self.doLevitate(self.fsm.transition)

        return False

    def _on_delevitating_enter_handler(self, e):
        if hasattr(self, 'doDeLevitate'):
            self.doDeLevitate(self.fsm.transition)

        return False

    def state(self):
        current = self.fsm.current
        return (self.statemap[current], current)

    def isResting(self):
        return self.fsm.current == 'resting'

    def isLevitated(self):
        return self.fsm.current == 'levitated'

    def levitate(self, callback=None):
        if self.fsm.can('levitate'):
            self.fsm.onlevitated = CallbackOnceWrapper(self.fsm, 'levitated', callback)
            self.fsm.levitate()
            self.fsm.levitation_complete()

    def lock(self, callback=None):
        if self.fsm.can('lock'):
            self.fsm.onlocked = CallbackOnceWrapper(self.fsm, 'locked', callback)
            self.fsm.lock()

    def unlock(self, callback=None):
        if self.fsm.can('unlock'):
            self.fsm.onlevitated = CallbackOnceWrapper(self.fsm, 'levitated', callback)
            self.fsm.unlock()

    def delevitate(self, callback=None):
        if self.fsm.can('delevitate'):
            self.fsm.onresting = CallbackOnceWrapper(self.fsm, 'resting', callback)
            self.fsm.delevitate()
            self.fsm.delevitation_complete()


class TimedLevitationDevice(LevitationDevice):
    def __init__(self, levitation_time, delevitation_time):
        super(TimedLevitationDevice, self).__init__()

        self._levitation_time = levitation_time
        self._delevitation_time = delevitation_time

        self._thread = None
        self._finish_callback = None

    def _wait(self, time=0, callback=None):
        sleep(time)

        if callable(callback):
            callback()

    def doLevitate(self, callback):
        thread = Thread(target=self._wait, args=(self._levitation_time, callback))
        thread.start()

    def doDeLevitate(self, callback):
        thread = Thread(target=self._wait, args=(self._delevitation_time, callback))
        thread.start()


class Chopper(object):
    def __init__(self, levitation_device):
        self.fsm = Statemachine({
            'initial': 'init',
            'events': [
                ('fulfill_interlocks', 'init', 'idle'),

                ('set_speed', 'idle', 'speed_setting'),
                ('set_speed', 'rotating', 'speed_setting'),

                ('speed_setpoint_reached', 'speed_setting', 'rotating'),

                ('lock_phase', 'rotating', 'phase_locking'),
                ('phase_lock_obtained', 'phase_locking', 'phase_locked'),
                ('set_phase', 'phase_locked', 'phase_locking'),
                ('set_speed', 'phase_locked', 'speed_setting'),

                ('stop', 'rotating', 'stopping'),
                ('stop', 'phase_locking', 'stopping'),
                ('stop', 'phase_locked', 'stopping'),
                ('stop', 'speed_setting', 'stopping'),

                ('stopped', 'stopping', 'idle')
            ],
            'callbacks': {
                'onchangestate': printhandler,
            }
        })

        self.levitation_device = levitation_device

    def fulfill_interlocks(self):
        if self.fsm.can('fulfill_interlocks'):
            self.fsm.fulfill_interlocks()

    def start(self):
        if self.fsm.isstate('idle'):
            self.levitation_device.levitate(partial(self.levitation_device.lock, callback=self.fsm.set_speed))


ld = TimedLevitationDevice(5.0, 2.0)
c = Chopper(ld)

c.fulfill_interlocks()
c.start()

for i in range(16):
    print ld.state()
    sleep(0.5)
