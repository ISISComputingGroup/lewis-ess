# Plankton

Plankton is a library that assists in building simulated hardware devices. Currently this repository contains
a simulated neutron chopper as it will be present at [ESS](http://europeanspallationsource.se).
Choppers at ESS are abstracted in such a way that all of them are exposed via the same interface,
regardless of manufacturer. The behavior of this abstraction layer can be modelled as a finite state machine.

The docs-directory contains an `fsm`-file (created using the program [qfsm](http://qfsm.sourceforge.net/)) which describes
the state machine. While this is still work in progress, it gives an idea of how the choppers are going to operate internally.

## Python module

Install dependencies through the requirements.txt file:

```
$ pip install -r requirements.txt
```

Run the basic chopper simulation:

```
$ python basic_chopper_simulation.py
```

Observe available EPICS PVs in an automatically updating screen:

```
$ watch -n 1 caget SIM:STATE SIM:LAST_COMMAND SIM:SPEED SIM:SPEED:SP SIM:PHASE SIM:PHASE:SP SIM:PARKPOSITION SIM:PARKPOSITION:SP
```

The following series of `caput`-commands, executed from a different terminal, will move the chopper to the specified
speed and phase:

```
$ caput SIM:COMMAND INTERLOCK
$ caput SIM:SPEED:SP 100.0
$ caput SIM:PHASE:SP 23.0
$ caput SIM:COMMAND START
```

It may take a while until the simulation reaches the `phase_locked` state.


## EPICS interface

The simulator is exposed to channel access, using the [pcaspy](https://pypi.python.org/pypi/pcaspy)-module. Depending on the level
of simulation there may be different PVs available to control the simulated chopper. At a minimum, the following PVs will be
exposed:

| PV  | Description  | Unit | Access |
|---|---|---|---|---|
| SPEED  |  Current rotation speed of the chopper disc. | Hz  | Read |
| PHASE  |  Current phase of the chopper disc. | Degree | Read |
| PARKPOSITION  |  Current position of chopper disc if in parked state. | Degree | Read |
| STATE  |  Enum for chopper state. | - | Read |
| TDCE  |  Vector of TDC (top dead center) events in last accelerator pulse. | to be determined | Read |
| SPEED:SP  | Speed setpoint.  | Hz | Read/Write |
| PHASE:SP  |  Phase setpoint. | Degree | Read/Write |
| PARKPOSITION:SP  |  Position to which the disc should rotate in parked state. | Degree | Read/Write |
| DIRECTION  |  Enum for rotation direction (clockwise, counter clockwise). | - | Read/Write |
| COMMAND  |  String field to accept commands. | - | Read/Write |

**Possible values for STATE**
- Resting*: The chopper disc is resting, the magnetic bearings are off.
- Levitating*: The chopper disc is in the process of being lifted up into stable levitation.
- Delevitating*: The chopper disc is in the process of being let down into the resting state.
- Accelerating: The chopper disc is accelerated to the speed setpoint.
- Phase locking: The chopper is trying to acquire a phase lock.
- Phase locked: Speed and phase are at the setpoints.
- Idle: The motor is off, the disc is rotating only via inertia.
- Parking: The chopper disc is in the process of rotating to the park position.
- Parked: The chopper disc is parked in the specified position.
- Stopping: The chopper disc is actively decelerated to speed 0.
- Stopped: The chopper disc is at speed 0.
- Error*: An error has occured (to be specified in more detail).

The states marked with a * are not implemented yet and are not present in choppers which work with mechanical bearings.

**Possible values for COMMAND**
- START: Speed and phase are adjusted to match the corresponding setpoints
- PHASE: Phase is adjusted to match the corresponding setpoint
- COAST: Switch off motor, but do not actively decelerate disc
- STOP: Go to velocity 0, disc remains levitated
- PARK: Go to velocity 0, disc remains levitated, is rotated to PARKEDANGLE:SP
- LEVITATE*: Levitate disc if it's not levitated
- DELEVITATE*: Delevitate disc if possible

The commands marked with a * are not implemented yet. There are however two additional commands, INTERLOCK and RELEASE. INTERLOCK takes the chopper from the initial `init` state to the `stopped` state, RELEASE does the opposite. This behavior will likely change soon.

## Additional tools

In a separate [repository](https://github.com/DMSC-Instrument-Data/plankton-misc) there is an OPI-file for use with CS-Studio and two files that expose the simulated chopper as a setup in NICOS (see readme there).
