class Chopper(object):
    def park(self):
        pass

    def stop(self):
        pass

    def setSpeedAndPhase(self, speed, phase):
        if not self.canSetSpeedAndPhase():
            raise RuntimeError('Haha')

        self.doSetSpeedAndPhase(speed, phase)

    def setPhase(self):
        pass

    def lock(self):
        pass

    def unlock(self):
        pass


class EssEpicsChopper(Chopper):
    def doSetSpeedAndPhase(self, speed, phase):
        caput('speed:sp', speed)
        caput('phase:sp', phase)
        caput('command', 'start')

class SimulatedChopper(Chopper):
    def doSetSpeedAndPhase(self, speed, phase):
        self._target_speed = speed
        self._target_phase = phase
        self._command = 'start'