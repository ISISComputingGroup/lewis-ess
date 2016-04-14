# pylint: disable=W0201


class StateMachineException(Exception):
    pass


class StateMachine(object):
    def __init__(self, target, cfg):
        self._target = None
        self._initial = None
        self._state = None

        self._handler = {}      # Nested dict mapping [state][event] = handler
        self._transition = {}   # Nested dict mapping [from_state][to_state] = transition
        self._prefix = {        # Default prefixes used when calling handler/transition functions by name
            'on_entry':   '_on_entry_',
            'in_state':   '_in_state_',
            'on_exit':    '_on_exit_',
            'transition': '_check_'
        }

        # The None state represents the condition when the machine has not yet entered
        # the initial state. This will be the case before the first cycle and immediately
        # following a reset(). It has no name and no handlers.
        self._add_state(None, None, None, None)

        # Apply initial config
        self.target = target
        self.extend(cfg)

    @property
    def state(self):
        return self._state

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    def extend(self, cfg):
        """
        Extend the current configuration of this state machine.

        :param cfg: dict containing configuration amendments. See __init__ for details.
        """
        if 'initial' in cfg:
            self._initial = cfg['initial']

        # TODO: Allow user to explicitly specify states and their handlers?

        for from_state, to_state, check_func in cfg.get('transitions', []):
            if from_state not in self._handler:
                self._add_state(from_state)
            if to_state not in self._handler:
                self._add_state(to_state)
            self._add_transition(from_state, to_state, check_func)

        # TODO: Allow user to override handler prefix settings?

    def process(self, dt):
        """
        Process a cycle of this state machine.

        A cycle will perform at most one transition. A transition will only occur if one
        of the transition check functions leaving the current state returns True.

        When a transition occurs, the following events are raised:
         - on_exit_old_state()
         - on_entry_new_state()
         - in_state_new_state()

        The first cycle after init or reset will never call transition checks and, instead,
        always performs on_entry and in_state on the initial state.

        Whether a transition occurs or not, and regardless of any other circumstances, a
        cycle always ends by raising an in_state event on the current (potentially new)
        state.

        :param dt: Delta T. "Time" passed since last cycle, passed on to event handlers.
        """
        # Initial transition on first cycle / after a reset()
        if self._state is None:
            self._state = self._initial
            self._raise_event('on_entry', 0)
            self._raise_event('in_state', 0)
            return

        # General transition
        for target_state, check_func in self._transition[self._state].iteritems():
            if self._check_transition(check_func):
                self._raise_event('on_exit', dt)
                self._state = target_state
                self._raise_event('on_entry', dt)
                break

        # Always end with an in_state
        self._raise_event('in_state', dt)

    def reset(self):
        self._state = None

    def _add_state(self, state, *args, **kwargs):
        # Variable arguments for state handlers
        # Default to calling target.on_entry_state_name(), etc
        on_entry = args[0] if len(args) > 0 else kwargs.get('on_entry', self._prefix['on_entry'] + state)
        in_state = args[1] if len(args) > 1 else kwargs.get('in_state', self._prefix['in_state'] + state)
        on_exit = args[2] if len(args) > 2 else kwargs.get('on_exit', self._prefix['on_exit'] + state)

        self._handler[state] = {'on_entry': on_entry,
                                'in_state': in_state,
                                'on_exit':  on_exit}

    def _add_transition(self, from_state, to_state, transition_check):
        if from_state not in self._transition.keys():
            self._transition[from_state] = {}

        if not callable(transition_check):
            transition_check = self._prefix['transition'] + transition_check

        self._transition[from_state][to_state] = transition_check

    def _raise_event(self, event, dt):
        # May be None, function reference, or string of target member function name
        handler = self._handler[self._state][event]

        if handler and not callable(handler):
            handler = getattr(self._target, handler, None)

        if handler and callable(handler):
            handler(dt)

    def _check_transition(self, check_func):
        if not callable(check_func):
            check_func = getattr(self._target, check_func)

        return check_func()


