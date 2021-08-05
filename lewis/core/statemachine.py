# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2021 European Spallation Source ERIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *********************************************************************

"""
The statemachine module contains one of lewis' central parts, the cycle-based
:class:`StateMachine`. The module also contains classes that make it easier to define the
state machine (:class:`State`, :class:`Transition`). Despite its central nature, it's unlikely
to be used directly in client code for device simulations - these should be based on
:class:`StateMachineDevice`, which provides a more convenient interface for that purpose.
"""

from lewis.core.logging import has_log
from lewis.core.processor import CanProcess


class StateMachineException(Exception):
    """
    Classes in this module should only raise this type of Exception.
    """

    pass


class HasContext:
    """
    Mixin to provide a Context.

    Creates a `_context` member variable that can be assigned with :meth:`set_context`.

    Any state handler or transition callable that derives from this mixin will
    receive a context from its :class:`StateMachine` upon initialization (assuming the
    StateMachine was provided with a context itself).
    """

    def __init__(self):
        super(HasContext, self).__init__()
        self._context = None

    def set_context(self, new_context):
        """Assigns the new context to the member variable ``_context``."""
        self._context = new_context

        if hasattr(self, "_set_logging_context"):
            self._set_logging_context(self._context)


@has_log
class State(HasContext):
    """
    StateMachine state handler base class.

    Provides a way to implement StateMachine event handling behaviour using an
    object-oriented interface. Once the StateMachine is configured to do so, it
    will automatically invoke the events in this class when appropriate.

    To use this class, create a derived class and override any events that need
    custom behaviour. Device context is provided via :class:`HasContext` mixin.
    """

    def __init__(self):
        super(State, self).__init__()

    def on_entry(self, dt):
        """
        Handle entry event. Raised once, when this state is entered.

        :param dt: Delta T since last cycle.
        """
        pass

    def in_state(self, dt):
        """
        Handle in-state event.

        Raised repeatedly, once per cycle, while idling in this state. Exactly one
        in-state event occurs per cycle for every StateMachine. This is always the
        last event of the cycle.

        :param dt: Delta T since last cycle.
        """
        pass

    def on_exit(self, dt):
        """
        Handle exit event. Raised once, when this state is exited.

        :param dt: Delta T since last cycle.
        """
        pass


@has_log
class Transition(HasContext):
    """
    StateMachine transition condition base class.

    Provides a way to implement a transition that requires access to the device
    context. The device context is provided via :class:`HasContext` mixin, and can be
    accessed as `self._context`.

    To use this class, create a derived class and override the :meth:`__call__` attribute.
    """

    def __init__(self):
        super(Transition, self).__init__()

    def __call__(self):
        """
        This is invoked when the StateMachine wants to check whether this transition
        should occur. This happens on cycles when the StateMachine starts the cycle
        in the source state of this transition.

        If this call returns True, the StateMachine will transition to the destination
        state. Any remaining transition checks for the source state are not checked.

        :return: True or False / Should transition occur or not
        """
        return True


