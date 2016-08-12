[![Build Status](https://travis-ci.org/DMSC-Instrument-Data/plankton.svg?branch=master)](https://travis-ci.org/DMSC-Instrument-Data/plankton) [![Coverage Status](https://coveralls.io/repos/github/DMSC-Instrument-Data/plankton/badge.svg?branch=master)](https://coveralls.io/github/DMSC-Instrument-Data/plankton?branch=master)


# Plankton

Plankton is a Python library that assists in building simulated hardware devices. It is compatible with both Python 2 and 3.
Currently this repository contains a simulated neutron chopper as it will be present at [ESS](http://europeanspallationsource.se).
Choppers at ESS are abstracted in such a way that all of them are exposed via the same interface,
regardless of manufacturer. The behavior of this abstraction layer can be modelled as a finite state machine.

The docs-directory contains an `fsm`-file (created using the program [qfsm](http://qfsm.sourceforge.net/)) which describes
the state machine. While this is still work in progress, it gives an idea of how the choppers are going to operate internally.

# Chopper simulation

There are two ways of installing and running the chopper simulation. The first option is to run it directly using Python,
the second is to run it in a [Docker containter](https://www.docker.com/).

## Installation and startup I: Python

Clone the repository in a location of your choice:

```
$ git clone https://github.com/DMSC-Instrument-Data/plankton.git
```

If you do not have [git](https://git-scm.com/) available, you can also download this repository as an archive and unpack it somewhere. Plankton has a few dependencies that can be installed through pip via the requirements.txt file:

```
$ pip install -r requirements.txt
```

Furthermore, [EPICS base](http://www.aps.anl.gov/epics/base/) has to be installed on the machine. Usually some environment
variables have to be configured so everything is found on the network. For exposing the simulated chopper only on your
`localhost`, the following exports can be used:

```
$ export EPICS_CAS_INTF_ADDR_LIST=localhost
$ export EPICS_CA_AUTO_ADDR_LIST=NO
$ export EPICS_CA_ADDR_LIST=localhost
```

Run the basic chopper simulation:

```
$ python simulation.py --device chopper --setup default --protocol epics --parameters pv_prefix=SIM:
```

## Installation and startup II: Docker

Another option to install and run plankton is via Docker (installation of Docker is outside the scope of this document,
please refer to the instructions on the Docker website). Once Docker is installed on the machine,
running the simulation is done via docker, with the same parameters passed to the simulation as in the Python case:

```
$ docker run -it dmscid/plankton --device chopper --setup default --protocol epics --parameters pv_prefix=SIM:
```

Please note that this currently only works on a Linux host, but a solution using `docker-machine` that runs on other systems
is under development.

When this method is used, the EPICS configuration on the host needs to be a bit different, because the docker container has its own IP address on the internal network that the containers and the host are part of.

```
$ export EPICS_CA_ADDR_LIST=172.17.255.255
```

If the Docker network is configured differently, this IP needs to be changed accordingly.

## Interacting with the simulated chopper

The simulated chopper is exposed via a set of EPICS PVs. For a detailed description of those, see the table of available PVs below.

Observe some available EPICS PVs in an automatically updating screen:

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

The simulator is exposed to channel access, using the [pcaspy](https://pypi.python.org/pypi/pcaspy)-module.
Depending on the level of simulation there may be different PVs available to control the simulated chopper.
At a minimum, the following PVs will be exposed:

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
