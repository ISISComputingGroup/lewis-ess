[![Build Status](https://travis-ci.org/DMSC-Instrument-Data/plankton.svg?branch=master)](https://travis-ci.org/DMSC-Instrument-Data/plankton) [![Coverage Status](https://coveralls.io/repos/github/DMSC-Instrument-Data/plankton/badge.svg?branch=master)](https://coveralls.io/github/DMSC-Instrument-Data/plankton?branch=master)


# Plankton

Plankton is a Python framework for simulating hardware devices. It is compatible with both Python 2 and 3.

Plankton can be run directly using Python 2.7 or 3.x, or using a prepackaged Docker image that includes all dependencies. See relevant usage sections for details.

Resources:
- [GitHub](https://github.com/DMSC-Instrument-Data/plankton)
- [DockerHub](https://hub.docker.com/r/dmscid/plankton/)
- [Dockerfile](https://github.com/DMSC-Instrument-Data/plankton/blob/master/Dockerfile)


## Purpose and Use Cases

Plankton is being developed in the context of instrument control at the [ESS](http://europeanspallationsource.se), but it is general enough to be used in many other contexts that require detailed, stateful software simulations of hardware devices.

We consider a detailed device simulation to be one that can communicate using the same protocol as the real device, and that can very closely approximate real device behaviour in terms of what is seen through this protocol. This includes gradual processes, side-effects and error conditions.

The purpose of Plankton is to provide a common framework to facilitate the development of such simulators. By providing a common set of tools and abstracting away device protocols, we can minimize code replication and allow the developer of a simulated device to focus on capturing device behaviour.

Potential use cases for detailed device simulators include:

- Developing and testing software that interfaces with the device when it is unavailable
- Testing failure conditions without risking damage to the physical device
- Automated system and unit tests of software that communicates with the device
- Perform "dry runs" to test scripts that are to be run against the device

Using a simulation for the above has the added benefit that, unlike most real devices, a simulation may be sped up / fast-forwarded past any lengthy delays or processes that occur in the device.


## Framework Details

The Plankton framework is built around a cycle-based statemachine that drives the device simulation, and shared protocol adapters that separate the communication layer from the simulated device.

#### Cycle-based

By cycle-based we mean that all processing in the framework occurs during "heartbeat" simulation ticks that propagate calls to `process` methods throughout the simulation, along with a Delta T parameter that contains the time that has passed since the last tick. The device simulation is then responsible for updating its state based on how much time has passed and what input has been received during that time.

The benefits of this approach include:

- This closely models real device behaviour, since processing in electronic devices naturally occurs on a cycle basis.
- As a side-effect of the above, certain quirks of real devices are often captured by the simulated device naturally, without additional effort.
- The simulation becomes deterministic: The same amount of process cycles, with the same Delta T parameters along the way, and the same input via the device protocol, will always result in exactly the same device state.
- Simulation speed can be controlled by increasing (fast-forward) or decreasing (slow-motion) the Delta T parameter by a given factor.
- Simulation fidelity can be controlled independently from speed by increasing or decreasing the number of cycles per second while adjusting the Delta T parameter to compensate.

The above traits are very desirable both for running automated tests against the simulation, and for debugging any issues that are identified.

#### Statemachine

A statemachine class that was written with a cycle-based approach in mind is provided to allow modeling complex device behaviour in an event-driven fashion.

A device may initialize a statemachine on construction, telling it what states the device can be in and what conditions should cause it to transition between them. The statemachine will automatically check eligible (exiting current state) transition conditions every cycle and perform transitions as necessary, triggering callbacks for any event that occurs. The following events are available for every state:

- `on_exit` is triggered once just before exiting a state
- `on_entry` is triggered once when entering a state
- `in_state` is triggered every cycle that is spent within a state

Every cycle will trigger exactly one `in_state` event. This will always be the last event of the cycle. When no transition occurs, this is the only event. On the very first cycle of a simulation run, `on_entry` is raised against the initial state before raising an `in_state` against it. Any other cycles that involve a transition first raise `on_exit` against the current state, and then raise `on_entry` and `in_state` against the new state. Only one transition may occur per cycle.

There are three ways to specify event handlers when initializing the statemacine:

- Object-Oriented: Implement one class per state, derived from `State`, which contains one of each event handler
- Function-Driven: Bind individual functions to individual events
- Implicit: Implement handlers in the device class, with standard names like `on_entry_init` for a state called "init", and call `bindHandlersByName()`

#### Adapters

The adapters... WIP?


## Usage with Docker

Docker Engine must be installed in order to run the Plankton Docker image. Detailed installation instructions for various OSes may be found [here](https://docs.docker.com/engine/installation/).

On OSX and Windows, we recommend simply installing the [Docker Toolbox](https://www.docker.com/products/docker-toolbox). It contains everything you need and is (currently) more stable than the "Docker for Windows/Mac" beta versions.

On Linux, to avoid manually copy-pasting your way through the rather detailed instructions linked to above, you can let the Docker installation script take care of everything for you:

```
$ curl -fsSL https://get.docker.com/ | sh
```

Once Docker is installed, Plankton can be run as follows to, for example, simulate a Linkam T95 **d**evice and expose it via the TCP Stream **p**rotocol:

```
$ docker run -it dmscid/plankton -d linkam_t95 -p stream
```

Details about parameters for the various adapters, and differences between OSes are covered in the "Adapter Specifics" sections.


## Usage with Python

To use Plankton directly via Python you must install its dependencies:

- Python 2.7+ or 3.4+
- EPICS Base R3.14.12.5
- PIP 8.1+

Clone the repository in a location of your choice:

```
$ git clone https://github.com/DMSC-Instrument-Data/plankton.git
```

If you do not have [git](https://git-scm.com/) available, you can also download this repository as an archive and unpack it somewhere. A few additional dependencies must be installed. This can be done through pip via the requirements.txt file:

```
$ pip install -r requirements.txt
```

If you also want to run Plankton's unit tests, you may also install the development dependencies:

```
$ pip install -r requirements-dev.txt
```

If you want to use the EPICS adapter, you will also need to configure EPICS environment variables correctly. If you only want to communicate using EPICS locally via the loopback device, you can configure it like this:

```
$ export EPICS_CA_AUTO_ADDR_LIST=NO
$ export EPICS_CA_ADDR_LIST=localhost
$ export EPICS_CAS_INTF_ADDR_LIST=localhost
```

You can then run Plankton as follows (from within the plankton directory):

```
$ python simulation.py -d chopper -p epics
```

Details about parameters for the various adapters, and differences between OSes are covered in the "Adapter Specifics" sections.


## EPICS Adapter Specifics

The EPICS adapter takes only one optional argument:

- `-p` / `--prefix`: This string is prefixed to all PV names. Defaults to empty / no prefix.

Arguments meant for the adapter should be separated from general Plankton arguments by a free-standing `--`. For example:

```
$ docker run -itd dmscid/plankton -d chopper -p epics -- -p SIM1:
$ python simulation.py -d chopper -p epics -- --prefix SIM2:
```

When using the EPICS adapter within a docker container, the PV will be served on the docker0 network (172.17.0.0/16).

On Linux, this means that `EPICS_CA_ADDR_LIST` must include this networks broadcast address:

```
$ export EPICS_CA_AUTO_ADDR_LIST=NO
$ export EPICS_CA_ADDR_LIST=172.17.255.255
$ export EPICS_CAS_INTF_ADDR_LIST=localhost
``` 

On Windows and OSX, the docker0 network is inside of a virtual machine. If we want to communicate with it, we need to use an EPICS Gateway to forward EPICS requests and responses for us. We provide an [EPICS Gateway Docker image](https://hub.docker.com/r/dmscid/epics-gateway/) that can be used to do this relatively easily (detailed instructions on the linked page). 


## Stream Adapter Specifics



Describe command-line arguments used by the Stream adapter, communicating with containers via Stream on Windows and OSX (port forwarding).

Mention line endings?





# --- Most of this belongs in a chopper.md or something ---

Currently this repository contains a simulated neutron chopper as it will be present at [ESS](http://europeanspallationsource.se).
Choppers at ESS are abstracted in such a way that all of them are exposed via the same interface,
regardless of manufacturer. The behavior of this abstraction layer can be modelled as a finite state machine.

The docs-directory contains an `fsm`-file (created using the program [qfsm](http://qfsm.sourceforge.net/)) which describes
the state machine. While this is still work in progress, it gives an idea of how the choppers are going to operate internally.

# Chopper simulation

There are two ways of installing and running the chopper simulation. The first option is to run it directly using Python,
the second is to run it in a [Docker container](https://www.docker.com/).

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
$ python simulation.py --device chopper --setup default --protocol epics -- --prefix SIM:
```

The `--` separates arguments of the protocol adapter from the simulation's arguments.

## Installation and startup II: Docker

Another option to install and run plankton is via Docker (installation of Docker is outside the scope of this document,
please refer to the instructions on the Docker website). Once Docker is installed on the machine,
running the simulation is done via docker, with the same parameters passed to the simulation as in the Python case:

```
$ docker run -it dmscid/plankton --device chopper --setup default --protocol epics --  --prefix=SIM:
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