@has_log
class StateMachine(CanProcess):
    """
    Cycle based state machine.

    :param cfg: dict which contains state machine configuration.
    :param context: object which is assigned to State and Transition objects as their _context.

    The configuration dict may contain the following keys:

     - initial: Name of the initial state of this machine
     - states: [optional] Dict of custom state handlers
     - transitions: [optional] Dict of transitions in this state machine.

    State handlers may be given as a dict, list or State class:

     - dict: May contain keys 'on_entry', 'in_state' and 'on_exit'.
     - list: May contain up to 3 entries, above events in that order.
     - class: Should be an instance of a class that derives from State.

    In case of handlers being provided as a dict or a list, values should be callable
    and may take a single parameter: the Delta T since the last cycle.

    Transitions should be provided as a dict where:

     - Each key is a tuple of two values, the FROM and TO states respectively.
     - Each value is a callable transition condition that return True or False.

    Transition conditions are called once per cycle when in the FROM state. If one of
    the transition conditions returns True, the transition is executed that cycle. The
    remaining conditions aren't called.

    Consider using an OrderedDict if order matters.

    Only one transition may occur per cycle. Every cycle will, at the very least,
    trigger an in_state event against the current state.

    .. seealso:: See :meth:`~StateMachine.doProcess` for details.
    """

    def __init__(self, cfg, context=None):
        super(StateMachine, self).__init__()

        self._set_logging_context(context)

        self._state = (
            None  # We start outside of any state, first cycle enters initial state
        )
        self._handler = {}  # Nested dict mapping [state][event] = handler
        self._transition = (
            {}
        )  # Dict mapping [from_state] = [ (to_state, transition), ... ]
        self._prefix = {  # Default prefixes used when calling handler functions by name
            "on_entry": "_on_entry_",
            "in_state": "_in_state_",
            "on_exit": "_on_exit_",
        }

        # Specifying an initial state is not optional
        if "initial" not in cfg:
            raise StateMachineException(
                "StateMachine configuration must include "
                "'initial' to specify starting state."
            )
        self._initial = cfg["initial"]
        self._set_handlers(self._initial)

        self._setup_state_handlers(cfg.get("states", {}), context)
        self._setup_transition_handlers(cfg.get("transitions", {}), context)

    def _setup_state_handlers(self, state_handler_configuration, context):
        """
        This method constructs the state handlers from a user-provided dict.

        :param state_handler_configuration: Dictionary with state handler
        definitions.
        :param context: Context is provided to state handlers that inherit
        from HasContext.
        """
        for state_name, handlers in state_handler_configuration.items():
            if isinstance(handlers, HasContext):
                handlers.set_context(context)

            try:
                if isinstance(handlers, State):
                    self._set_handlers(
                        state_name,
                        handlers.on_entry,
                        handlers.in_state,
                        handlers.on_exit,
                    )
                elif isinstance(handlers, dict):
                    self._set_handlers(state_name, **handlers)
                elif hasattr(handlers, "__iter__"):
                    self._set_handlers(state_name, *handlers)
                else:
                    raise RuntimeError("Handler is not State, dict or __iter__.")
            except Exception:
                raise StateMachineException(
                    "Failed to parse state handlers for state '%s'. "
                    "Must be dict or iterable." % state_name
                )

    def _setup_transition_handlers(self, transition_handler_configuration, context):
        """
        This method constructs the transition handlers from a user-provided
        dict.

        :param transition_handler_configuration: Dictionary with transition
            handler definitions.
        :param context: Context is provided to transition handlers that inherit
        from HasContext.
        """
        for states, check_func in transition_handler_configuration.items():
            from_state, to_state = states

            # Set up default handlers if this state hasn't been mentioned before
            if from_state not in self._handler:
                self._set_handlers(from_state)
            if to_state not in self._handler:
                self._set_handlers(to_state)

            if isinstance(check_func, HasContext):
                check_func.set_context(context)

            # Set up the transition
            self._set_transition(from_state, to_state, check_func)

    @property
    def state(self):
        """Name of the current state."""
        return self._state

    def can(self, state):
        """
        Returns true if the transition to 'state' is allowed from the current state.

        :param state: State to check transition to
        :return: True if state is reachable from current
        """
        if self._state is None:
            return state == self._initial

        return state in (transition[0] for transition in self._transition[self._state])

    def bind_handlers_by_name(self, instance, override=False, prefix=None):
        """
        Auto-bind state handlers based on naming convention.

        :param instance: Target object instance to search for handlers and bind events to.
        :param override: If set to True, matching handlers will replace
                         previously registered handlers.
        :param prefix: Dict or list of prefixes to override defaults
                       (keys: on_entry, in_state, on_exit)

        This function enables automatically binding state handlers to events without having to
        specify them in the constructor. When called, this function searches `instance` for
        member functions that match the following patterns for all known states
        (states mentioned in 'states' or 'transitions' dicts of cfg):

            - ``instance._on_entry_[state]``
            - ``instance._in_state_[state]``
            - ``instance._on_exit_[state]``

        The default prefixes may be overridden using the prefix parameter. Supported keys are
        'on_entry', 'in_state', and 'on_exit'. Values should include any and
        all desired underscores.

        Matching functions are assigned as handlers to the corresponding state events,
        iff no handler was previously assigned to that event.

        If a state event already had a handler assigned (during construction or previous call
        to this function), no changes are made even if a matching function is found. To force
        previously assigned handlers to be overwritten, set the third parameter to True.
        This may be useful to implement inheritance-like specialization using multiple
        implementation classes but only one StateMachine instance.
        """
        if prefix is None:
            prefix = {}
        if not isinstance(prefix, dict) and hasattr(prefix, "__iter__"):
            prefix = dict(zip(["on_entry", "in_state", "on_exit"], prefix))

        # Merge prefix defaults with any provided prefixes
        prefix = dict(list(self._prefix.items()) + list(prefix.items()))

        # Bind handlers
        for state, handlers in self._handler.items():
            for event, handler in handlers.items():
                if handler is None or override:
                    named_handler = getattr(instance, prefix[event] + state, None)
                    if callable(named_handler):
                        self._handler[state][event] = named_handler

    def doProcess(self, dt):
        """
        Process a cycle of this state machine.

        :param dt: Delta T. "Time" passed since last cycle, passed on to event handlers.

        A cycle will perform at most one transition and exactly one in_state event.

        A transition will only occur if one of the transition condition functions leaving
        the current state returns True.

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
            self.log.debug('Entering initial state "%s"', self._initial)
            self._state = self._initial
            self._raise_event("on_entry", 0)
            self._raise_event("in_state", 0)
            return

        # General transition
        for target_state, check_func in self._transition.get(self._state, []):
            if check_func():
                self.log.debug(
                    "Transition triggered (%s -> %s)", self._state, target_state
                )
                self._raise_event("on_exit", dt)
                self._state = target_state
                self._raise_event("on_entry", dt)
                break

        # Always end with an in_state
        self._raise_event("in_state", dt)

    def reset(self):
        """
        Reset the state machine to before the first cycle. The next process() will
        enter the initial state.
        """
        self._state = None

    def _set_handlers(self, state, *args, **kwargs):
        """
        Add or update state handlers.

        :param state: Name of state to be added or updated
        :param on_entry: Handler for on_entry events. May be None, callable, or list of callables.
        :param in_state: Handler for in_state events. May be None, callable, or list of callables.
        :param on_exit: Handler for on_exit events. May be None, callable, or list of callables.

        Handlers may take up to one parameter (not counting self), delta T since last cycle,
        and should return nothing.

        When handlers are omitted or set to None, no event will be raised at all.
        """
        # Variable arguments for state handlers
        # Default to calling target.on_entry_state_name(), etc
        on_entry = args[0] if len(args) > 0 else kwargs.get("on_entry", None)
        in_state = args[1] if len(args) > 1 else kwargs.get("in_state", None)
        on_exit = args[2] if len(args) > 2 else kwargs.get("on_exit", None)

        self._handler[state] = {
            "on_entry": on_entry,
            "in_state": in_state,
            "on_exit": on_exit,
        }

    def _set_transition(self, from_state, to_state, transition_check):
        """
        Add or update a transition and its condition function.

        :param from_state: Name of state this transition leaves
        :param to_state: Name of state this transition enters
        :param transition_check: Callable condition under which this transition occurs.
                                 Should return True or False.

        The transition_check function should return True if the transition should occur.
        Otherwise, False.

        Transition condition functions should take no parameters (not counting self).
        """
        if not callable(transition_check):
            raise StateMachineException("Transition condition must be callable.")

        if from_state not in self._transition.keys():
            self._transition[from_state] = []

        # Remove previously added transition with same From -> To mapping
        try:
            del self._transition[from_state][
                [x[0] for x in self._transition[from_state]].index(to_state)
            ]
        except Exception:
            pass

        self._transition[from_state].append(
            (
                to_state,
                transition_check,
            )
        )

    def _raise_event(self, event, dt):
        """
        Invoke the given event name for the current state, passing dt as a parameter.

        :param event: Name of event to raise on current state.
        :param dt: Delta T since last cycle.
        """
        # May be None, function reference, or list of function refs
        self.log.debug("Processing state=%s, handler=%s", self._state, event)
        handlers = self._handler[self._state][event]

        if handlers is None:
            handlers = []

        if callable(handlers):
            handlers = [handlers]

        for handler in handlers:
            try:
                handler(dt)
            except TypeError:
                handler()
