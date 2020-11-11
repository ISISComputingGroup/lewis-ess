Chopper simulation
==================

This folder contains a simulated neutron chopper as it will be present
at `ESS <http://europeanspallationsource.se>`__.

Choppers at ESS are abstracted in such a way that all of them are
exposed via the same interface, regardless of manufacturer. The behavior
of this abstraction layer is modelled as a finite state machine.

The docs-directory contains an ``fsm``-file (created using the program
`qfsm <http://qfsm.sourceforge.net/>`__) which describes the state
machine. While this is still work in progress, it gives an idea of how
the choppers are going to operate internally.

Starting the Chopper
--------------------

Start using Python:

::

    $ python simulation.py chopper -p "epic: {prefix: 'SIM:'}"

The ``--`` separates arguments of the protocol adapter from the
simulation's arguments.

Interacting with the simulated chopper
--------------------------------------

The simulated chopper is exposed via a set of EPICS PVs. For a detailed
description of those, see the table of available PVs below.

To observe some available EPICS PVs in an automatically updating screen:

::

    $ watch -n 1 caget SIM:State SIM:CmdL SIM:Spd-RB SIM:Spd SIM:Phs-RB SIM:Phs SIM:ParkAng-RB SIM:ParkAng

The following series of ``caput``-commands, executed from a different
terminal, will move the chopper to the specified speed and phase:

::

    $ caput SIM:CmdS init
    $ caput SIM:Spd 100.0
    $ caput SIM:Phs 23.0
    $ caput SIM:CmdS start

It may take a while until the simulation reaches the ``phase_locked``
state.

EPICS interface
---------------

The following PVs are available. Note that if a prefix was specified on
startup, it needs to be prepended to these:

+------+------+------+------+------+
| PV   | Desc | Unit | Acce |
|      | ript |      | ss   |
|      | ion  |      |      |
+======+======+======+======+======+
| Spd- | Read | Hz   | Read |
| RB   | back |      |      |
|      | of   |      |      |
|      | the  |      |      |
|      | spee |      |      |
|      | d    |      |      |
|      | setp |      |      |
|      | oint |      |      |
|      | .    |      |      |
+------+------+------+------+------+
| ActS | Curr | Hz   | Read |
| pd   | ent  |      |      |
|      | rota |      |      |
|      | tion |      |      |
|      | spee |      |      |
|      | d    |      |      |
|      | of   |      |      |
|      | the  |      |      |
|      | chop |      |      |
|      | per  |      |      |
|      | disc |      |      |
|      | .    |      |      |
+------+------+------+------+------+
| Spd  | Spee | Hz   | Read |
|      | d    |      | /Wri |
|      | setp |      | te   |
|      | oint |      |      |
|      | .    |      |      |
+------+------+------+------+------+
| Phs- | Read | Degr | Read |
| RB   | back | ee   |      |
|      | of   |      |      |
|      | the  |      |      |
|      | phas |      |      |
|      | e    |      |      |
|      | setp |      |      |
|      | oint |      |      |
+------+------+------+------+------+
| ActP | Curr | Degr | Read |
| hs   | ent  | ee   |      |
|      | phas |      |      |
|      | e    |      |      |
|      | of   |      |      |
|      | the  |      |      |
|      | chop |      |      |
|      | per  |      |      |
|      | disc |      |      |
|      | .    |      |      |
+------+------+------+------+------+
| Phs  | Phas | Degr | Read |
|      | e    | ee   | /Wri |
|      | setp |      | te   |
|      | oint |      |      |
|      | .    |      |      |
+------+------+------+------+------+
| Park | Read | Degr | Read |
| Ang- | back | ee   |      |
| RB   | of   |      |      |
|      | the  |      |      |
|      | park |      |      |
|      | posi |      |      |
|      | tion |      |      |
|      | setp |      |      |
|      | oint |      |      |
+------+------+------+------+------+
| Park | Posi | Degr | Read |
| Ang  | tion | ee   | /Wri |
|      | to   |      | te   |
|      | whic |      |      |
|      | h    |      |      |
|      | the  |      |      |
|      | disc |      |      |
|      | shou |      |      |
|      | ld   |      |      |
|      | rota |      |      |
|      | te   |      |      |
|      | in   |      |      |
|      | park |      |      |
|      | ed   |      |      |
|      | stat |      |      |
|      | e.   |      |      |
+------+------+------+------+------+
| Auto | Enum | -    | Read |
| Park | ``fa |      | /Wri |
|      | lse` |      | te   |
|      | `/`` |      |      |
|      | true |      |      |
|      | ``   |      |      |
|      | (or  |      |      |
|      | 0/1) |      |      |
|      | .    |      |      |
|      | If   |      |      |
|      | enab |      |      |
|      | led, |      |      |
|      | the  |      |      |
|      | chop |      |      |
|      | per  |      |      |
|      | will |      |      |
|      | move |      |      |
|      | to   |      |      |
|      | the  |      |      |
|      | park |      |      |
|      | ing  |      |      |
|      | stat |      |      |
|      | e    |      |      |
|      | when |      |      |
|      | the  |      |      |
|      | stop |      |      |
|      | stat |      |      |
|      | e    |      |      |
|      | is   |      |      |
|      | reac |      |      |
|      | hed. |      |      |
+------+------+------+------+------+
| Stat | Enum | -    | Read |
| e    | for  |      |      |
|      | chop |      |      |
|      | per  |      |      |
|      | stat |      |      |
|      | e.   |      |      |
+------+------+------+------+------+
| TDCE | Vect | to   | Read |
| \*   | or   | be   |      |
|      | of   | dete |      |
|      | TDC  | rmin |      |
|      | (top | ed   |      |
|      | dead |      |      |
|      | cent |      |      |
|      | er)  |      |      |
|      | even |      |      |
|      | ts   |      |      |
|      | in   |      |      |
|      | last |      |      |
|      | acce |      |      |
|      | lera |      |      |
|      | tor  |      |      |
|      | puls |      |      |
|      | e.   |      |      |
+------+------+------+------+------+
| Dir- | Enum | -    | Read |
| RB\* | for  |      |      |
|      | rota |      |      |
|      | tion |      |      |
|      | dire |      |      |
|      | ctio |      |      |
|      | n    |      |      |
|      | (clo |      |      |
|      | ckwi |      |      |
|      | se,  |      |      |
|      | coun |      |      |
|      | ter  |      |      |
|      | cloc |      |      |
|      | kwis |      |      |
|      | e).  |      |      |
+------+------+------+------+------+
| Dir\ | Desi | -    | Read |
| *    | red  |      | /Wri |
|      | rota |      | te   |
|      | tion |      |      |
|      | dire |      |      |
|      | ctio |      |      |
|      | n.   |      |      |
|      | (clo |      |      |
|      | ckwi |      |      |
|      | se,  |      |      |
|      | coun |      |      |
|      | ter  |      |      |
|      | cloc |      |      |
|      | kwis |      |      |
|      | e).  |      |      |
+------+------+------+------+------+
| CmdS | Stri | -    | Read |
|      | ng   |      | /Wri |
|      | fiel |      | te   |
|      | d    |      |      |
|      | to   |      |      |
|      | acce |      |      |
|      | pt   |      |      |
|      | comm |      |      |
|      | ands |      |      |
|      | .    |      |      |
+------+------+------+------+------+
| CmdL | Stri | -    | Read |
|      | ng   |      |      |
|      | fiel |      |      |
|      | d    |      |      |
|      | with |      |      |
|      | last |      |      |
|      | comm |      |      |
|      | and. |      |      |
+------+------+------+------+------+

Starred PVs are not implemented yet, but will become part of the
interface.

**Possible values for STATE** - Resting\ *: The chopper disc is resting,
the magnetic bearings are off. - Levitating*: The chopper disc is in the
process of being lifted up into stable levitation. - Delevitating\ *:
The chopper disc is in the process of being let down into the resting
state. - Accelerating: The chopper disc is accelerated to the speed
setpoint. - Phase locking: The chopper is trying to acquire a phase
lock. - Phase locked: Speed and phase are at the setpoints. - Idle: The
motor is off, the disc is rotating only via inertia. - Parking: The
chopper disc is in the process of rotating to the park position. -
Parked: The chopper disc is parked in the specified position. -
Stopping: The chopper disc is actively decelerated to speed 0. -
Stopped: The chopper disc is at speed 0. - Error*: An error has occurred
(to be specified in more detail).

The states marked with a \* are not implemented yet and are not present
in choppers which work with mechanical bearings.

**Possible values for COMMAND** - start: Speed and phase are adjusted to
match the corresponding setpoints - set\_phase: Phase is adjusted to
match the corresponding setpoint - unlock: Switch off motor, but do not
actively decelerate disc - stop: Go to velocity 0, disc remains
levitated - park: Go to velocity 0, disc remains levitated, is rotated
to PARKEDANGLE:SP - levitate\ *: Levitate disc if it's not levitated -
delevitate*: Delevitate disc if possible

The commands marked with a \* are not implemented yet. There are however
two additional commands, INIT and DEINIT. INIT takes the chopper from
the initial ``init`` state to the ``stopped`` state, DEINIT does the
opposite.
