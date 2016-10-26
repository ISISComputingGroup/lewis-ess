# Chopper simulation

This folder contains a simulated neutron chopper as it will be present at [ESS](http://europeanspallationsource.se).

Choppers at ESS are abstracted in such a way that all of them are exposed via the same interface, regardless of manufacturer. The behavior of this abstraction layer is modelled as a finite state machine.

The docs-directory contains an `fsm`-file (created using the program [qfsm](http://qfsm.sourceforge.net/)) which describes the state machine. While this is still work in progress, it gives an idea of how the choppers are going to operate internally.

There are two ways of running the chopper simulation. The first option is to run it directly using Python, the second is to run it in a [Docker container](https://www.docker.com/). See the [toplevel README](https://github.com/DMSC-Instrument-Data/plankton/blob/master/README.md) for details on installing.


## Starting the Chopper

Start using Docker:

```
$ docker run -it dmscid/plankton --device chopper --protocol epics -- --prefix SIM:
```

If running on Windows or OSX, you will additionally need to start a [Gateway](https://hub.docker.com/r/dmscid/epics-gateway/) if you want to communicate with the Docker container from outside of the VM.

Start using Python:

```
$ python simulation.py --device chopper --protocol epics -- --prefix SIM:
```

The `--` separates arguments of the protocol adapter from the simulation's arguments.


## Interacting with the simulated chopper

The simulated chopper is exposed via a set of EPICS PVs. For a detailed description of those, see the table of available PVs below.

To observe some available EPICS PVs in an automatically updating screen:

```
$ watch -n 1 caget SIM:State SIM:CmdL SIM:Spd-RB SIM:Spd SIM:Phs-RB SIM:Phs SIM:ParkAng-RB SIM:ParkAng
```

The following series of `caput`-commands, executed from a different terminal, will move the chopper to the specified speed and phase:

```
$ caput SIM:CmdS init
$ caput SIM:Spd 100.0
$ caput SIM:Phs 23.0
$ caput SIM:CmdS start
```

It may take a while until the simulation reaches the `phase_locked` state.


## EPICS interface

The following PVs are available. Note that if a prefix was specified on startup, it needs to be prepended to these:

| PV  | Description  | Unit | Access |
|---|---|---|---|---|
| Spd-RB  |  Readback of the speed setpoint. | Hz  | Read |
| ActSpd  |  Current rotation speed of the chopper disc. | Hz  | Read |
| Spd  | Speed setpoint.  | Hz | Read/Write |
| Phs-RB  |  Readback of the phase setpoint | Degree | Read |
| ActPhs  |  Current phase of the chopper disc. | Degree | Read |
| Phs  |  Phase setpoint. | Degree | Read/Write |
| ParkAng-RB  |  Readback of the park position setpoint | Degree | Read |
| ParkAng  |  Position to which the disc should rotate in parked state. | Degree | Read/Write |
| AutoPark | Enum `false`/`true` (or 0/1). If enabled, the chopper will move to the parking state when the stop state is reached. | - | Read/Write |
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

