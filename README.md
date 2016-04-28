# Chopper simulation

This repository contains a Virtual device for simulation of choppers at ESS. Choppers at ESS are abstracted in such a way that
all of them are exposed via the same interface, regardless of manufacturer. The behavior of this abstraction layer can
be modelled as a finite state machine.

The docs-directory contains an `fsm`-file (created using the program [qfsm](http://qfsm.sourceforge.net/)) which describes
the state machine. While this is still work in progress, it gives an idea of how the choppers are going to operate internally.

## Python module

```
pip install -r simulation/requirements.txt
```

## EPICS interface

The simulator is exposed to channel access, using the [pcaspy](https://pypi.python.org/pypi/pcaspy)-module. Depending on the level
of simulation there may be different PVs available to control the simulated chopper. At a minimum, the following PVs will be
exposed:

| PV  | Description  | Unit | Access |
|---|---|---|---|---|
| SPEED  |  Current rotation speed of the chopper disc. | Hz  | Read |
| PHASE  |  Current phase of the chopper disc. | Degree | Read |
| PARKPOSITION  |  Current position of chopper disc if in parked state. | Degree | Read/Write |
| STATE  |  Enum for chopper state. | - | Read |
| TDCE  |  Vector of TDC (top dead center) events in last accelerator pulse. | to be determined | Read |
| SPEED:SP  | Speed setpoint.  | Hz | Read/Write |
| PHASE:SP  |  Phase setpoint. | Degree | Read/Write |
| PARKPOSITION:SP  |  Position to which the disc should rotate in parked state. | Degree | Read/Write |
| DIRECTION  |  Enum for rotation direction (clockwise, counter clockwise). | - | Read/Write |
| COMMAND  |  String field to accept commands. | - | Read/Write |

**Possible values for STATE**
- Delevitated
- Levitating
- Delevitating
- Levitated
- Locking
- Locked
- Coasting
- Parking
- Parked
- Error

**Possible values for COMMAND**
- START: Speed and phase are adjusted to match the corresponding setpoints
- PHASE: Phase is adjusted to match the corresponding setpoint
- COAST: Switch off motor, but do not actively decelerate disc
- STOP: Go to velocity 0, disc remains levitated
- PARK: Go to velocity 0, disc remains levitated, is rotated to PARKEDANGLE:SP
- LEVITATE: Levitate disc if it's not levitated
- DELEVITATE: Delevitate disc if possible
