from processor import CanProcess


class StateMachineException(Exception):
    pass


class StateMachine(CanProcess):
    def __init__(self, cfg):
        """
        Cycle based state machine.

        :param cfg: dict which contains state machine configuration.

        The configuration may contain the following keys:
        - initial: Name of the initial state of this machine
        - states: [optional] Dict of custom state handlers
        - transitions: [optional] List of transitions in this state machine.

        Transitions should be provided as tuples with three elements:
        - From State: String name of state that this transition leaves
        - To State: String name of state that this transition enters
        - Condition Function: Condition under which the transition should be executed

        A condition function should take no arguments and return True or False. If True
        is returned, the transition will be executed.

        Only one transition may occur per cycle. Every cycle will, at the very least,
        trigger an in_state event against the current state. See process() for details.
        """
        super(StateMachine, self).__init__()

        self._state = None      # We start outside of any state, first cycle enters initial state
        self._handler = {}      # Nested dict mapping [state][event] = handler
        self._transition = {}   # Nested dict mapping [from_state][to_state] = transition
        self._prefix = {        # Default prefixes used when calling handler functions by name
            'on_entry': '_on_entry_',
            'in_state': '_in_state_',
            'on_exit': '_on_exit_',
        }

        # Specifying an initial state is not optional
        if 'initial' not in cfg:
            raise StateMachineException("StateMachine configuration must include 'initial' to specify starting state.")
        self._initial = cfg['initial']
        self._set_handlers(self._initial)

        # Allow user to explicitly specify state handlers
        for state_name, handlers in cfg.get('states', {}).iteritems():
            try:
                if isinstance(handlers, dict):
                    self._set_handlers(state_name, **handlers)
                elif hasattr(handlers, '__iter__'):
                    self._set_handlers(state_name, *handlers)
                else:
                    raise
            except:
                raise StateMachineException(
                    "Failed to parse state handlers for state '%s'. Must be dict or iterable." % state_name)

        for from_state, to_state, check_func in cfg.get('transitions', []):
            # Set up default handlers if this state hasn't been mentioned before
            if from_state not in self._handler:
                self._set_handlers(from_state)
            if to_state not in self._handler:
                self._set_handlers(to_state)

            # Set up the transition
            self._set_transition(from_state, to_state, check_func)

    @property
    def state(self):
        """
        :return: Name of the current state
        """
        return self._state

    def bind_handlers_by_name(self, instance, prefix=None, override=False):
        """
        Auto-bind state handlers based on naming convention.

        :param instance: Target object instance to search for handlers and bind events to.
        :param prefix: [optional] Dict of prefixes to override defaults (keys: on_entry, in_state, on_exit)
        :param override: [optional] If set to True, matching handlers will replace previously registered handlers.

        This function enables automatically binding state handlers to events without having to specify them in the
        constructor. When called, this function searches `instance` for member functions that match the following
        patterns for all known states:

        - instance._on_entry_[state]
        - instance._in_state_[state]
        - instance._on_exit_[state]

        The default prefixes may be overridden using the second parameter. Supported keys are 'on_entry', 'in_state',
        and 'on_exit'. Values should include any and all desired underscores.

        Matching functions are assigned as handlers to the corresponding state events, iff no handler was previously
        assigned to that event.

        If a state event already had a handler assigned (during construction or previous call to this function), no
        changes are made even if a matching function is found. To force previously assigned handlers to be overwritten,
        set the third parameter to True. This may be useful to implement inheritance-like specialization using multiple
        implementation classes but only one StateMachine instance.
        """
        if prefix is None:
            prefix = {}

        # Merge prefix defaults with any provided prefixes
        prefix = dict(list(self._prefix.items()) + list(prefix.items()))

        # Bind handlers
        for state, handlers in self._handler.iteritems():
            for event, handler in handlers.iteritems():
                if handler is None or override:
                    named_handler = getattr(instance, prefix[event] + state, None)
                    if callable(named_handler):
                        self._handler[state][event] = named_handler

    def doProcess(self, dt):
        """
        Process a cycle of this state machine.

        :param dt: Delta T. "Time" passed since last cycle, passed on to event handlers.

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
        """
        # Initial transition on first cycle / after a reset()
        if self._state is None:
            self._state = self._initial
            self._raise_event('on_entry', 0)
            self._raise_event('in_state', 0)
            return

        # General transition
        for target_state, check_func in self._transition.get(self._state, {}).iteritems():
            if check_func():
                self._raise_event('on_exit', dt)
                self._state = target_state
                self._raise_event('on_entry', dt)
                break

        # Always end with an in_state
        self._raise_event('in_state', dt)

    def reset(self):
        """
        Reset the state machine to before the first cycle. The next process() will enter the initial state.
        """
        self._state = None

    def _set_handlers(self, state, *args, **kwargs):
        """
        Add or update state handlers.

        :param state: Name of state to be added or updated
        :param on_entry: Handler for on_entry events. May be None, function ref, or list of function refs.
        :param in_state: Handler for in_state events. May be None, function ref, or list of function refs.
        :param on_exit: Handler for on_exit events. May be None, function ref, or list of function refs.

        Handlers should take exactly one parameter (not counting self), delta T since last cycle, and return nothing.

        When handlers are omitted or set to None, no event will be raised at all.
        """
        # Variable arguments for state handlers
        # Default to calling target.on_entry_state_name(), etc
        on_entry = args[0] if len(args) > 0 else kwargs.get('on_entry', None)
        in_state = args[1] if len(args) > 1 else kwargs.get('in_state', None)
        on_exit = args[2] if len(args) > 2 else kwargs.get('on_exit', None)

        self._handler[state] = {'on_entry': on_entry,
                                'in_state': in_state,
                                'on_exit': on_exit}

    def _set_transition(self, from_state, to_state, transition_check):
        """
        Add or update a transition and its condition function.

        :param from_state: Name of state this transition leaves
        :param to_state: Name of state this transition enters
        :param transition_check: Callable condition under which this transition occurs. Should return True or False.

        The transition_check function should return True if the transition should occur. Otherwise, False.

        Transition condition functions should take no parameters (not counting self).
        """
        if not callable(transition_check):
            raise StateMachineException("Transition condition must be callable.")

        if from_state not in self._transition.keys():
            self._transition[from_state] = {}

        self._transition[from_state][to_state] = transition_check

    def _raise_event(self, event, dt):
        """
        Invoke the given event name for the current state, passing dt as a parameter.

        :param event: Name of event to raise on current state.
        :param dt: Delta T since last cycle.
        """
        # May be None, function reference, or list of function refs
        handlers = self._handler[self._state][event]

        if handlers is None:
            handlers = []

        if callable(handlers):
            handlers = [handlers]

        for handler in handlers:
            handler(dt)
