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
            'on_entry':   'on_entry_',
            'in_state':   'in_state_',
            'on_exit':    'on_exit_',
            'transition': 'check_'
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

        for from_state, to_state, check_func in cfg.get('transitions', []):
            if from_state not in self._state:
                self._add_state(from_state)
            if to_state not in self._state:
                self._add_state(to_state)
            self._add_transition(from_state, to_state, check_func)

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
            handler = getattr(self._target, handler)

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
            'initial': 'init',
            'transitions': [
                # From State        To State            Condition Function
                ('off',             'parked',           lambda: self.power_switch),

                ('parked',          'off',              lambda: not self.power_switch),
                ('parked',          'idle',             lambda: self.bearings_ready),

                ('idle',            'off',              lambda: not self.power_switch),
                ('idle',            'adjust_speed',     'target_speed_changed'),

                ('adjust_speed',    'speed_locked',     self.check_target_speed_reached),
                ('adjust_speed',    'stopping',         'target_speed_zero'),

                ('speed_locked',    'adjust_speed',     'target_speed_changed'),
                ('speed_locked',    'stopping',         'target_speed_zero'),

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

        # Internal
        self._timer_bearings = 0

    def process(self, dt):
        self._csm.process(dt)

    @property
    def power_switch(self): return self._power_switch

    @power_switch.setter
    def power_switch(self, value): self._power_switch = True if value else False

    @property
    def bearings_ready(self): return self._bearings_ready

    @property
    def speed(self): return self._speed

    @speed.setter
    def speed(self, value): self._speed_target = value

    # Condition Functions
    def check_target_speed_changed(self):
        return self._speed_target != self.speed

    def check_target_speed_reached(self):
        return self._speed_target == self.speed

    def check_target_speed_zero(self):
        return self._speed_target == 0

    # State Handlers
    def on_entry_off(self, dt):
        self._init_vars()

    def on_exit_off(self, dt):
        print "Hello World! Initializing bearings!"
        self._timer_init_bearings = 3.0

    def in_state_parked(self, dt):
        if self._timer_bearings > 0:
            self._timer_bearings -= dt

        if self._timer_bearings <= 0:
            self._bearings_ready = True

    def on_exit_parked(self, dt):
        print "Bearings initialized, ready to go!"

    def in_state_adjust_speed(self, dt):
        # Modify speed based on dt
        pass

if __name__ == '__main__':
    chop = SimpleChopper()

    while True:
        # pcaspy.process() would be here
        chop.process(0.1)