class SimpleChopper(object):
    def print_status(self):
        pass

    def __init__(self):
        self._csm = StateMachine(self, {
            'initial': 'off',
            'transitions': [
                # From State        To State            Condition Function
                ('off',             'parked',           lambda: self.power_switch),

                ('parked',          'off',              lambda: not self.power_switch),
                ('parked',          'idle',             lambda: self.bearings_ready),

                ('idle',            'off',              lambda: not self.power_switch),
                ('idle',            'adjust_speed',     'target_speed_changed'),
                ('idle',            'stopping',         'target_speed_zero'),

                ('adjust_speed',    'speed_locked',     self._check_target_speed_reached),
                ('adjust_speed',    'stopping',         'target_speed_zero'),

                ('speed_locked',    'adjust_speed',     'target_speed_changed'),
                ('speed_locked',    'stopping',         'target_speed_zero'),
                ('speed_locked',    'idle',             lambda: not self._speed_locked),

                ('stopping',        'idle',             lambda: self.speed == 0),
            ]
        })

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

    # Client should call this to trigger a cycle
    def process(self, dt):
        self._csm.process(dt)

    # Properties and functions that the client can access
    @property
    def power_switch(self): return self._power_switch

    @power_switch.setter
    def power_switch(self, value): self._power_switch = True if value else False

    @property
    def bearings_ready(self): return self._bearings_ready

    @property
    def speed(self): return self._speed

    @property
    def state(self): return self._csm.state

    @property
    def speed_locked(self): return self._speed_locked

    def unlock(self): self._speed_locked = False

    def speed_command(self, speed):
        self._speed_target = speed
        self._command_issued = True

    # Condition Functions (StateMachine calls these by name, based on init settings)
    def _check_target_speed_changed(self):
        return self._speed_target != self._speed and self._speed_target != 0 and self._command_issued

    def _check_target_speed_reached(self):
        return self._speed_target == self._speed and self._speed_target != 0

    def _check_target_speed_zero(self):
        return self._speed_target == 0 and self._speed != 0 and self._command_issued

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
            self._bearings_ready = True

    def _on_exit_parked(self, dt):
        print "Bearings initialized, ready to go!"

    def _in_state_idle(self, dt):
        # Decelerate gradually if we're still spinning
        if self._speed < 0.1:
            self._speed = 0
        else:
            self._speed -= (self._speed / (8 / dt))

    def _on_entry_adjust_speed(self, dt):
        self._command_issued = False

    def _in_state_adjust_speed(self, dt):
        # Approach target speed, rate based on dt
        if abs(self._speed - self._speed_target) < 0.1:
            self._speed = self._speed_target
        else:
            self._speed += ((self._speed_target - self._speed) / (3 / dt))

    def _on_entry_speed_locked(self, dt):
        # Notice there's an exit condition from Speed_Locked to Idle based on _locked == False
        # But this will not be checked until the next cycle, so setting it True here works fine
        self._speed_locked = True

    def _on_entry_stopping(self, dt):
        self._command_issued = False

    def _in_state_stopping(self, dt):
        # Decelerate quickly based on dt
        if self._speed < 0.1:
            self._speed = 0
        else:
            self._speed -= (self._speed / (3 / dt))


from time import sleep

if __name__ == '__main__':
    chop = SimpleChopper()
    t = 0.0

    for x in xrange(5):
        chop.process(0.1)
        t += 0.1
        print "Tick: %.1f | State: %s | Speed: %.1f" % (t, chop.state, chop.speed)
        sleep(0.05)

    chop.power_switch = True

    for x in xrange(12):
        chop.process(0.4)
        t += 0.4
        print "Tick: %.1f | State: %s | Speed: %.1f" % (t, chop.state, chop.speed)
        sleep(0.2)

    print "*** Setting target speed to 60 ***"
    chop.speed_command(60)

    for x in xrange(100):
        chop.process(0.5)
        t += 0.5
        print "Tick: %.1f | State: %s | Speed: %.1f" % (t, chop.state, chop.speed)
        sleep(0.25)
        if chop.speed == 60:
            break

    for x in xrange(4):
        chop.process(0.5)
        t += 0.5
        print "Tick: %.1f | State: %s | Speed: %.1f" % (t, chop.state, chop.speed)
        sleep(0.25)

    print "*** Unlocking chopper ***"
    chop.unlock()

    for x in xrange(100):
        chop.process(0.5)
        t += 0.5
        print "Tick: %.1f | State: %s | Speed: %.1f" % (t, chop.state, chop.speed)
        sleep(0.25)
        if chop.speed < 30:
            break

    print "*** Stopping chopper ***"
    chop.speed_command(0)

    for x in xrange(100):
        chop.process(0.5)
        t += 0.5
        print "Tick: %.1f | State: %s | Speed: %.1f" % (t, chop.state, chop.speed)
        sleep(0.25)
        if chop.speed == 0:
            break

    for x in xrange(4):
        chop.process(0.5)
        t += 0.5
        print "Tick: %.1f | State: %s | Speed: %.1f" % (t, chop.state, chop.speed)
        sleep(0.25)
