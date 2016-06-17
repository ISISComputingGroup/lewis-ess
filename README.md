[![Build Status](https://travis-ci.org/DMSC-Instrument-Data/plankton.svg?branch=master)](https://travis-ci.org/DMSC-Instrument-Data/plankton)

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
$ python simulation.py --device chopper --setup default --protocol epics --parameters pv_prefix=SIM:
```

Observe available EPICS PVs in an automatically updating screen:

```
$ watch -n 1 caget SIM:State SIM:CmdL SIM:Spd-RB SIM:Spd SIM:Phs-RB SIM:Phs SIM:ParkAng-RB SIM:ParkAng
```

The following series of `caput`-commands, executed from a different terminal, will move the chopper to the specified
speed and phase:

```
$ caput SIM:CmdS init
$ caput SIM:Spd 100.0
$ caput SIM:Phs 23.0
$ caput SIM:CmdS start
```

It may take a while until the simulation reaches the `phase_locked` state.


## EPICS interface

The simulator is exposed to channel access, using the [pcaspy](https://pypi.python.org/pypi/pcaspy)-module. Depending on the level
of simulation there may be different PVs available to control the simulated chopper. At a minimum, the following PVs will be
exposed:

| PV  | Description  | Unit | Access |
|---|---|---|---|---|
| Spd-RB  |  Current rotation speed of the chopper disc. | Hz  | Read |
| ActSpd  |  Current rotation speed of the chopper disc. | Hz  | Read |
| Spd  | Speed setpoint.  | Hz | Read/Write |
| Phs-RB  |  Current phase of the chopper disc. | Degree | Read |
| ActPhs  |  Current phase of the chopper disc. | Degree | Read |
| Phs  |  Phase setpoint. | Degree | Read/Write |
| ParkAng-RB  |  Current position of chopper disc if in parked state. | Degree | Read |
| ParkAng  |  Position to which the disc should rotate in parked state. | Degree | Read/Write |
| State  |  Enum for chopper state. | - | Read |
| TDCE*  |  Vector of TDC (top dead center) events in last accelerator pulse. | to be determined | Read |
| Dir-RB*  |  Enum for rotation direction (clockwise, counter clockwise). | - | Read |
| Dir*  |  Desired rotation direction. (clockwise, counter clockwise). | - | Read/Write |
| CmdS  |  String field to accept commands. | - | Read/Write |
| CmdL  |  String field with last command. | - | Read |

Starred PVs are not implemented yet, but will become part of the interface.

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
- start: Speed and phase are adjusted to match the corresponding setpoints
- set_phase: Phase is adjusted to match the corresponding setpoint
- unlock: Switch off motor, but do not actively decelerate disc
- stop: Go to velocity 0, disc remains levitated
- park: Go to velocity 0, disc remains levitated, is rotated to PARKEDANGLE:SP
- levitate*: Levitate disc if it's not levitated
- delevitate*: Delevitate disc if possible

The commands marked with a * are not implemented yet. There are however two additional commands, INIT and DEINIT. INIT takes the chopper from the initial `init` state to the `stopped` state, DEINIT does the opposite.

## Additional tools

In a separate [repository](https://github.com/DMSC-Instrument-Data/plankton-misc) there is an OPI-file for use with CS-Studio and two files that expose the simulated chopper as a setup in NICOS (see readme there).
