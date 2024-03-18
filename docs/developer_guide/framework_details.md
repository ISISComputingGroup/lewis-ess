# Framework Details

The Lewis framework is built around a cycle-driven core which in turn drives
the device simulation, including an optional StateMachine, and shared protocol
adapters that separate the communication layer from the simulated device.

![The simulation cycle diagram.](../resources/diagrams/SimulationCycles.png)

## Cycle-driven

All processing in the framework occurs during "heartbeat" simulation ticks
which propagate calls to `process` methods throughout the simulation,
along with a Δt parameter that contains the time that has
passed since the last tick. The device simulation is then responsible for
updating its state based on how much time has passed and what input has
been received during that time.

The benefits of this approach include:

-  This closely models real device behaviour, since processing in
   electronic devices naturally occurs on a cycle basis.
-  As a side-effect of the above, certain quirks of real devices are
   often captured by the simulated device naturally, without additional
   effort.
-  The simulation becomes deterministic: The same amount of process
   cycles, with the same Δt parameters along the way, and
   the same input via the device protocol, will always result in exactly
   the same device state.
-  Simulation speed can be controlled by increasing (fast-forward) or
   decreasing (slow-motion) the Δt parameter by a given factor.
-  Simulation fidelity can be controlled independently from speed by
   increasing or decreasing the number of cycles per second while
   adjusting the Δt parameter to compensate.

The above traits are very desirable both for running automated tests
against the simulation, and for debugging any issues that are
identified.

## Statemachine

A class designed for a cycle-driven approach is provided to allow modeling complex
device behaviour in an event-driven fashion.

A device may initialize a statemachine on construction, telling it what
states the device can be in and what conditions should cause it to
transition between them. The statemachine will automatically check
eligible (exiting current state) transition conditions every cycle and
perform transitions as necessary, triggering callbacks for any event
that occurs. The following events are available for every state:

 - `on_exit` is triggered once just before exiting the state
 - `on_entry` is triggered once when entering the state
 - `in_state` is triggered every cycle that ends in the state

Every cycle will trigger exactly one `in_state` event. This will
always be the last event of the cycle. When no transition occurs, this
is the only event. On the very first cycle of a simulation run,
`on_entry` is raised against the initial state before raising an
`in_state` against it. Any other cycles that involve a transition
first raise `on_exit` against the current state, and then raise
`on_entry` and `in_state` against the new state. Only one transition
may occur per cycle.

There are three ways to specify event handlers when initializing the
statemachine:

-  Object-Oriented: Implement one class per state, derived from
   `lewis.core.statemachine.State`, which optionally contains up to
   one of each event handler
-  Function-Driven: Bind individual functions to individual events that
   need handling
-  Implicit: Implement handlers in the device class, with standard names
   like `on_entry_init` for a state called "init", and call
   `bindHandlersByName()`
