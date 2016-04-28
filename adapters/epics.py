from datetime import datetime

from pcaspy import Driver, SimpleServer

from simulation.core import CanProcess
from simulation import SimulatedChopper


class PropertyExposingDriver(CanProcess, Driver):
    def __init__(self, target, pv_dict, default_poll_interval=1.0):
        super(PropertyExposingDriver, self).__init__()

        self._target = target
        self._pv_dict = pv_dict
        self._timers = {k: 0.0 for k in pv_dict.keys()}

        self._default_poll_interval = default_poll_interval

    def write(self, pv, value):
        try:
            setattr(self._target, self._pv_dict[pv]['property'], value)
        except AttributeError:
            return False

        self.setParam(pv, value)
        return True

    def doProcess(self, dt):
        # Updates bound parameters as needed
        for pv, parameters in self._pv_dict.iteritems():
            self._timers[pv] += dt
            if self._timers[pv] >= parameters.get('poll_interval', self._default_poll_interval):
                self.setParam(pv, getattr(self._target, parameters['property']))
                self._timers[pv] = 0.0

        self.updatePVs()


def run_pcaspy_server(target, pv_prefix, pv_db):
    server = SimpleServer()
    server.createPV(pv_prefix, pv_db)
    driver = PropertyExposingDriver(target=target, pv_dict=pv_db)

    delta = 0.0  # Delta between cycles
    count = 0  # Cycles per second counter
    timer = 0.0  # Second counter
    while True:
        start = datetime.now()

        # pcaspy's process() is weird. Docs claim argument is "processing time" in seconds.
        # But this is not at all consistent with the calculated delta.
        # Having "watch caget" running has a huge effect too (runs faster when watching!)
        # Additionally, if you don't call it every ~0.05s or less, PVs stop working. Annoying.
        # Set it to 0.0 for maximum cycle speed.
        server.process(0.1)
        target.process(delta)
        driver.process(delta)

        delta = (datetime.now() - start).total_seconds()
        count += 1
        timer += delta
        if timer >= 1.0:
            print "Running at %d cycles per second (%.3f ms per cycle)" % (count, 1000.0 / count)
            count = 0
            timer = 0.0
