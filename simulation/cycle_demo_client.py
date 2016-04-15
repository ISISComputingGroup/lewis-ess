from pcaspy import Driver, SimpleServer
from cycle_demo_sim import SimpleChopper
from datetime import datetime


prefix = 'SIM:'
pvdb = {
    'SPEED': {'prec': 1},
    'SPEED:SP': {'prec': 1},
    'POWER': {'type': 'int'},
    'POWER:SP': {'type': 'int'},
    'LOCKED': {'type': 'int'},
    'LOCKED:SP': {'type': 'int'},
    'BEARINGS_READY': {'type': 'int'},
    'STATE': {'type': 'string'},
}


class SimDriver(Driver):
    def __init__(self, chopper):
        super(SimDriver, self).__init__()

        self._chopper = chopper
        self._bindings = {}

    def write(self, pv, value):
        if pv == 'SPEED:SP':
            self._chopper.speed_command(value)
        elif pv == 'POWER:SP':
            self._chopper.power_switch = value
        elif pv == 'LOCKED:SP' and not value:
            self._chopper.unlock()
        else:
            return False

        self.setParam(pv, value)
        return True

    def bindParam(self, pv, value_func, poll_rate):
        # [pv] will be updated with value returned from [value_func] every [poll_rate] seconds.
        self._bindings[pv] = {
            'value_func': value_func,
            'poll_rate': poll_rate,
            'poll_timer': 0.0
        }

    def process(self, dt):
        # Updates bound parameters as needed
        for pv, binding in self._bindings.iteritems():
            binding['poll_timer'] += dt
            if binding['poll_timer'] >= binding['poll_rate']:
                self.setParam(pv, binding['value_func']())
                binding['poll_timer'] = 0


if __name__ == '__main__':
    """
    To run this, first make sure you have caRepeater running in the background and
    EPICS_CA variables are set up for localhost and no auto.

    Then execute this script in a python shell or pycharm.

    To watch all the PV values, I would recommend running this command in a terminal (Linux):

    $ watch -n 0.1 caget SIM:SPEED SIM:SPEED:SP SIM:POWER SIM:POWER:SP SIM:LOCKED SIM:LOCKED:SP SIM:BEARINGS_READY SIM:STATE

    In another terminal, you can set PVs as per usual:

    $ caput SIM:POWER:SP 1
    $ caput SIM:SPEED:SP 1000
    $ caput SIM:LOCKED:SP 0
    $ caput SIM:SPEED:SP 700
    """
    chopper = SimpleChopper()
    server = SimpleServer()
    server.createPV(prefix, pvdb)
    driver = SimDriver(chopper)

    # Most PVs update every 1.0 seconds; state updates every 0.1 seconds.
    driver.bindParam('SPEED', lambda: chopper.speed, 1.0)
    driver.bindParam('POWER', lambda: chopper.power_switch, 1.0)
    driver.bindParam('LOCKED', lambda: chopper.speed_locked, 1.0)
    driver.bindParam('BEARINGS_READY', lambda: chopper.bearings_ready, 1.0)
    driver.bindParam('STATE', lambda: chopper.state, 0.1)

    delta = 0.0     # Delta between cycles
    count = 0       # Cycles per second counter
    timer = 0.0     # Second counter
    while True:
        start = datetime.now()

        # pcaspy's process() is weird. Docs claim argument is "processing time" in seconds.
        # But this is not at all consistent with the calculated delta.
        # Having "watch caget" running has a huge effect too (runs faster when watching!)
        # Additionally, if you don't call it every ~0.05s or less, PVs stop working. Annoying.
        # Set it to 0.0 for maximum cycle speed.
        server.process(0.1)
        chopper.process(delta)
        driver.process(delta)

        delta = (datetime.now() - start).total_seconds()
        count += 1
        timer += delta
        if timer >= 1.0:
            print "Running at %d cycles per second (%.3f ms per cycle)" % (count, 1000.0 / count)
            count = 0
            timer = 0.0
